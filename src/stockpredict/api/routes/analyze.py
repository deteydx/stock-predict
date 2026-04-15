"""POST /api/analyze/{ticker} — trigger or retrieve analysis."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from stockpredict.api.deps import get_app_settings, get_current_user, get_db
from stockpredict.api.security import normalize_ticker
from stockpredict.db import crud
from stockpredict.db.models import Analysis, User

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory progress store (task_id → list of updates)
# In production, use Redis or similar
_progress_store: dict[int, list[dict]] = {}
_progress_store_created: dict[int, float] = {}  # task_id → creation timestamp

_PROGRESS_TTL_SECONDS = 600  # 10 minutes

_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-5.4",
    "claude": "claude-sonnet-4-6",
}


def _cleanup_stale_progress():
    """Remove progress entries older than TTL to prevent memory leaks."""
    now = time.monotonic()
    stale_ids = [
        tid for tid, created in _progress_store_created.items()
        if now - created > _PROGRESS_TTL_SECONDS
    ]
    for tid in stale_ids:
        _progress_store.pop(tid, None)
        _progress_store_created.pop(tid, None)


@dataclass(frozen=True)
class RequestedAIConfig:
    enabled: bool
    provider: str | None = None
    model: str | None = None
    language: str = "zh"


class AnalyzeAIRequest(BaseModel):
    provider: Literal["openai", "claude"] = "openai"
    model: str = Field(default="", max_length=120)
    api_key: str = Field(default="", max_length=512)

    @field_validator("model", "api_key")
    @classmethod
    def _strip_value(cls, value: str) -> str:
        return value.strip()


class AnalyzeRequest(BaseModel):
    force_refresh: bool = False
    ai: AnalyzeAIRequest | None = None
    language: Literal["zh", "en"] = "zh"


class AnalyzeResponse(BaseModel):
    task_id: int | None = None
    analysis_id: int | None = None
    cached: bool = False
    status: str = "started"


def _default_model_for_provider(provider: Literal["openai", "claude"], settings: Settings) -> str:
    if provider == "openai":
        return settings.ai.openai_model or _DEFAULT_MODELS["openai"]
    return settings.ai.claude_model or _DEFAULT_MODELS["claude"]


def _build_runtime_settings(
    settings: Settings,
    request_ai: AnalyzeAIRequest | None,
    language: str = "zh",
) -> tuple[Settings, RequestedAIConfig]:
    runtime_settings = settings.model_copy(deep=True)
    runtime_ai = runtime_settings.ai.model_copy(deep=True)

    if request_ai is None:
        if not runtime_ai.ai_enabled:
            return runtime_settings, RequestedAIConfig(enabled=False, language=language)

        model = (
            runtime_ai.openai_model
            if runtime_ai.ai_provider == "openai"
            else runtime_ai.claude_model
        )
        return runtime_settings, RequestedAIConfig(
            enabled=True,
            provider=runtime_ai.ai_provider,
            model=model,
            language=language,
        )

    provider = request_ai.provider
    model = request_ai.model or _default_model_for_provider(provider, settings)
    api_key = request_ai.api_key

    runtime_ai.ai_enabled = bool(api_key)
    runtime_ai.ai_provider = provider
    runtime_ai.openai_api_key = api_key if provider == "openai" else ""
    runtime_ai.anthropic_api_key = api_key if provider == "claude" else ""

    if provider == "openai":
        runtime_ai.openai_model = model
    else:
        runtime_ai.claude_model = model

    runtime_settings.ai = runtime_ai

    if not runtime_ai.ai_enabled:
        return runtime_settings, RequestedAIConfig(enabled=False, language=language)

    return runtime_settings, RequestedAIConfig(
        enabled=True,
        provider=provider,
        model=model,
        language=language,
    )


def _matches_requested_ai_config(analysis: Analysis, requested_ai: RequestedAIConfig) -> bool:
    if not requested_ai.enabled:
        return analysis.ai_provider is None and analysis.ai_model is None
    stored_lang = getattr(analysis, "ai_language", None) or "zh"
    return (
        analysis.ai_provider == requested_ai.provider
        and analysis.ai_model == requested_ai.model
        and stored_lang == requested_ai.language
    )


async def _run_pipeline(analysis_id: int, ticker: str, settings: Settings, language: str = "zh"):
    """Background task that runs the analysis pipeline."""
    from stockpredict.db.database import async_session_factory
    from stockpredict.pipeline import run_analysis
    from stockpredict.types import ProgressUpdate

    async def progress_cb(update: ProgressUpdate):
        if analysis_id not in _progress_store:
            _progress_store[analysis_id] = []
        _progress_store[analysis_id].append(update.model_dump())

    try:
        report = await run_analysis(
            ticker=ticker,
            ibkr_client=None,  # Will fallback to yfinance
            settings=settings,
            progress_callback=progress_cb,
            language=language,
        )

        # Save to database
        async with async_session_factory() as db:
            await crud.update_analysis(
                db,
                analysis_id,
                status="completed",
                as_of_price=report.as_of_price,
                short_term_score=report.short_term.raw_score if report.short_term else None,
                short_term_verdict=report.short_term.verdict.value if report.short_term else None,
                short_term_confidence=report.short_term.confidence if report.short_term else None,
                medium_term_score=report.medium_term.raw_score if report.medium_term else None,
                medium_term_verdict=report.medium_term.verdict.value if report.medium_term else None,
                medium_term_confidence=report.medium_term.confidence if report.medium_term else None,
                long_term_score=report.long_term.raw_score if report.long_term else None,
                long_term_verdict=report.long_term.verdict.value if report.long_term else None,
                long_term_confidence=report.long_term.confidence if report.long_term else None,
                report_json=report.model_dump_json(),
                ai_summary=report.ai_summary,
                ai_provider=report.ai_provider,
                ai_model=report.ai_model,
                ai_language=report.ai_language,
            )

        completed_msg = "Analysis complete" if language == "en" else "分析完成"
        await progress_cb(ProgressUpdate(step="completed", progress=100, message=completed_msg))

    except Exception as e:
        logger.error("Pipeline failed for %s: %s", ticker, e, exc_info=True)
        async with async_session_factory() as db:
            await crud.update_analysis(db, analysis_id, status="failed")
        if analysis_id not in _progress_store:
            _progress_store[analysis_id] = []
            _progress_store_created.setdefault(analysis_id, time.monotonic())
        _progress_store[analysis_id].append({
            "step": "error", "progress": -1, "message": str(e)
        })


@router.post("/analyze/{ticker}", response_model=AnalyzeResponse)
async def analyze_ticker(
    ticker: str,
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    current_user: User = Depends(get_current_user),
):
    """Start a new analysis or return a cached one."""
    try:
        ticker = normalize_ticker(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    runtime_settings, requested_ai = _build_runtime_settings(settings, request.ai, request.language)

    # Check for cached result
    if not request.force_refresh:
        cached = await crud.get_latest(db, current_user.id, ticker, max_age_hours=24)
        if cached and _matches_requested_ai_config(cached, requested_ai):
            return AnalyzeResponse(
                analysis_id=cached.id,
                cached=True,
                status="completed",
            )

    running = await crud.get_running(db, current_user.id, ticker, max_age_minutes=10)
    if running and _matches_requested_ai_config(running, requested_ai):
        return AnalyzeResponse(
            task_id=running.id,
            analysis_id=running.id,
            cached=False,
            status="running",
        )

    # Create a new analysis record
    analysis = Analysis(
        user_id=current_user.id,
        ticker=ticker,
        status="running",
        created_at=datetime.utcnow(),
        ai_provider=requested_ai.provider,
        ai_model=requested_ai.model,
        ai_language=requested_ai.language if requested_ai.enabled else None,
    )
    analysis_id = await crud.save_analysis(db, analysis)

    # Initialize progress store (and clean up stale entries)
    _cleanup_stale_progress()
    _progress_store[analysis_id] = []
    _progress_store_created[analysis_id] = time.monotonic()

    # Run pipeline in background
    background_tasks.add_task(_run_pipeline, analysis_id, ticker, runtime_settings, request.language)

    return AnalyzeResponse(
        task_id=analysis_id,
        analysis_id=analysis_id,
        cached=False,
        status="running",
    )
