"""Content-completeness tests for the flow simulator scenarios.

Every Day must have exactly 2 scenarios (1 success, 1 failure); each
scenario's steps must line up 1:1 with the Day's flow_steps, with at most
one failing step, and every step after a failure must be "skip".
Written BEFORE the content (TDD): fails until the sim fragments are merged.
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


def test_every_day_has_two_sim_scenarios(db):
    days = db.query(models.Day).order_by(models.Day.number).all()
    assert len(days) == 14
    for day in days:
        scenarios = json.loads(day.sim_scenarios or "[]")
        assert len(scenarios) == 2, f"Day {day.number}: {len(scenarios)} scenarios"
        for sc in scenarios:
            assert sc["title"].strip(), f"Day {day.number}: empty title"
            assert sc["input"].strip(), f"Day {day.number}: empty input"
            assert sc["result"].strip(), f"Day {day.number}: empty result"


def test_sim_steps_match_flow_steps(db):
    days = db.query(models.Day).order_by(models.Day.number).all()
    for day in days:
        n_flow = len(json.loads(day.flow_steps or "[]"))
        assert n_flow >= 2, f"Day {day.number}: no flow steps"
        for sc in json.loads(day.sim_scenarios or "[]"):
            steps = sc["steps"]
            assert len(steps) == n_flow, (
                f"Day {day.number} '{sc['title']}': {len(steps)} sim steps "
                f"vs {n_flow} flow steps")
            statuses = [s["status"] for s in steps]
            assert all(s in ("ok", "fail", "skip") for s in statuses), \
                f"Day {day.number}: bad status in {statuses}"
            assert all(s["note"].strip() for s in steps), \
                f"Day {day.number}: empty step note"
            fails = [i for i, s in enumerate(statuses) if s == "fail"]
            assert len(fails) <= 1, f"Day {day.number}: {len(fails)} fails"
            if fails:
                assert all(s == "skip" for s in statuses[fails[0] + 1:]), \
                    f"Day {day.number}: steps after the fail must be skip"


def test_each_day_has_one_success_and_one_failure_scenario(db):
    days = db.query(models.Day).order_by(models.Day.number).all()
    for day in days:
        scenarios = json.loads(day.sim_scenarios or "[]")
        failed = [sc for sc in scenarios
                  if any(s["status"] == "fail" for s in sc["steps"])]
        succeeded = [sc for sc in scenarios
                     if all(s["status"] == "ok" for s in sc["steps"])]
        assert len(failed) == 1, f"Day {day.number}: {len(failed)} failure scenarios"
        assert len(succeeded) == 1, f"Day {day.number}: {len(succeeded)} success scenarios"
