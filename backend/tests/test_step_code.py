"""Content-completeness tests for the per-step code shown by the simulator's
"Xem code" button.

Every Day must have exactly one {code, note} entry per flow step; the code
must be real (no placeholders, 3-15 lines) and the note must say where the
code lives and when it runs.
Written BEFORE the content (TDD): fails until the step-code fragments are merged.
"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.migrate import migrate
from app.seed import seed


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    migrate(engine)
    session = sessionmaker(bind=engine)()
    seed(session)
    yield session
    session.close()


def test_every_day_has_step_code_for_each_flow_step(db):
    days = db.query(models.Day).order_by(models.Day.number).all()
    assert len(days) == 14
    for day in days:
        n_flow = len(json.loads(day.flow_steps or "[]"))
        entries = json.loads(day.flow_step_code or "[]")
        assert len(entries) == n_flow, (
            f"Day {day.number}: {len(entries)} step-code entries vs {n_flow} flow steps")
        for i, e in enumerate(entries):
            code = e.get("code", "")
            note = e.get("note", "")
            assert code.strip(), f"Day {day.number} step {i + 1}: empty code"
            lines = [l for l in code.splitlines() if l.strip()]
            assert 3 <= len(lines) <= 15, (
                f"Day {day.number} step {i + 1}: {len(lines)} non-empty lines")
            assert "..." not in code and "TODO" not in code, \
                f"Day {day.number} step {i + 1}: placeholder in code"
            assert note.strip(), f"Day {day.number} step {i + 1}: empty note"
            assert len(note.split(". ")) <= 2, \
                f"Day {day.number} step {i + 1}: note longer than 2 sentences"
