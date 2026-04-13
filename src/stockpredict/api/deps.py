"""FastAPI dependency injection and auth helpers."""

from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings, get_settings
from stockpredict.api.security import hash_session_token
from stockpredict.db import crud
from stockpredict.db.database import async_session_factory
from stockpredict.db.models import User, UserSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_app_settings() -> Settings:
    return get_settings()


async def get_optional_current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> UserSession | None:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        return None

    session = await crud.get_user_session_by_token_hash(db, hash_session_token(token))
    if session is None:
        return None

    if session.expires_at <= datetime.utcnow():
        await crud.delete_user_session(db, session.id)
        return None

    return session


async def get_current_session(
    session: UserSession | None = Depends(get_optional_current_session),
) -> UserSession:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )
    return session


async def get_current_user(
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await crud.get_user_by_id(db, session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )
    return user
