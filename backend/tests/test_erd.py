"""API tests for the interactive ERD (spec 002).

GET /api/erd returns the 5 stages where the storage shape changes
(Days 1, 2, 8, 9, 10). Static content from seed_data, no DB table.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.migrate import migrate
from app.seed import seed


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
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_erd_five_stages_in_day_order(t):
    r = t.get("/api/erd")
    assert r.status_code == 200
    stages = r.json()
    assert [s["day"] for s in stages] == [1, 2, 8, 9, 10]
    for s in stages:
        assert s["title"] and s["note"]
        assert [tb["name"] for tb in s["tables"]] == ["bookings", "audit_log"]


def test_erd_day1_model_only_no_rows(t):
    s = t.get("/api/erd").json()[0]
    bookings = s["tables"][0]
    assert bookings["kind"] == "model"
    assert bookings["present"] is True
    assert [c["name"] for c in bookings["columns"]] == ["id", "customer", "start", "end"]
    assert bookings["rows"] == []
    assert "Chưa có bảng" in bookings["sql"]
    assert s["tables"][1]["present"] is False


def test_erd_day2_dict_with_sample_rows(t):
    s = t.get("/api/erd").json()[1]
    bookings = s["tables"][0]
    assert bookings["kind"] == "dict"
    assert bookings["rows"][0][1] == "An"
    assert bookings["rows"][1][1] == "Bình"
    assert s["tables"][1]["present"] is False


def test_erd_day8_two_tables_with_fk(t):
    s = t.get("/api/erd").json()[2]
    bookings, audit = s["tables"]
    assert bookings["kind"] == "table" and audit["kind"] == "table"
    assert audit["fk"] == {"column": "booking_id", "to_table": "bookings", "to_column": "id"}
    assert "CREATE TABLE bookings" in bookings["sql"]
    assert "REFERENCES bookings(id)" in audit["sql"]
    # audit_log columns are illustrative, not from the Day content
    assert "minh họa" in audit["illustration"]
    assert audit["rows"][0][2] == "created"


def test_erd_day9_unique_on_start(t):
    s = t.get("/api/erd").json()[3]
    start = [c for c in s["tables"][0]["columns"] if c["name"] == "start"][0]
    assert start["badge"] == "UNIQUE"
    assert "UNIQUE (start)" in s["tables"][0]["sql"]
    # no UNIQUE badge on any earlier stage
    for earlier in t.get("/api/erd").json()[:3]:
        badges = [c.get("badge") for tb in earlier["tables"] for c in tb["columns"]]
        assert "UNIQUE" not in badges


def test_erd_day10_status_column_new(t):
    s = t.get("/api/erd").json()[4]
    cols = s["tables"][0]["columns"]
    status = [c for c in cols if c["name"] == "status"][0]
    assert status["is_new"] is True
    assert s["tables"][0]["rows"][0][-1] == "confirmed"
    assert s["tables"][0]["rows"][1][-1] == "cancelled"
    # no status column on any earlier stage
    for earlier in t.get("/api/erd").json()[:4]:
        names = [c["name"] for tb in earlier["tables"] for c in tb["columns"]]
        assert "status" not in names
