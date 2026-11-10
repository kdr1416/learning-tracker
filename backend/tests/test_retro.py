"""API tests for the Weekly Retro per Module (spec 004).

Retro is computed live from real progress: failed gates per Day,
weakest skill = most-failed gate on incomplete Days, next Day = first
incomplete Day. One retro per Module, saved as a JournalEntry.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

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

ANSWERS = [
    "Viết API từ đầu chạy được, test 4/4 pass.",
    "Kẹt lâu nhất ở bước kiểm tra trùng id.",
    "Module sau viết test trước khi viết code.",
]
LONG_NOTE = ("Mình hiểu Pydantic validate ngay khi request tới. "
             "Sai thì trả 422 trước khi vào service, nhờ vậy service không nhận dữ liệu bẩn.")
LONG_SUMMARY = ("Module này mình học cách viết API từ đầu: Pydantic validate, "
                "router nhận request, service giữ nghiệp vụ, repository chỉ đọc ghi.")


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


def _module_id(t, order=1):
    db = t["Session"]()
    try:
        return db.query(models.Module).filter_by(order=order).one().id
    finally:
        db.close()


def _complete_days(t, numbers):
    db = t["Session"]()
    try:
        for d in db.query(models.Day).filter(models.Day.number.in_(numbers)).all():
            work = db.query(models.DayWork).filter_by(day_id=d.id).first()
            if work is None:
                work = models.DayWork(day_id=d.id, completed=True)
                db.add(work)
            else:
                work.completed = True
        db.commit()
    finally:
        db.close()


def _pass_all_gates_except_bug(t, number):
    """Make one incomplete Day pass every gate except bug."""
    db = t["Session"]()
    try:
        day = db.query(models.Day).filter_by(number=number).one()
        db.add(models.QuizAttempt(day_id=day.id, score=4, total=4, answers="[]"))
        work = models.DayWork(
            day_id=day.id,
            exercise_submission="Day la bai tap day du hon hai muoi ky tu.",
            test_result="4/4 tests passed, ket qua chay that.",
            flow_puzzle_passed=True, bug_passed=False,
            self_note=LONG_NOTE,
            followup_answers='["Cau tra loi bien the day du hon hai muoi ky tu.", '
                            '"Cau tra loi thu hai cung day du hai muoi ky tu."]',
            summary=LONG_SUMMARY)
        db.add(work)
        db.commit()
    finally:
        db.close()


def test_retro_lists_modules_with_progress(t):
    r = t["client"].get("/api/retro")
    assert r.status_code == 200
    mods = r.json()
    assert [m["order"] for m in mods] == [1, 2, 3]
    m1 = mods[0]
    assert m1["total_days"] == 7 and m1["completed_days"] == 0
    assert m1["can_retro"] is False and m1["retro_done"] is False
    assert m1["next_day"]["number"] == 1
    # every gate fails on all 7 untouched Days -> tie, first in gate order wins
    assert m1["weakest_skill"] == {"skill": "Hiểu khái niệm", "count": 7}
    assert len(m1["questions"]) == 3
    assert all(d["completed"] is False for d in m1["days"])


def test_retro_post_before_complete_400(t):
    r = t["client"].post(f"/api/retro/{_module_id(t)}", json={"answers": ANSWERS})
    assert r.status_code == 400


def test_retro_post_unknown_module_404(t):
    r = t["client"].post("/api/retro/999", json={"answers": ANSWERS})
    assert r.status_code == 404


def test_retro_full_flow_then_second_post_409(t):
    _complete_days(t, [1, 2, 3, 4, 5, 6, 7])
    mid = _module_id(t)
    r = t["client"].get("/api/retro")
    m1 = [m for m in r.json() if m["module_id"] == mid][0]
    assert m1["can_retro"] is True
    assert m1["next_day"] is None
    assert m1["weakest_skill"] is None  # no incomplete Day, no failing gate

    r = t["client"].post(f"/api/retro/{mid}", json={"answers": ANSWERS})
    assert r.status_code == 201, r.text
    entry = r.json()
    assert entry["topic"].startswith("Retro Module 1:")
    assert entry["done"] == ANSWERS[0]
    assert entry["stuck"] == ANSWERS[1]
    assert entry["next_step"] == ANSWERS[2]
    today = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
    assert entry["date"] == today

    r = t["client"].get("/api/retro")
    m1 = [m for m in r.json() if m["module_id"] == mid][0]
    assert m1["retro_done"] is True and m1["retro_date"] == today

    r = t["client"].post(f"/api/retro/{mid}", json={"answers": ANSWERS})
    assert r.status_code == 409


def test_retro_weakest_skill_from_real_failed_gates(t):
    _complete_days(t, [1, 2, 3, 4, 5, 6])
    _pass_all_gates_except_bug(t, 7)
    r = t["client"].get("/api/retro")
    m1 = r.json()[0]
    assert m1["completed_days"] == 6
    assert m1["next_day"]["number"] == 7
    assert m1["weakest_skill"] == {"skill": "Đọc và bắt lỗi code", "count": 1}
    day7 = [d for d in m1["days"] if d["number"] == 7][0]
    assert day7["failed_gates"] == ["Đọc và bắt lỗi code"]


def test_retro_validation_422(t):
    _complete_days(t, [1, 2, 3, 4, 5, 6, 7])
    mid = _module_id(t)
    r = t["client"].post(f"/api/retro/{mid}", json={"answers": ANSWERS[:2]})
    assert r.status_code == 422
    r = t["client"].post(f"/api/retro/{mid}",
                         json={"answers": [ANSWERS[0], "   ", ANSWERS[2]]})
    assert r.status_code == 422
