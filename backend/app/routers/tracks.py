import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, repositories, schemas
from ..seed_data import METHOD
from ..services import day_state, evaluate_day_gates
from .days import _work_dict

router = APIRouter()


def _day_out(day: models.Day) -> schemas.DayOut:
    return schemas.DayOut(
        id=day.id, number=day.number, slug=day.slug, title=day.title,
        objective=day.objective, role_in_project=day.role_in_project,
        flow_steps=json.loads(day.flow_steps or "[]"),
        project_tree=json.loads(day.project_tree or "{}"),
        guide_steps=json.loads(day.guide_steps or "[]"),
        exercise=day.exercise,
        exercise_deliverables=json.loads(day.exercise_deliverables or "[]"),
        exercise_pass_criteria=json.loads(day.exercise_pass_criteria or "[]"),
        flow_question=day.flow_question, role_question=day.role_question,
        variant_question=day.variant_question, explain_prompt=day.explain_prompt,
        importance=day.importance or "should",
        real_world_use=day.real_world_use or "",
        pitfalls=json.loads(day.pitfalls or "[]"),
        bug_code=day.bug_code or "",
        bug_line=day.bug_line,
        bug_reasons=json.loads(day.bug_reasons or "[]"),
        bug_correct_reason=day.bug_correct_reason,
        followup_questions=json.loads(day.followup_questions or "[]"),
        sim_scenarios=json.loads(day.sim_scenarios or "[]"),
        flow_step_code=json.loads(day.flow_step_code or "[]"),
        quiz=[schemas.QuizQuestionOut(
            id=q.id, question=q.question,
            options=json.loads(q.options or "[]"), explanation=q.explanation)
            for q in day.quiz_questions],
    )


@router.get("/tracks", response_model=list[schemas.TrackOut])
def list_tracks(db: Session = Depends(get_db)):
    tracks = db.query(models.Track).all()
    out = []
    for t in tracks:
        mods = []
        for m in sorted(t.modules, key=lambda x: x.order):
            days = sorted(m.days, key=lambda x: x.number)
            mods.append(schemas.ModuleOut(
                id=m.id, slug=m.slug, title=m.title, description=m.description,
                order=m.order, days=[_day_out(d) for d in days]))
        out.append(schemas.TrackOut(id=t.id, slug=t.slug, title=t.title,
                                    description=t.description, modules=mods))
    return out


@router.get("/method")
def get_method():
    """Phương pháp Viết - Test - Giải thích + luật bài kiểm tra hàng ngày."""
    return METHOD


@router.get("/tracks/{track_id}/skill-tree", response_model=schemas.SkillTreeOut)
def skill_tree(track_id: int, db: Session = Depends(get_db)):
    """Skill tree: node states are derived from progress, never stored.
    A mastered Day counts 6/6 gates (grandfathered v1 completions included)."""
    track = db.query(models.Track).filter(models.Track.id == track_id).first()
    if not track:
        raise HTTPException(404, "Track not found")
    modules_out = []
    for m in sorted(track.modules, key=lambda x: x.order):
        days_out = []
        for d in sorted(m.days, key=lambda x: x.number):
            state = day_state(db, d)
            work = repositories.get_work(db, d.id)
            if work is not None and work.completed:
                gates_passed, gates_total = 6, 6
            else:
                score, total = repositories.best_quiz(db, d.id)
                gates = evaluate_day_gates(score, total, _work_dict(work))
                gates_passed = sum(1 for g in gates if g.passed)
                gates_total = len(gates)
            days_out.append(schemas.SkillTreeDayOut(
                day_id=d.id, number=d.number, title=d.title, state=state,
                gates_passed=gates_passed, gates_total=gates_total))
        module_day_numbers = {d.number for d in m.days}
        extensions = [
            schemas.SkillTreeExtensionOut(
                id=e.id, title=e.title, description=e.description,
                related_day_number=e.related_day_number, state="unexplored")
            for e in sorted(
                db.query(models.ExtensionTopic).filter_by(track_id=track.id).all(),
                key=lambda x: x.order)
            if e.related_day_number in module_day_numbers
        ]
        modules_out.append(schemas.SkillTreeModuleOut(
            module_id=m.id, title=m.title, order=m.order,
            days=days_out, extensions=extensions))
    return schemas.SkillTreeOut(track_id=track.id, modules=modules_out)


@router.get("/tracks/{track_id}", response_model=schemas.TrackOut)
def get_track(track_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Track).filter(models.Track.id == track_id).first()
    if not t:
        from fastapi import HTTPException
        raise HTTPException(404, "Track not found")
    mods = []
    for m in sorted(t.modules, key=lambda x: x.order):
        days = sorted(m.days, key=lambda x: x.number)
        mods.append(schemas.ModuleOut(
            id=m.id, slug=m.slug, title=m.title, description=m.description,
            order=m.order, days=[_day_out(d) for d in days]))
    return schemas.TrackOut(id=t.id, slug=t.slug, title=t.title,
                            description=t.description, modules=mods)
