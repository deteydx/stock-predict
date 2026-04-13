"""GET /api/analysis/{id} — full analysis detail."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from stockpredict.api.deps import get_current_user, get_db
from stockpredict.db import crud
from stockpredict.db.models import User

router = APIRouter()


@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return full analysis detail including report JSON and AI summary."""
    analysis = await crud.get_analysis_for_user(db, analysis_id, current_user.id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    result = {
        "id": analysis.id,
        "ticker": analysis.ticker,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "status": analysis.status,
        "as_of_price": analysis.as_of_price,
        "short_term": {
            "score": analysis.short_term_score,
            "verdict": analysis.short_term_verdict,
            "confidence": analysis.short_term_confidence,
        },
        "medium_term": {
            "score": analysis.medium_term_score,
            "verdict": analysis.medium_term_verdict,
            "confidence": analysis.medium_term_confidence,
        },
        "long_term": {
            "score": analysis.long_term_score,
            "verdict": analysis.long_term_verdict,
            "confidence": analysis.long_term_confidence,
        },
        "ai_summary": analysis.ai_summary,
        "ai_provider": analysis.ai_provider,
        "ai_model": analysis.ai_model,
    }

    # Parse and include full report JSON
    if analysis.report_json:
        try:
            result["report"] = json.loads(analysis.report_json)
        except json.JSONDecodeError:
            result["report"] = None

    return result


@router.delete("/analysis/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a stored analysis record."""
    deleted = await crud.delete_analysis_for_user(db, analysis_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
