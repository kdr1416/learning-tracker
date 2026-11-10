"""Idempotent schema migration for Learning Tracker v2.

Why this file exists: ``Base.metadata.create_all`` creates missing tables but
never adds columns to tables that already exist. The production Neon database
already has the v1 tables, so new v2 columns need explicit
``ALTER TABLE ... ADD COLUMN IF NOT EXISTS``.

Rules:
- Additive only: this file NEVER issues UPDATE/DELETE/DROP against any table,
  and never touches progress rows (day_work, quiz_attempts, checklist_items,
  journal_entries).
- Idempotent: safe to run on every startup, on a fresh DB and on a v1 DB.
- SQLite (local dev) has no ``ADD COLUMN IF NOT EXISTS`` on older versions, so
  columns are checked via ``PRAGMA table_info`` first. Postgres uses
  ``IF NOT EXISTS`` directly.
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

# (table, column, DDL type, DEFAULT clause or None) — must match models.py.
# Existing rows get the DEFAULT value when the column is added, so a v1 row
# never reads back NULL for a gate field (NULL would break gate evaluation).
NEW_COLUMNS: list[tuple[str, str, str, str | None]] = [
    ("days", "importance", "VARCHAR", "'should'"),
    ("days", "real_world_use", "TEXT", "''"),
    ("days", "pitfalls", "TEXT", "'[]'"),
    ("days", "bug_code", "TEXT", "''"),
    ("days", "bug_line", "INTEGER", None),
    ("days", "bug_reasons", "TEXT", "'[]'"),
    ("days", "bug_correct_reason", "INTEGER", None),
    ("days", "correct_code", "TEXT", "''"),
    ("days", "followup_questions", "TEXT", "'[]'"),
    ("days", "sim_scenarios", "TEXT", "'[]'"),
    ("days", "flow_step_code", "TEXT", "'[]'"),
    ("day_work", "flow_puzzle_passed", "BOOLEAN", "FALSE"),
    ("day_work", "bug_passed", "BOOLEAN", "FALSE"),
    ("day_work", "self_note", "TEXT", "''"),
    ("day_work", "followup_answers", "TEXT", "'[]'"),
    ("day_work", "summary", "TEXT", "''"),
]


def _sqlite_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def migrate(engine: Engine) -> list[str]:
    """Add every missing v2 column. Returns the list of columns added."""
    dialect = engine.dialect.name
    added: list[str] = []
    with engine.begin() as conn:
        for table, column, coltype, default in NEW_COLUMNS:
            ddl = f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
            if default is not None:
                ddl += f" DEFAULT {default}"
            if dialect == "sqlite":
                if column in _sqlite_columns(conn, table):
                    continue
                conn.execute(text(ddl))
            else:  # postgres and others supporting IF NOT EXISTS
                conn.execute(text(ddl.replace("ADD COLUMN", "ADD COLUMN IF NOT EXISTS")))
            added.append(f"{table}.{column}")
    return added
