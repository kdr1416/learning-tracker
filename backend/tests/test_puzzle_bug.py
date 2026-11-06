"""API tests for the Phase 6 puzzle/bug submit endpoints (T031–T033).

Written BEFORE the endpoints (TDD): these tests must FAIL until T034/T035
land in routers/days.py.
"""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.migrate import migrate
from app.seed import seed

FULL = "Day la cau tra loi day du hon hai muoi ky tu de qua cong kiem tra."
NOTE = ("Pydantic kiem tra du lieu ngay khi request toi, sai thi tra 422. "
        "Nho vay service khong bao gio nhan du lieu ban tu client.")
SUMMARY = ("Hom nay minh hieu Pydantic la cua ngo dau tien cua API: no parse va "
           "validate body truoc khi vao service, sai thi tra 422 va khong cham DB.")


@pytest.fixture
def t():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    migrate(engine)
    seed(TestingSession())

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    yield {"client": TestClient(app), "Session": TestingSession}
    app.dependency_overrides.clear()


def _day(t, number=1):
    db = t["Session"]()
    try:
        return db.query(models.Day).filter_by(number=number).one()
    finally:
        db.close()


def _correct_quiz_answers(t, day_id=1):
    db = t["Session"]()
    try:
        qs = sorted(db.query(models.QuizQuestion).filter_by(day_id=day_id),
                    key=lambda q: q.id)
        return [q.correct_index for q in qs]
    finally:
        db.close()


def _set_flags(t, day_id=1, puzzle=True, bug=True):
    db = t["Session"]()
    try:
        work = db.query(models.DayWork).filter_by(day_id=day_id).first()
        if work is None:
            work = models.DayWork(day_id=day_id)
            db.add(work)
        work.flow_puzzle_passed = puzzle
        work.bug_passed = bug
        db.commit()
    finally:
        db.close()


def _full_work(short_note=False):
    return {"exercise_submission": FULL, "test_result": FULL,
            "explain_answer": FULL, "flow_answer": FULL, "role_answer": FULL,
            "variant_answer": FULL,
            "self_note": "Mot cau ngan." if short_note else NOTE,
            "followup_answers": [FULL, FULL], "summary": SUMMARY}


# --- T031: Flow Puzzle ---

def test_puzzle_right_order_passes_and_sets_flag(t):
    c = t["client"]
    day = _day(t, 1)
    steps = json.loads(day.flow_steps)
    order = list(range(len(steps)))
    r = c.post("/api/days/1/flow-puzzle", json={"order": order})
    assert r.status_code == 200, r.text
    assert r.json()["passed"] is True
    assert r.json()["correct_order"] == order
    db = t["Session"]()
    try:
        work = db.query(models.DayWork).filter_by(day_id=1).one()
        assert work.flow_puzzle_passed is True
    finally:
        db.close()


def test_puzzle_wrong_order_fails_with_first_wrong_position(t):
    c = t["client"]
    day = _day(t, 1)
    steps = json.loads(day.flow_steps)
    assert len(steps) >= 2
    order = list(range(len(steps)))
    order[0], order[1] = order[1], order[0]  # swap first two
    r = c.post("/api/days/1/flow-puzzle", json={"order": order})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["passed"] is False
    assert body["first_wrong_position"] == 0
    db = t["Session"]()
    try:
        work = db.query(models.DayWork).filter_by(day_id=1).first()
        assert work is None or work.flow_puzzle_passed is False
    finally:
        db.close()


def test_puzzle_invalid_order_rejected(t):
    c = t["client"]
    day = _day(t, 1)
    n = len(json.loads(day.flow_steps))
    # duplicate index / missing index
    r = c.post("/api/days/1/flow-puzzle", json={"order": [0] * n})
    assert r.status_code == 422
    # wrong length
    r = c.post("/api/days/1/flow-puzzle", json={"order": [0]})
    assert r.status_code == 422


def test_puzzle_locked_day_forbidden(t):
    c = t["client"]
    day2 = _day(t, 2)
    n = len(json.loads(day2.flow_steps))
    r = c.post("/api/days/2/flow-puzzle", json={"order": list(range(n))})
    assert r.status_code == 403


def test_puzzle_unknown_day_404(t):
    c = t["client"]
    r = c.post("/api/days/999/flow-puzzle", json={"order": [0, 1]})
    assert r.status_code == 404


# --- T032: Spot the Bug ---

def test_bug_right_line_and_reason_passes_and_sets_flag(t):
    c = t["client"]
    day = _day(t, 1)
    r = c.post("/api/days/1/bug",
               json={"line": day.bug_line, "reason": day.bug_correct_reason})
    assert r.status_code == 200, r.text
    assert r.json()["passed"] is True
    db = t["Session"]()
    try:
        work = db.query(models.DayWork).filter_by(day_id=1).one()
        assert work.bug_passed is True
    finally:
        db.close()


def test_bug_right_line_wrong_reason_fails_and_names_half(t):
    c = t["client"]
    day = _day(t, 1)
    wrong_reason = (day.bug_correct_reason + 1) % 4
    r = c.post("/api/days/1/bug",
               json={"line": day.bug_line, "reason": wrong_reason})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["passed"] is False
    assert body["line_correct"] is True
    assert body["reason_correct"] is False
    db = t["Session"]()
    try:
        work = db.query(models.DayWork).filter_by(day_id=1).first()
        assert work is None or work.bug_passed is False
    finally:
        db.close()


def test_bug_wrong_line_fails_and_names_half(t):
    c = t["client"]
    day = _day(t, 1)
    n_lines = len(day.bug_code.split("\n"))
    wrong_line = (day.bug_line + 1) % n_lines
    r = c.post("/api/days/1/bug",
               json={"line": wrong_line, "reason": day.bug_correct_reason})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["passed"] is False
    assert body["line_correct"] is False
    assert body["reason_correct"] is True


def test_bug_locked_day_forbidden(t):
    c = t["client"]
    day2 = _day(t, 2)
    r = c.post("/api/days/2/bug",
               json={"line": day2.bug_line, "reason": day2.bug_correct_reason})
    assert r.status_code == 403


def test_bug_day_without_content_rejected(t):
    c = t["client"]
    db = t["Session"]()
    try:
        track = db.query(models.Track).first()
        module = sorted(track.modules, key=lambda m: m.order)[0]
        # number 0 sorts before Day 1, so it is unlocked and the test reaches
        # the content check (a locked Day must 403 first, per the other tests).
        day = models.Day(module_id=module.id, number=0, slug="day-rong",
                         title="Day rong", flow_steps="[]",
                         bug_code="", bug_line=None, bug_reasons="[]",
                         bug_correct_reason=None)
        db.add(day)
        db.commit()
        day_id = day.id
    finally:
        db.close()
    r = c.post(f"/api/days/{day_id}/bug", json={"line": 0, "reason": 0})
    assert r.status_code == 400


# --- T033: self-note gate (enforced at complete time, per the T017 correction) ---

def test_short_self_note_blocks_completion(t):
    c = t["client"]
    answers = _correct_quiz_answers(t, 1)
    r = c.post("/api/days/1/quiz", json={"answers": answers})
    assert r.status_code == 200 and r.json()["passed"] is True
    _set_flags(t, 1, puzzle=True, bug=True)
    r = c.put("/api/days/1/work", json=_full_work(short_note=True))
    assert r.status_code == 200  # drafts save; the gate blocks completion
    r = c.post("/api/days/1/complete")
    assert r.status_code == 400, r.text
    missing = r.json()["detail"]["missing"]
    assert any("Giải thích lại" in m for m in missing)
