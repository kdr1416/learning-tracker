"""API tests for the day-completion gate, using a fresh in-memory DB."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.seed import seed

engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                       poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
seed(TestingSession())


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)

FULL = "Day la cau tra loi day du hon hai muoi ky tu de qua cong kiem tra."


def test_health_and_seed():
    assert client.get("/api/health").json() == {"ok": True}
    tracks = client.get("/api/tracks").json()
    assert len(tracks) == 1
    days = [d for m in tracks[0]["modules"] for d in m["days"]]
    assert len(days) == 14
    assert sum(len(d["quiz"]) for d in days) == 56
    checklist = client.get("/api/checklist").json()
    assert len(checklist) == 50


def test_complete_day_rejected_when_incomplete():
    r = client.post("/api/days/1/complete")
    assert r.status_code == 400
    assert "missing" in r.json()["detail"]


def test_complete_day_accepted_when_all_gates_pass():
    # quiz 4/4: answers are the correct indexes from the seeded Day 1 quiz
    # (Day 1 correct indexes: 1, 3, 1, 1)
    r = client.post("/api/days/1/quiz", json={"answers": [1, 3, 1, 1]})
    assert r.status_code == 200, r.text
    assert r.json()["score"] == 4
    work = {"exercise_submission": FULL, "test_result": FULL, "explain_answer": FULL,
            "flow_answer": FULL, "role_answer": FULL, "variant_answer": FULL}
    r = client.put("/api/days/1/work", json=work)
    assert r.status_code == 200, r.text
    r = client.post("/api/days/1/complete")
    assert r.status_code == 200, r.text
    assert r.json()["completed"] is True
    assert r.json()["all_gates_passed"] is True


def test_quiz_wrong_answers_do_not_pass_gate():
    r = client.post("/api/days/2/quiz", json={"answers": [0, 0, 0, 0]})
    assert r.json()["score"] < 3
    status = client.get("/api/days/2/status").json()
    assert status["quiz_passed"] is False
