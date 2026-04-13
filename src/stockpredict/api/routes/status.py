"""GET /api/status/{task_id} — SSE progress stream."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from stockpredict.api.deps import get_current_user, get_db
from stockpredict.api.routes.analyze import _progress_store, _progress_store_created
from stockpredict.db import crud
from stockpredict.db.models import User

router = APIRouter()


@router.get("/status/{task_id}")
async def get_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream analysis progress via Server-Sent Events."""
    analysis = await crud.get_analysis_for_user(db, task_id, current_user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def event_generator():
        sent_count = 0
        max_wait = 300  # 5 minutes max

        for _ in range(max_wait * 2):  # Check every 0.5s
            updates = _progress_store.get(task_id, [])

            # Send any new updates
            while sent_count < len(updates):
                update = updates[sent_count]
                yield {"data": json.dumps(update, ensure_ascii=False)}
                sent_count += 1

                # Check if we're done
                if update.get("step") in ("completed", "error"):
                    # Clean up progress store
                    _progress_store.pop(task_id, None)
                    _progress_store_created.pop(task_id, None)
                    return

            await asyncio.sleep(0.5)

        # Timeout — check DB for final status
        latest_analysis = await crud.get_analysis_for_user(db, task_id, current_user.id)
        if latest_analysis and latest_analysis.status == "completed":
            yield {
                "data": json.dumps({
                    "step": "completed",
                    "progress": 100,
                    "message": "分析完成",
                    "analysis_id": task_id,
                })
            }
        else:
            yield {
                "data": json.dumps({
                    "step": "error",
                    "progress": -1,
                    "message": "分析超时",
                })
            }
        _progress_store.pop(task_id, None)
        _progress_store_created.pop(task_id, None)

    return EventSourceResponse(event_generator())
