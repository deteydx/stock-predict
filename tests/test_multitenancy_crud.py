from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from stockpredict.api.security import hash_password, verify_password
from stockpredict.db import crud
from stockpredict.db.models import Analysis, Base


@pytest_asyncio.fixture
async def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_password_hash_round_trip():
    encoded = hash_password("supersecret")
    assert verify_password("supersecret", encoded) is True
    assert verify_password("wrong-password", encoded) is False


@pytest.mark.asyncio
async def test_watchlist_is_unique_per_user(db_session):
    first_user = await crud.create_user(db_session, "first@example.com", hash_password("password123"))
    second_user = await crud.create_user(db_session, "second@example.com", hash_password("password123"))

    await crud.add_watchlist_item(db_session, first_user.id, "AAPL")
    await crud.add_watchlist_item(db_session, first_user.id, "AAPL")
    await crud.add_watchlist_item(db_session, second_user.id, "AAPL")

    first_items = await crud.list_watchlist(db_session, first_user.id)
    second_items = await crud.list_watchlist(db_session, second_user.id)

    assert [item.ticker for item in first_items] == ["AAPL"]
    assert [item.ticker for item in second_items] == ["AAPL"]


@pytest.mark.asyncio
async def test_analysis_queries_are_scoped_to_user(db_session):
    first_user = await crud.create_user(db_session, "alpha@example.com", hash_password("password123"))
    second_user = await crud.create_user(db_session, "beta@example.com", hash_password("password123"))

    first_analysis = Analysis(
        user_id=first_user.id,
        ticker="AAPL",
        status="completed",
        created_at=datetime.utcnow() - timedelta(minutes=2),
    )
    second_analysis = Analysis(
        user_id=second_user.id,
        ticker="AAPL",
        status="completed",
        created_at=datetime.utcnow() - timedelta(minutes=1),
    )
    running_analysis = Analysis(
        user_id=first_user.id,
        ticker="MSFT",
        status="running",
        created_at=datetime.utcnow(),
    )

    await crud.save_analysis(db_session, first_analysis)
    await crud.save_analysis(db_session, second_analysis)
    await crud.save_analysis(db_session, running_analysis)

    first_recent = await crud.list_recent(db_session, first_user.id)
    second_recent = await crud.list_recent(db_session, second_user.id)
    first_latest_aapl = await crud.get_latest(db_session, first_user.id, "AAPL")
    second_latest_aapl = await crud.get_latest(db_session, second_user.id, "AAPL")
    first_running_msft = await crud.get_running(db_session, first_user.id, "MSFT")

    assert [analysis.id for analysis in first_recent] == [first_analysis.id]
    assert [analysis.id for analysis in second_recent] == [second_analysis.id]
    assert first_latest_aapl is not None and first_latest_aapl.id == first_analysis.id
    assert second_latest_aapl is not None and second_latest_aapl.id == second_analysis.id
    assert first_running_msft is not None and first_running_msft.id == running_analysis.id
