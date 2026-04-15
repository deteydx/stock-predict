"""SQLAlchemy ORM models for persisting analysis results."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_token_hash", "token_hash", unique=True),
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_watchlist_items_user_ticker"),
        Index("ix_watchlist_items_user_id", "user_id"),
        Index("ix_watchlist_items_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_ticker", "ticker"),
        Index("ix_analyses_created_at", "created_at"),
        Index("ix_analyses_user_id", "user_id"),
        Index("ix_analyses_user_ticker_created_at", "user_id", "ticker", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    as_of_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Denormalized scores for fast list queries
    short_term_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    short_term_verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    short_term_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    medium_term_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    medium_term_verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    medium_term_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    long_term_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    long_term_verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    long_term_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Full report (JSON blob — complete Report model serialized)
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI analysis
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_language: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # Config snapshot
    weights_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ml_model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
