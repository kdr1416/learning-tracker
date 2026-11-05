import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, repositories, schemas
from ..database import get_db
from ..services import evaluate_day_gates

router = APIRouter()


def _status(db: Session, day_id: int) -> schemas.DayStatusOut:
    score, total = repositories.best_quiz(db, day_id)
    work = repositories.get_work(db, day_id)
    w = {
        "exercise_submission": work.exercise_submission if work else "",
        "test_result": work.test_result if work else "",
        "explain_answer": work.explain_answer if work else "",
        "flow_answer": work.flow_answer if work else "",
        "role_answer": work.role_answer if work else "",
        "variant_answer": work.variant_answer if work else "",
    }
    gates = evaluate_day_gates(score, total, w)
    gate_out = [schemas.GateOut(key=g.key, label=g.label, passed=g.passed) for g in gates]
    missing = [g.label for g in gates if not g.passed]
    return schemas.DayStatusOut(
        day_id=day_id, completed=bool(work and work.completed),
        best_quiz_score=score, best_quiz_total=total,
        quiz_passed=bool(total) and score / total >= 0.75,
        gates=gate_out, all_gates_passed=all(g.passed for g in gates), missing=missing)


@router.get("/days/{day_id}/status", response_model=schemas.DayStatusOut)
def day_status(day_id: int, db: Session = Depends(get_db)):
    if not repositories.get_day(db, day_id):
        raise HTTPException(404, "Day not found")
    return _status(db, day_id)


@router.post("/days/{day_id}/quiz", response_model=schemas.QuizAttemptOut)
def submit_quiz(day_id: int, payload: schemas.QuizAttemptIn, db: Session = Depends(get_db)):
    day = repositories.get_day(db, day_id)
    if not day:
        raise HTTPException(404, "Day not found")
    questions = sorted(day.quiz_questions, key=lambda q: q.id)
    if len(payload.answers) != len(questions):
        raise HTTPException(400, f"Expected {len(questions)} answers, got {len(payload.answers)}")
    score = sum(1 for a, q in zip(payload.answers, questions) if a == q.correct_index)
    attempt = models.QuizAttempt(day_id=day_id, score=score, total=len(questions),
                                 answers=json.dumps(payload.answers))
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    best_score, best_total = repositories.best_quiz(db, day_id)
    return schemas.QuizAttemptOut(
        id=attempt.id, day_id=day_id, score=score, total=len(questions),
        passed=score / len(questions) >= 0.75,
        best_score=best_score, best_total=best_total)


@router.get("/days/{day_id}/work", response_model=schemas.DayWorkOut)
def get_work(day_id: int, db: Session = Depends(get_db)):
    work = repositories.get_work(db, day_id)
    if not work:
        return schemas.DayWorkOut(day_id=day_id, completed=False)
    return schemas.DayWorkOut(
        day_id=day_id, completed=work.completed,
        exercise_submission=work.exercise_submission, test_result=work.test_result,
        explain_answer=work.explain_answer, flow_answer=work.flow_answer,
        role_answer=work.role_answer, variant_answer=work.variant_answer)


@router.put("/days/{day_id}/work", response_model=schemas.DayWorkOut)
def save_work(day_id: int, payload: schemas.DayWorkIn, db: Session = Depends(get_db)):
    if not repositories.get_day(db, day_id):
        raise HTTPException(404, "Day not found")
    work = repositories.upsert_work(db, day_id, payload.model_dump())
    return schemas.DayWorkOut(
        day_id=day_id, completed=work.completed,
        exercise_submission=work.exercise_submission, test_result=work.test_result,
        explain_answer=work.explain_answer, flow_answer=work.flow_answer,
        role_answer=work.role_answer, variant_answer=work.variant_answer)


@router.post("/days/{day_id}/complete", response_model=schemas.DayStatusOut)
def complete_day(day_id: int, db: Session = Depends(get_db)):
    """Server-side gate: incomplete -> 400 with the missing gates listed.
    The frontend must show those reasons, not just 'failed'."""
    if not repositories.get_day(db, day_id):
        raise HTTPException(404, "Day not found")
    status = _status(db, day_id)
    if not status.all_gates_passed:
        raise HTTPException(400, detail={"missing": status.missing})
    work = repositories.get_work(db, day_id)
    work.completed = True
    db.commit()
    return _status(db, day_id)
