"""GET /api/history/{ticker} — past analyses list."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from stockpredict.api.deps import get_current_user, get_db
from stockpredict.db import crud
from stockpredict.db.models import User

router = APIRouter()


@router.get("/history/{ticker}")
async def get_history(
    ticker: str,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List past analyses for a ticker (lightweight, no full report)."""
    analyses = await crud.list_history(db, current_user.id, ticker.upper(), limit=limit)
    return [
        {
            "id": a.id,
            "ticker": a.ticker,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "as_of_price": a.as_of_price,
            "short_term": {"score": a.short_term_score, "verdict": a.short_term_verdict},
            "medium_term": {"score": a.medium_term_score, "verdict": a.medium_term_verdict},
            "long_term": {"score": a.long_term_score, "verdict": a.long_term_verdict},
            "ai_summary_preview": (a.ai_summary[:200] + "...") if a.ai_summary else None,
        }
        for a in analyses
    ]


@router.get("/recent")
async def get_recent(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List most recent analyses across all tickers."""
    analyses = await crud.list_recent(db, current_user.id, limit=limit)
    return [
        {
            "id": a.id,
            "ticker": a.ticker,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "as_of_price": a.as_of_price,
            "short_term": {"score": a.short_term_score, "verdict": a.short_term_verdict},
            "medium_term": {"score": a.medium_term_score, "verdict": a.medium_term_verdict},
            "long_term": {"score": a.long_term_score, "verdict": a.long_term_verdict},
        }
        for a in analyses
    ]
