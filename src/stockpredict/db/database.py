"""SQLite database setup via SQLAlchemy async."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import event, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import get_settings


def _ensure_db_dir(url: str) -> None:
    """Create parent directory for SQLite file if needed."""
    if "sqlite" in url:
        # Extract path from URL like sqlite+aiosqlite:///./data/stockpredict.db
        db_path = url.split("///")[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_settings = get_settings()
_ensure_db_dir(_settings.database_url)

engine = create_async_engine(_settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


if "sqlite" in _settings.database_url:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _run_migrations(sync_conn) -> None:
    inspector = inspect(sync_conn)
    table_names = set(inspector.get_table_names())

    if "analyses" not in table_names:
        return

    analysis_columns = {column["name"] for column in inspector.get_columns("analyses")}
    if "user_id" not in analysis_columns:
        sync_conn.execute(text("ALTER TABLE analyses ADD COLUMN user_id INTEGER"))

    sync_conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_analyses_user_id ON analyses (user_id)"
    ))
    sync_conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_analyses_user_ticker_created_at "
        "ON analyses (user_id, ticker, created_at)"
    ))
    sync_conn.execute(text("DELETE FROM analyses WHERE user_id IS NULL"))


async def init_db() -> None:
    """Create all tables."""
    from stockpredict.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_run_migrations)
