import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..seed_data import METHOD

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
