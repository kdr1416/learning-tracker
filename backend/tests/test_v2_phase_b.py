"""Phase B service-level tests (written FIRST, before implementation).

- Gate matrix (T012): each of the 6 v2 gates, broken in turn, blocks completion
  while the other 5 pass.
- Skill-tree states (T019): available / locked / in_progress / mastered derived
  from progress + the sequential unlock rule.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.migrate import migrate
from app.seed import seed
from app.services import evaluate_day_gates

FULL = "Day la cau tra loi day du hon hai muoi ky tu de qua cong kiem tra."
NOTE = ("Pydantic kiem tra du lieu ngay khi request toi, sai thi tra 422. "
        "Nho vay service khong bao gio nhan du lieu ban tu client.")
SUMMARY = ("Hom nay minh hieu Pydantic la cua ngo dau tien cua API: no parse va "
           "validate body truoc khi vao service, sai thi tra 422 va khong cham DB.")


def _full_work():
    return {"exercise_submission": FULL, "test_result": FULL,
            "explain_answer": FULL, "flow_answer": FULL, "role_answer": FULL,
            "variant_answer": FULL, "self_note": NOTE,
            "followup_answers": [FULL, FULL], "summary": SUMMARY,
            "flow_puzzle_passed": True, "bug_passed": True}


def _gates(work, score=4, total=4):
    return {g.key: g.passed for g in evaluate_day_gates(score, total, work)}


def test_gate_matrix_each_gate_blocks_completion():
    assert len(_gates(_full_work())) == 6
    assert all(_gates(_full_work()).values())

    cases = [
        ("quiz", {"score": 2, "total": 4}, "quiz"),
        ("exercise-empty", {"exercise_submission": ""}, "exercise"),
        ("exercise-no-test", {"test_result": ""}, "exercise"),
        ("puzzle", {"flow_puzzle_passed": False}, "flow_puzzle"),
        ("bug", {"bug_passed": False}, "bug"),
        ("note-empty", {"self_note": ""}, "self_note"),
        ("note-one-short-sentence", {"self_note": "Pydantic hay."}, "self_note"),
        ("note-no-followup-no-variant",
         {"followup_answers": [], "variant_answer": ""}, "self_note"),
        ("note-one-followup-only",
         {"followup_answers": [FULL]}, "self_note"),
        ("summary-empty", {"summary": ""}, "summary"),
    ]
    for _name, override, failing_gate in cases:
        work = _full_work()
        score, total = 4, 4
        if "score" in override:
            score, total = override["score"], override["total"]
        else:
            work.update(override)
        result = _gates(work, score, total)
        assert result[failing_gate] is False, _name
        assert all(v for k, v in result.items() if k != failing_gate), _name


def test_self_note_falls_back_to_variant_when_no_followups_yet():
    # Before Phase C content exists, a Day has no follow-up questions stored:
    # a valid variant answer still passes the self-note gate.
    work = _full_work()
    work["followup_answers"] = []
    assert _gates(work)["self_note"] is True


def _seeded_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    migrate(engine)
    Session = sessionmaker(bind=engine)
    seed(Session())
    return Session


def test_skill_tree_states():
    from app.services import day_state
    Session = _seeded_db()
    db = Session()
    try:
        d1 = db.query(models.Day).filter_by(number=1).one()
        d2 = db.query(models.Day).filter_by(number=2).one()
        d8 = db.query(models.Day).filter_by(number=8).one()
        assert day_state(db, d1) == "available"
        assert day_state(db, d2) == "locked"
        assert day_state(db, d8) == "locked"
        # Partial work -> in progress, still locked for the next Day.
        db.add(models.DayWork(day_id=d1.id, exercise_submission=FULL))
        db.commit()
        assert day_state(db, d1) == "in_progress"
        assert day_state(db, d2) == "locked"
        # Complete Day 1 -> mastered, Day 2 available.
        work = db.query(models.DayWork).filter_by(day_id=d1.id).one()
        work.completed = True
        db.commit()
        assert day_state(db, d1) == "mastered"
        assert day_state(db, d2) == "available"
        # Complete all of Module 1 -> Day 8 (first of Module 2) available.
        for n in range(2, 8):
            day = db.query(models.Day).filter_by(number=n).one()
            db.add(models.DayWork(day_id=day.id, completed=True))
        db.commit()
        assert day_state(db, d8) == "available"
    finally:
        db.close()
