"""v2 tests: migration proof + gate behaviour.

T010 (migration proof): build a v1-schema database (tables WITHOUT the v2
columns), insert fake progress, run migrate() + seed(), and prove the progress
is byte-identical while the new columns appear. This is the test that must pass
before any production deploy — create_all alone never adds columns.
"""
import sqlite3

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base
from app.migrate import NEW_COLUMNS, migrate
from app.seed import seed

# v1 DDL: exactly the tables/columns v1 models created (no v2 columns).
V1_DDL = [
    """CREATE TABLE tracks (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL UNIQUE,
        title VARCHAR NOT NULL, description TEXT)""",
    """CREATE TABLE modules (id INTEGER PRIMARY KEY, track_id INTEGER NOT NULL,
        slug VARCHAR NOT NULL, title VARCHAR NOT NULL, description TEXT,
        "order" INTEGER)""",
    """CREATE TABLE days (id INTEGER PRIMARY KEY, module_id INTEGER NOT NULL,
        number INTEGER NOT NULL, slug VARCHAR NOT NULL, title VARCHAR NOT NULL,
        objective TEXT, role_in_project TEXT, flow_steps TEXT, project_tree TEXT,
        guide_steps TEXT, exercise TEXT, exercise_deliverables TEXT,
        exercise_pass_criteria TEXT, flow_question TEXT, role_question TEXT,
        variant_question TEXT, explain_prompt TEXT)""",
    """CREATE TABLE quiz_questions (id INTEGER PRIMARY KEY, day_id INTEGER NOT NULL,
        question TEXT NOT NULL, options TEXT NOT NULL, correct_index INTEGER NOT NULL,
        explanation TEXT)""",
    """CREATE TABLE quiz_attempts (id INTEGER PRIMARY KEY, day_id INTEGER NOT NULL,
        score INTEGER NOT NULL, total INTEGER NOT NULL, answers TEXT)""",
    """CREATE TABLE day_work (id INTEGER PRIMARY KEY, day_id INTEGER NOT NULL UNIQUE,
        exercise_submission TEXT, test_result TEXT, explain_answer TEXT,
        flow_answer TEXT, role_answer TEXT, variant_answer TEXT,
        completed BOOLEAN)""",
    """CREATE TABLE checklist_items (id INTEGER PRIMARY KEY, "group" VARCHAR NOT NULL,
        text TEXT NOT NULL, "order" INTEGER, done BOOLEAN)""",
    """CREATE TABLE journal_entries (id INTEGER PRIMARY KEY, date VARCHAR NOT NULL,
        topic VARCHAR, done TEXT, stuck TEXT, ai_use TEXT, can_explain VARCHAR,
        next_step TEXT)""",
]


def _v1_db_with_progress(tmp_path):
    """Return (engine, Session) on a v1-schema DB holding fake progress."""
    path = tmp_path / "v1.db"
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        for ddl in V1_DDL:
            conn.execute(text(ddl))
        conn.execute(text(
            "INSERT INTO tracks (id, slug, title, description) "
            "VALUES (1, 'backend-intern', 'Backend Intern', '')"))
        conn.execute(text(
            "INSERT INTO modules (id, track_id, slug, title, description, \"order\") "
            "VALUES (1, 1, 'm1', 'Module 1', '', 1)"))
        conn.execute(text(
            "INSERT INTO days (id, module_id, number, slug, title) "
            "VALUES (1, 1, 1, 'day-1', 'Day 1 old title')"))
        conn.execute(text(
            "INSERT INTO quiz_questions (id, day_id, question, options, correct_index) "
            "VALUES (1, 1, 'Q?', '[\"a\", \"b\"]', 0)"))
        # Fake progress: 1 completed Day, 1 done checklist item, 1 quiz attempt.
        conn.execute(text(
            "INSERT INTO day_work (id, day_id, exercise_submission, completed) "
            "VALUES (1, 1, 'bai nop cu', 1)"))
        conn.execute(text(
            "INSERT INTO checklist_items (id, \"group\", text, \"order\", done) "
            "VALUES (1, 'Hang ngay', 'muc cu', 0, 1)"))
        conn.execute(text(
            "INSERT INTO quiz_attempts (id, day_id, score, total, answers) "
            "VALUES (1, 1, 4, 4, '[1]')"))
    return engine, sessionmaker(bind=engine)


def test_migration_keeps_progress_and_adds_v2_columns(tmp_path):
    engine, Session = _v1_db_with_progress(tmp_path)

    # Pre-check: v2 columns really absent before migrate().
    cols_before = {r[1] for r in
                   sqlite3.connect(str(tmp_path / "v1.db")).execute("PRAGMA table_info(days)")}
    assert "importance" not in cols_before

    added = migrate(engine)
    assert sorted(added) == sorted(f"{t}.{c}" for t, c, _, _ in NEW_COLUMNS)

    # Idempotent: second run adds nothing.
    assert migrate(engine) == []

    # New tables (extension_topics) are created by create_all, not migrate().
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        # Progress byte-identical.
        work = db.query(models.DayWork).filter_by(day_id=1).one()
        assert work.completed is True
        assert work.exercise_submission == "bai nop cu"
        item = db.query(models.ChecklistItem).filter_by(id=1).one()
        assert item.done is True and item.text == "muc cu"
        attempt = db.query(models.QuizAttempt).filter_by(id=1).one()
        assert (attempt.score, attempt.total) == (4, 4)
        # New columns exist with defaults on the old row.
        assert work.flow_puzzle_passed is False
        assert work.self_note == ""
        day = db.query(models.Day).filter_by(id=1).one()
        assert day.importance == "should"
        assert day.bug_code == ""
    finally:
        db.close()

    # Seed refresh on top of the migrated DB: content updates, progress stays.
    db = Session()
    try:
        seed(db)
        work = db.query(models.DayWork).filter_by(day_id=1).one()
        assert work.completed is True
        assert work.exercise_submission == "bai nop cu"
        item = db.query(models.ChecklistItem).filter_by(id=1).one()
        assert item.done is True
        # The old Day 1 row was refreshed to the seeded v2 content.
        day = db.query(models.Day).filter_by(id=1).one()
        assert day.title.startswith("Day 1")
    finally:
        db.close()


def test_fresh_seed_has_v2_defaults():
    """A fresh (empty) DB seeds with the v2 content present (Phase C)."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    migrate(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed(db)
        day = db.query(models.Day).filter_by(number=1).one()
        # Phase C content: Day 1 card + bug are authored, not defaults.
        assert day.importance == "must"
        assert day.real_world_use.strip()
        assert day.bug_line is not None
        work = db.query(models.DayWork).filter_by(day_id=1).first()
        assert work is None  # no progress on a fresh DB
    finally:
        db.close()


def test_v2_content_complete_for_all_days():
    """T029: every Day must have an enterprise card, a bug snippet and exactly
    2 follow-up questions. A Day missing any of them must render
    'đang bổ sung' and its gates cannot pass — this test enforces that."""
    import json
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    migrate(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed(db)
        days = db.query(models.Day).order_by(models.Day.number).all()
        assert len(days) == 14
        for day in days:
            assert day.importance in ("must", "should", "nice"), f"Day {day.number}"
            assert (day.real_world_use or "").strip(), f"Day {day.number}: no real-world use"
            pitfalls = json.loads(day.pitfalls or "[]")
            assert len(pitfalls) >= 2, f"Day {day.number}: <2 pitfalls"
            lines = [ln for ln in (day.bug_code or "").split("\n") if ln.strip()]
            assert 5 <= len(lines) <= 10, f"Day {day.number}: bug has {len(lines)} lines"
            assert day.bug_line is not None, f"Day {day.number}: no bug_line"
            assert 0 <= day.bug_line < len((day.bug_code or "").split("\n")), \
                f"Day {day.number}: bug_line out of range"
            reasons = json.loads(day.bug_reasons or "[]")
            assert len(reasons) == 4, f"Day {day.number}: {len(reasons)} reasons"
            assert day.bug_correct_reason is not None
            assert 0 <= day.bug_correct_reason < 4, f"Day {day.number}"
            followups = json.loads(day.followup_questions or "[]")
            assert len(followups) == 2, f"Day {day.number}: {len(followups)} follow-ups"
    finally:
        db.close()
