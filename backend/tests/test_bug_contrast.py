"""API tests for Spot the Bug contrasting cases (spec 003).

Days 2, 3, 5, 9 ship a correct_code shown side by side with the buggy
code. The server accepts any line in the difflib diff set (Day 5 drops
two lines, so both 2 and 3 count), and returns the diff only AFTER a
submission. The answer key (bug_line / bug_correct_reason) must not
reach the browser in the Day payload.
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

# expected 0-based diff lines (buggy side) per bottleneck Day
EXPECTED_DIFF = {2: [3], 3: [6], 5: [2, 3], 9: [7]}


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


def _day(t, number):
    db = t["Session"]()
    try:
        return db.query(models.Day).filter_by(number=number).one()
    finally:
        db.close()


def _unlock_up_to(t, number):
    """Sequential unlock: mark all earlier Days completed directly in the DB."""
    db = t["Session"]()
    try:
        for d in db.query(models.Day).filter(models.Day.number < number).all():
            work = db.query(models.DayWork).filter_by(day_id=d.id).first()
            if work is None:
                work = models.DayWork(day_id=d.id, completed=True)
                db.add(work)
            else:
                work.completed = True
        db.commit()
    finally:
        db.close()


def _day_out(t, number):
    r = t["client"].get("/api/tracks")
    assert r.status_code == 200
    for track in r.json():
        for mod in track["modules"]:
            for d in mod["days"]:
                if d["number"] == number:
                    return d
    raise AssertionError(f"Day {number} not in tracks payload")


def test_correct_code_only_for_bottleneck_days(t):
    for number in (2, 3, 5, 9):
        d = _day_out(t, number)
        assert d["correct_code"], f"Day {number}: correct_code missing"
        assert d["correct_code"] != d["bug_code"]
    for number in (1, 4, 6, 7, 8, 10):
        assert _day_out(t, number)["correct_code"] == ""


def test_day_out_hides_answer_key(t):
    d = _day_out(t, 1)
    assert "bug_line" not in d
    assert "bug_correct_reason" not in d


def test_contrast_days_accept_diff_lines(t):
    for number, diff in EXPECTED_DIFF.items():
        _unlock_up_to(t, number)
        day = _day(t, number)
        for line in diff:
            r = t["client"].post(
                f"/api/days/{day.id}/bug",
                json={"line": line, "reason": day.bug_correct_reason})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["passed"] is True, f"Day {number} line {line} should pass"
            assert body["diff_lines"] == diff
        db = t["Session"]()
        try:
            work = db.query(models.DayWork).filter_by(day_id=day.id).one()
            assert work.bug_passed is True
        finally:
            db.close()


def test_day5_if_line_counts_but_wrong_reason_fails(t):
    _unlock_up_to(t, 5)
    day = _day(t, 5)
    wrong_reason = (day.bug_correct_reason + 1) % 4
    r = t["client"].post(f"/api/days/{day.id}/bug",
                         json={"line": 2, "reason": wrong_reason})
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is False
    assert body["line_correct"] is True  # line 2 is in the diff set
    assert body["reason_correct"] is False
    assert body["diff_lines"] == [2, 3]


def test_contrast_wrong_line_fails_and_reveals_diff(t):
    _unlock_up_to(t, 2)
    day = _day(t, 2)
    r = t["client"].post(f"/api/days/{day.id}/bug",
                         json={"line": 0, "reason": day.bug_correct_reason})
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is False
    assert body["line_correct"] is False
    assert body["reason_correct"] is True
    assert body["diff_lines"] == [3]
    assert body["diff_lines_correct"] == [3]


def test_day_without_correct_code_still_uses_bug_line(t):
    day = _day(t, 1)
    r = t["client"].post(f"/api/days/{day.id}/bug",
                         json={"line": day.bug_line,
                               "reason": day.bug_correct_reason})
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is True
    assert body["diff_lines"] == []
    assert body["diff_lines_correct"] == []
