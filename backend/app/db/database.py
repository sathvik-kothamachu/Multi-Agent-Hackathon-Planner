"""SQLAlchemy engine, session factory, and Base.

The relational DB stores lightweight project metadata + the (optional) baseline
result for the ablation. The evolving *workflow* state lives in the LangGraph
SQLite checkpointer, keyed by thread_id (= project_id) — not here.
"""
from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

Base = declarative_base()

_settings = get_settings()
_connect_args = (
    {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(_settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create tables, then patch in any columns added after the DB was first created.

    ``create_all`` only creates *missing tables*; it never alters an existing one.
    A dev DB created before a column was added (e.g. ``using_ai``) would therefore
    still be missing it, and every INSERT would fail with a 500. We reconcile the
    live schema against the ORM here so the app self-heals on startup.
    """
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


# SQLAlchemy type -> SQLite column type + default, for additive migrations.
def _sqlite_coltype(col) -> str:
    name = col.type.__class__.__name__.upper()
    if "INT" in name:
        return "INTEGER"
    if any(t in name for t in ("TEXT", "STRING", "VARCHAR")):
        return "TEXT"
    if "DATETIME" in name or "DATE" in name:
        return "DATETIME"
    return "TEXT"


def _add_missing_columns() -> None:
    """Additively add any ORM columns absent from the live SQLite tables."""
    if not _settings.database_url.startswith("sqlite"):
        return
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            live_cols = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in live_cols:
                    continue
                coltype = _sqlite_coltype(col)
                default = col.default.arg if col.default is not None else None
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {coltype}'
                if isinstance(default, (int, float)):
                    ddl += f" DEFAULT {default}"
                elif isinstance(default, str):
                    ddl += f" DEFAULT '{default}'"
                conn.execute(text(ddl))


def get_session() -> Iterator[Session]:
    """FastAPI dependency: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
