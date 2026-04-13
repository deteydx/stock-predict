"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from stockpredict.api.deps import (
    get_app_settings,
    get_current_user,
    get_optional_current_session,
    get_db,
)
from stockpredict.api.security import (
    build_session_expiry,
    generate_session_token,
    hash_password,
    hash_session_token,
    normalize_email,
    validate_email,
    validate_password,
    verify_password,
)
from stockpredict.db import crud
from stockpredict.db.models import User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        try:
            return validate_email(value)
        except ValueError as exc:
            raise ValueError("invalid_email") from exc

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        try:
            return validate_password(value)
        except ValueError as exc:
            raise ValueError("password_too_short") from exc


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str | None


class AuthResponse(BaseModel):
    user: UserResponse


def _serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.auth_session_days * 24 * 60 * 60,
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
    )


async def _issue_session(
    response: Response,
    db: AsyncSession,
    user: User,
    settings: Settings,
) -> AuthResponse:
    token = generate_session_token()
    await crud.create_user_session(
        db,
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=build_session_expiry(settings),
    )
    _set_session_cookie(response, token, settings)
    return AuthResponse(user=_serialize_user(user))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: AuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    email = normalize_email(payload.email)
    existing = await crud.get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_registered",
        )

    try:
        user = await crud.create_user(db, email=email, password_hash=hash_password(payload.password))
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_registered",
        ) from exc

    return await _issue_session(response, db, user, settings)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: AuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    user = await crud.get_user_by_email(db, normalize_email(payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )

    return await _issue_session(response, db, user, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: UserSession | None = Depends(get_optional_current_session),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    if session is not None:
        await crud.delete_user_session(db, session.id)
    _clear_session_cookie(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@router.get("/me", response_model=AuthResponse)
async def me(current_user: User = Depends(get_current_user)):
    return AuthResponse(user=_serialize_user(current_user))
