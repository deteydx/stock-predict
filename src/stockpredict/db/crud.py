"""CRUD operations for users, sessions, watchlists, and analyses."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from stockpredict.db.models import Analysis, User, UserSession, WatchlistItem


async def create_user(db: AsyncSession, email: str, password_hash: str) -> User:
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def create_user_session(
    db: AsyncSession,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_user_session_by_token_hash(
    db: AsyncSession,
    token_hash: str,
) -> UserSession | None:
    stmt = select(UserSession).where(UserSession.token_hash == token_hash)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_user_session(db: AsyncSession, session_id: int) -> None:
    session = await db.get(UserSession, session_id)
    if session is None:
        return
    await db.delete(session)
    await db.commit()


async def get_watchlist_item(
    db: AsyncSession,
    user_id: int,
    ticker: str,
) -> WatchlistItem | None:
    stmt = select(WatchlistItem).where(
        WatchlistItem.user_id == user_id,
        WatchlistItem.ticker == ticker.upper(),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_watchlist_item(
    db: AsyncSession,
    user_id: int,
    ticker: str,
) -> WatchlistItem:
    normalized_ticker = ticker.upper()
    existing = await get_watchlist_item(db, user_id, normalized_ticker)
    if existing:
        return existing

    item = WatchlistItem(user_id=user_id, ticker=normalized_ticker)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_watchlist_item(
    db: AsyncSession,
    user_id: int,
    ticker: str,
) -> bool:
    item = await get_watchlist_item(db, user_id, ticker)
    if item is None:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def list_watchlist(db: AsyncSession, user_id: int) -> list[WatchlistItem]:
    stmt = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.ticker.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def save_analysis(db: AsyncSession, analysis: Analysis) -> int:
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis.id


async def update_analysis(db: AsyncSession, analysis_id: int, **kwargs) -> None:
    result = await db.get(Analysis, analysis_id)
    if result:
        for key, value in kwargs.items():
            setattr(result, key, value)
        await db.commit()


async def get_analysis_for_user(
    db: AsyncSession,
    analysis_id: int,
    user_id: int,
) -> Analysis | None:
    stmt = select(Analysis).where(
        Analysis.id == analysis_id,
        Analysis.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_analysis_for_user(
    db: AsyncSession,
    analysis_id: int,
    user_id: int,
) -> bool:
    analysis = await get_analysis_for_user(db, analysis_id, user_id)
    if analysis is None:
        return False
    await db.delete(analysis)
    await db.commit()
    return True


async def get_latest(
    db: AsyncSession,
    user_id: int,
    ticker: str,
    max_age_hours: int = 24,
) -> Analysis | None:
    """Get the user's most recent completed analysis for a ticker within max_age_hours."""
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    stmt = (
        select(Analysis)
        .where(
            Analysis.user_id == user_id,
            Analysis.ticker == ticker.upper(),
            Analysis.status == "completed",
            Analysis.created_at >= cutoff,
        )
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_running(
    db: AsyncSession,
    user_id: int,
    ticker: str,
    max_age_minutes: int = 10,
) -> Analysis | None:
    """Get the user's most recent running analysis for a ticker within max_age_minutes."""
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    stmt = (
        select(Analysis)
        .where(
            Analysis.user_id == user_id,
            Analysis.ticker == ticker.upper(),
            Analysis.status == "running",
            Analysis.created_at >= cutoff,
        )
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_history(
    db: AsyncSession,
    user_id: int,
    ticker: str,
    limit: int = 20,
) -> list[Analysis]:
    stmt = (
        select(Analysis)
        .where(
            Analysis.user_id == user_id,
            Analysis.ticker == ticker.upper(),
            Analysis.status == "completed",
        )
        .order_by(Analysis.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_recent(db: AsyncSession, user_id: int, limit: int = 20) -> list[Analysis]:
    """List the user's most recent analyses, one per ticker (latest only)."""
    latest_per_ticker = (
        select(
            Analysis.ticker.label("ticker"),
            func.max(Analysis.created_at).label("max_ts"),
        )
        .where(
            Analysis.user_id == user_id,
            Analysis.status == "completed",
        )
        .group_by(Analysis.ticker)
        .subquery()
    )
    stmt = (
        select(Analysis)
        .join(
            latest_per_ticker,
            and_(
                Analysis.ticker == latest_per_ticker.c.ticker,
                Analysis.created_at == latest_per_ticker.c.max_ts,
            ),
        )
        .where(
            Analysis.user_id == user_id,
            Analysis.status == "completed",
        )
        .order_by(Analysis.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
