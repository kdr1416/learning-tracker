import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, repositories, schemas
from ..database import get_db
from ..services import day_state, evaluate_day_gates, is_locked

router = APIRouter()


def _work_dict(work: models.DayWork | None) -> dict:
    if work is None:
        return {}
    return {
        "exercise_submission": work.exercise_submission,
        "test_result": work.test_result,
        "explain_answer": work.explain_answer,
        "flow_answer": work.flow_answer,
        "role_answer": work.role_answer,
        "variant_answer": work.variant_answer,
        "flow_puzzle_passed": work.flow_puzzle_passed,
        "bug_passed": work.bug_passed,
        "self_note": work.self_note,
        "followup_answers": json.loads(work.followup_answers or "[]"),
        "summary": work.summary,
    }


def _status(db: Session, day_id: int) -> schemas.DayStatusOut:
    score, total = repositories.best_quiz(db, day_id)
    work = repositories.get_work(db, day_id)
    gates = evaluate_day_gates(score, total, _work_dict(work))
    gate_out = [schemas.GateOut(key=g.key, label=g.label, passed=g.passed) for g in gates]
    # Grandfathering (Constitution I): a Day completed under v1 stays completed
    # and is never re-evaluated against the v2 gates.
    completed = bool(work and work.completed)
    if completed:
        missing: list[str] = []
        all_passed = True
    else:
        missing = [g.label for g in gates if not g.passed]
        all_passed = all(g.passed for g in gates)
    return schemas.DayStatusOut(
        day_id=day_id, completed=completed,
        best_quiz_score=score, best_quiz_total=total,
        quiz_passed=bool(total) and score / total >= 0.75,
        gates=gate_out, all_gates_passed=all_passed, missing=missing)


def _get_day_or_404(db: Session, day_id: int) -> models.Day:
    day = repositories.get_day(db, day_id)
    if not day:
        raise HTTPException(404, "Day not found")
    return day


def _forbid_if_locked(db: Session, day: models.Day) -> None:
    if is_locked(db, day):
        raise HTTPException(403, "Day chưa được mở khóa — hãy hoàn thành Day trước đó.")


@router.get("/days/{day_id}/status", response_model=schemas.DayStatusOut)
def day_status(day_id: int, db: Session = Depends(get_db)):
    if not repositories.get_day(db, day_id):
        raise HTTPException(404, "Day not found")
    return _status(db, day_id)


@router.post("/days/{day_id}/quiz", response_model=schemas.QuizAttemptOut)
def submit_quiz(day_id: int, payload: schemas.QuizAttemptIn, db: Session = Depends(get_db)):
    day = _get_day_or_404(db, day_id)
    _forbid_if_locked(db, day)
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
        role_answer=work.role_answer, variant_answer=work.variant_answer,
        self_note=work.self_note,
        followup_answers=json.loads(work.followup_answers or "[]"),
        summary=work.summary)


@router.put("/days/{day_id}/work", response_model=schemas.DayWorkOut)
def save_work(day_id: int, payload: schemas.DayWorkIn, db: Session = Depends(get_db)):
    day = _get_day_or_404(db, day_id)
    _forbid_if_locked(db, day)
    data = payload.model_dump()
    # followup_answers is stored as JSON text on the row.
    data["followup_answers"] = json.dumps(data.get("followup_answers") or [])
    work = repositories.upsert_work(db, day_id, data)
    return schemas.DayWorkOut(
        day_id=day_id, completed=work.completed,
        exercise_submission=work.exercise_submission, test_result=work.test_result,
        explain_answer=work.explain_answer, flow_answer=work.flow_answer,
        role_answer=work.role_answer, variant_answer=work.variant_answer,
        self_note=work.self_note,
        followup_answers=json.loads(work.followup_answers or "[]"),
        summary=work.summary)


@router.post("/days/{day_id}/flow-puzzle", response_model=schemas.FlowPuzzleOut)
def submit_flow_puzzle(day_id: int, payload: schemas.FlowPuzzleIn,
                       db: Session = Depends(get_db)):
    """Flow Puzzle: compare the submitted index order against the Day's stored
    flow_steps. A wrong order is a 200 with passed=false (retry allowed),
    never an error — only a non-permutation is a 422."""
    day = _get_day_or_404(db, day_id)
    _forbid_if_locked(db, day)
    steps = json.loads(day.flow_steps or "[]")
    correct_order = list(range(len(steps)))
    if sorted(payload.order) != correct_order:
        raise HTTPException(
            422, f"order phải là một hoán vị của 0..{len(steps) - 1}")
    if payload.order == correct_order:
        repositories.upsert_work(db, day_id, {"flow_puzzle_passed": True})
        return schemas.FlowPuzzleOut(passed=True, correct_order=correct_order)
    first_wrong = next(i for i, (a, b) in enumerate(zip(payload.order, correct_order))
                       if a != b)
    return schemas.FlowPuzzleOut(passed=False, first_wrong_position=first_wrong)


@router.post("/days/{day_id}/bug", response_model=schemas.BugOut)
def submit_bug(day_id: int, payload: schemas.BugIn, db: Session = Depends(get_db)):
    """Spot the Bug: line AND reason must both be right. On failure the
    response names which half was right, so the learner re-reads the
    relevant theory instead of guessing blindly."""
    day = _get_day_or_404(db, day_id)
    _forbid_if_locked(db, day)
    if day.bug_line is None or day.bug_correct_reason is None:
        raise HTTPException(400, "Day này chưa có bài Spot the Bug.")
    reasons = json.loads(day.bug_reasons or "[]")
    n_lines = len((day.bug_code or "").split("\n"))
    if not 0 <= payload.line < n_lines or not 0 <= payload.reason < len(reasons):
        raise HTTPException(422, "line hoặc reason ngoài phạm vi")
    line_ok = payload.line == day.bug_line
    reason_ok = payload.reason == day.bug_correct_reason
    if line_ok and reason_ok:
        repositories.upsert_work(db, day_id, {"bug_passed": True})
        return schemas.BugOut(passed=True)
    return schemas.BugOut(passed=False, line_correct=line_ok,
                          reason_correct=reason_ok)


@router.post("/days/{day_id}/complete", response_model=schemas.DayStatusOut)
def complete_day(day_id: int, db: Session = Depends(get_db)):
    """Server-side gate: incomplete -> 400 with the missing gates listed.
    The frontend must show those reasons, not just 'failed'.
    Already-completed Days return 200 (grandfathered, never re-checked)."""
    day = _get_day_or_404(db, day_id)
    work = repositories.get_work(db, day_id)
    if work is not None and work.completed:
        return _status(db, day_id)
    _forbid_if_locked(db, day)
    status = _status(db, day_id)
    if not status.all_gates_passed:
        raise HTTPException(400, detail={"missing": status.missing})
    work = repositories.get_work(db, day_id)
    work.completed = True
    db.commit()
    return _status(db, day_id)
