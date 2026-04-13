"""Watchlist routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from stockpredict.api.deps import get_current_user, get_db
from stockpredict.api.security import normalize_ticker
from stockpredict.db import crud
from stockpredict.db.models import User

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def _serialize_watchlist_item(item) -> dict:
    return {
        "id": item.id,
        "ticker": item.ticker,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await crud.list_watchlist(db, current_user.id)
    return [_serialize_watchlist_item(item) for item in items]


@router.post("/{ticker}")
async def add_watchlist_item(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        normalized_ticker = normalize_ticker(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    item = await crud.add_watchlist_item(db, current_user.id, normalized_ticker)
    return _serialize_watchlist_item(item)


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_item(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        normalized_ticker = normalize_ticker(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    await crud.remove_watchlist_item(db, current_user.id, normalized_ticker)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
