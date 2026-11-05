"""Config. SQLite by default for local dev; PostgreSQL via DATABASE_URL."""
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./learning_tracker.db"
)
# SQLAlchemy needs postgresql+psycopg for Postgres URLs; keep the env value
# as-is otherwise (sqlite:///./learning_tracker.db works out of the box).
