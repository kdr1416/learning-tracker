"""API tests for the v2 day-completion gates, skill tree and locks (Phase B).

Each test gets a fresh in-memory DB (seeded). The puzzle/bug submit endpoints
do not exist yet (Phase 6, T034/T035), so tests set the puzzle/bug flags
directly in the DB to exercise gate evaluation.
"""
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


def _full_work():
    return {"exercise_submission": FULL, "test_result": FULL,
            "explain_answer": FULL, "flow_answer": FULL, "role_answer": FULL,
            "variant_answer": FULL, "self_note": NOTE,
            "followup_answers": [FULL, FULL], "summary": SUMMARY}


def _set_puzzle_bug_done(Session, day_id=1):
    db = Session()
    try:
        work = db.query(models.DayWork).filter_by(day_id=day_id).first()
        if work is None:
            work = models.DayWork(day_id=day_id)
            db.add(work)
        work.flow_puzzle_passed = True
        work.bug_passed = True
        db.commit()
    finally:
        db.close()


def _complete_day_1(t):
    c = t["client"]
    r = c.post("/api/days/1/quiz", json={"answers": [1, 3, 1, 1]})
    assert r.status_code == 200, r.text
    r = c.put("/api/days/1/work", json=_full_work())
    assert r.status_code == 200, r.text
    _set_puzzle_bug_done(t["Session"], 1)
    r = c.post("/api/days/1/complete")
    assert r.status_code == 200, r.text
    return r.json()


def test_health_and_seed(t):
    c = t["client"]
    assert c.get("/api/health").json() == {"ok": True}
    tracks = c.get("/api/tracks").json()
    assert len(tracks) == 1
    days = [d for m in tracks[0]["modules"] for d in m["days"]]
    assert len(days) == 14
    assert sum(len(d["quiz"]) for d in days) == 56
    assert len(c.get("/api/checklist").json()) == 50


def test_complete_day_rejected_when_incomplete(t):
    c = t["client"]
    r = c.post("/api/days/1/complete")
    assert r.status_code == 400
    missing = r.json()["detail"]["missing"]
    assert len(missing) == 6  # the v2 6-gate set


def test_complete_day_accepted_when_all_gates_pass(t):
    status = _complete_day_1(t)
    assert status["completed"] is True
    assert status["all_gates_passed"] is True
    assert len(status["gates"]) == 6
    assert all(g["passed"] for g in status["gates"])


def test_complete_day_rejected_when_one_gate_missing(t):
    c = t["client"]
    c.post("/api/days/1/quiz", json={"answers": [1, 3, 1, 1]})
    work = _full_work()
    work["summary"] = ""  # missing only the summary gate
    c.put("/api/days/1/work", json=work)
    _set_puzzle_bug_done(t["Session"], 1)
    r = c.post("/api/days/1/complete")
    assert r.status_code == 400
    missing = r.json()["detail"]["missing"]
    assert len(missing) == 1
    assert "tóm tắt" in missing[0]


def test_quiz_wrong_answers_do_not_pass_gate(t):
    c = t["client"]
    r = c.post("/api/days/1/quiz", json={"answers": [0, 0, 0, 0]})
    assert r.json()["score"] < 3
    status = c.get("/api/days/1/status").json()
    assert status["quiz_passed"] is False


def test_grandfathered_completed_day_stays_completed(t):
    c = t["client"]
    db = t["Session"]()
    try:
        # v1-completed Day with empty v2 fields: must stay completed.
        db.add(models.DayWork(day_id=1, completed=True))
        db.commit()
    finally:
        db.close()
    status = c.get("/api/days/1/status").json()
    assert status["completed"] is True
    r = c.post("/api/days/1/complete")
    assert r.status_code == 200
    assert r.json()["completed"] is True


def test_locked_day_rejects_writes_but_allows_reads(t):
    c = t["client"]
    # Day 2 is locked while Day 1 is not completed.
    r = c.put("/api/days/2/work", json=_full_work())
    assert r.status_code == 403
    r = c.post("/api/days/2/quiz", json={"answers": [0, 0, 0, 0]})
    assert r.status_code == 403
    r = c.get("/api/days/2/status")
    assert r.status_code == 200


def test_skill_tree_states(t):
    c = t["client"]
    tree = c.get("/api/tracks/1/skill-tree").json()
    days = [d for m in tree["modules"] for d in m["days"]]
    assert len(days) == 14
    by_number = {d["number"]: d for d in days}
    assert by_number[1]["state"] == "available"
    assert by_number[2]["state"] == "locked"
    assert by_number[1]["gates_total"] == 6
    _complete_day_1(t)
    tree = c.get("/api/tracks/1/skill-tree").json()
    days = [d for m in tree["modules"] for d in m["days"]]
    by_number = {d["number"]: d for d in days}
    assert by_number[1]["state"] == "mastered"
    assert by_number[2]["state"] == "available"


def test_skill_tree_404(t):
    assert t["client"].get("/api/tracks/999/skill-tree").status_code == 404
