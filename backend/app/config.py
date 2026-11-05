"""Config. SQLite by default for local dev; PostgreSQL via DATABASE_URL."""
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./learning_tracker.db"
)
# Neon / Supabase / Render Postgres give postgres://... — SQLAlchemy with
# psycopg 3 needs postgresql+psycopg://, so normalise the scheme here.
# sqlite:///./learning_tracker.db still works out of the box for local dev.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
