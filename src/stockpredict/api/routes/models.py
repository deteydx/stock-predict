"""POST /api/models — fetch the live list of usable chat models from the provider."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from stockpredict.api.deps import get_current_user
from stockpredict.db.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


_FALLBACK_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
    ],
    "claude": [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
}

_RECOMMENDED: dict[str, str] = {
    "openai": "gpt-5.4",
    "claude": "claude-sonnet-4-6",
}

# Cache: (provider, sha256(api_key)) -> (expires_at, models)
_CACHE_TTL_SECONDS = 3600
_models_cache: dict[tuple[str, str], tuple[float, list[str]]] = {}


class ListModelsRequest(BaseModel):
    provider: Literal["openai", "claude"]
    api_key: str = Field(default="", max_length=512)

    @field_validator("api_key")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class ListModelsResponse(BaseModel):
    models: list[str]
    recommended: str
    source: Literal["live", "fallback"]


def _cache_key(provider: str, api_key: str) -> tuple[str, str]:
    return provider, hashlib.sha256(api_key.encode()).hexdigest()


def _filter_openai(model_ids: list[str]) -> list[str]:
    """Keep chat-capable models and drop embeddings/audio/image/realtime variants."""
    blocklist = ("embedding", "tts", "whisper", "dall-e", "image", "audio", "moderation", "realtime")
    keep = [
        m for m in model_ids
        if (m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3") or m.startswith("o4"))
        and not any(b in m for b in blocklist)
    ]
    # Newest first by string sort (works for gpt-5 > gpt-4 > gpt-3.5)
    keep.sort(reverse=True)
    return keep


def _filter_claude(model_ids: list[str]) -> list[str]:
    keep = [m for m in model_ids if m.startswith("claude-")]
    keep.sort(reverse=True)
    return keep


async def _fetch_openai_models(api_key: str) -> list[str]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    try:
        result = await client.models.list()
        ids = [m.id for m in result.data]
    finally:
        await client.close()
    return _filter_openai(ids)


async def _fetch_claude_models(api_key: str) -> list[str]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        # Anthropic returns paginated list; first page is plenty for UI.
        result = await client.models.list(limit=50)
        ids = [m.id for m in result.data]
    finally:
        await client.close()
    return _filter_claude(ids)


@router.post("/models", response_model=ListModelsResponse)
async def list_models(
    request: ListModelsRequest,
    _: User = Depends(get_current_user),
) -> ListModelsResponse:
    provider = request.provider
    api_key = request.api_key

    if not api_key:
        return ListModelsResponse(
            models=_FALLBACK_MODELS[provider],
            recommended=_RECOMMENDED[provider],
            source="fallback",
        )

    key = _cache_key(provider, api_key)
    now = time.monotonic()
    cached = _models_cache.get(key)
    if cached and cached[0] > now:
        return ListModelsResponse(
            models=cached[1],
            recommended=_RECOMMENDED[provider] if _RECOMMENDED[provider] in cached[1] else (cached[1][0] if cached[1] else ""),
            source="live",
        )

    try:
        models = (
            await _fetch_openai_models(api_key)
            if provider == "openai"
            else await _fetch_claude_models(api_key)
        )
    except Exception as exc:
        logger.warning("Failed to fetch %s models live, using fallback: %s", provider, exc)
        # Surface auth errors to the user; other failures silently fall back.
        msg = str(exc).lower()
        if "401" in msg or "unauthorized" in msg or "invalid" in msg and "key" in msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"{provider} API key was rejected",
            ) from exc
        return ListModelsResponse(
            models=_FALLBACK_MODELS[provider],
            recommended=_RECOMMENDED[provider],
            source="fallback",
        )

    if not models:
        return ListModelsResponse(
            models=_FALLBACK_MODELS[provider],
            recommended=_RECOMMENDED[provider],
            source="fallback",
        )

    _models_cache[key] = (now + _CACHE_TTL_SECONDS, models)
    recommended = _RECOMMENDED[provider] if _RECOMMENDED[provider] in models else models[0]
    return ListModelsResponse(models=models, recommended=recommended, source="live")
