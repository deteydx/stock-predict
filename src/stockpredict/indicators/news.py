"""News-based indicators: sentiment aggregation, volume spike, structural events."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime, timedelta

from stockpredict.types import NewsItem

POSITIVE_PHRASES = {
    "beats estimates": 1.8,
    "beat estimates": 1.6,
    "raises guidance": 1.8,
    "raised guidance": 1.8,
    "record revenue": 1.5,
    "record profit": 1.5,
    "strong demand": 1.2,
    "expands partnership": 1.1,
    "new partnership": 1.0,
    "wins contract": 1.3,
    "fda approval": 1.8,
    "share buyback": 1.0,
    "dividend increase": 1.2,
    "price target raised": 1.0,
    "upgraded to": 1.2,
}

NEGATIVE_PHRASES = {
    "misses estimates": -1.8,
    "missed estimates": -1.8,
    "cuts guidance": -1.8,
    "cut guidance": -1.8,
    "lowered guidance": -1.6,
    "weak demand": -1.2,
    "downgraded to": -1.2,
    "price target cut": -1.0,
    "sec investigation": -1.8,
    "doj investigation": -1.8,
    "antitrust probe": -1.6,
    "class action": -1.5,
    "product recall": -1.5,
    "ceo resigns": -1.3,
    "files for bankruptcy": -2.4,
    "bankruptcy filing": -2.4,
}

POSITIVE_WORDS = {
    "approval", "beat", "beats", "bullish", "contract", "expansion", "gain", "gains",
    "growth", "improved", "improves", "outperform", "outperforms", "partnership",
    "profit", "profitable", "rally", "rebound", "raised", "raises", "record", "strong",
    "surge", "surges", "upgrade", "upgraded", "upside",
}

NEGATIVE_WORDS = {
    "antitrust", "bankruptcy", "bearish", "cut", "cuts", "decline", "declines", "default",
    "downgrade", "downgraded", "fraud", "investigation", "lawsuit", "layoff", "layoffs",
    "loss", "losses", "miss", "misses", "probe", "recall", "resign", "resigns", "risk",
    "risks", "slump", "weak",
}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z0-9'-]*", text.lower()))


def estimate_article_sentiment(headline: str, summary: str = "") -> float:
    """Heuristic finance-news sentiment estimate in [-1, +1]."""
    text = " ".join(part for part in [headline, summary] if part).lower()
    if not text.strip():
        return 0.0

    raw_score = 0.0

    for phrase, weight in POSITIVE_PHRASES.items():
        if phrase in text:
            raw_score += weight
    for phrase, weight in NEGATIVE_PHRASES.items():
        if phrase in text:
            raw_score += weight

    tokens = _tokenize(text)
    raw_score += 0.35 * sum(1 for word in POSITIVE_WORDS if word in tokens)
    raw_score -= 0.35 * sum(1 for word in NEGATIVE_WORDS if word in tokens)

    if raw_score == 0:
        return 0.0

    return max(-1.0, min(1.0, math.tanh(raw_score / 3.0)))


async def llm_sentiment_batch(
    articles: list[tuple[str, str]],
    provider: object,  # LLMProvider protocol
) -> list[float]:
    """Use an LLM to score sentiment for a batch of news articles.

    Args:
        articles: List of (headline, summary) pairs.
        provider: An LLM provider with an async `complete(system, user)` method.

    Returns:
        List of sentiment floats in [-1, +1], one per article.
    """
    import json as _json

    if not articles:
        return []

    system = (
        "You are a financial news sentiment analyzer. "
        "For each headline+summary pair, rate sentiment from -1.0 (very bearish) "
        "to +1.0 (very bullish). Consider context: guidance warnings outweigh "
        "estimate beats; lawsuits outweigh minor positive news. "
        "Return ONLY a JSON array of numbers, e.g. [0.3, -0.7, 0.0]. "
        "No other text."
    )

    lines = []
    for i, (headline, summary) in enumerate(articles):
        entry = f"{i+1}. {headline}"
        if summary:
            entry += f" — {summary[:200]}"
        lines.append(entry)
    user = "\n".join(lines)

    try:
        response = await provider.complete(system, user)
        # Extract JSON array from response
        text = response.strip()
        # Handle potential markdown code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        scores = _json.loads(text)
        if isinstance(scores, list) and len(scores) == len(articles):
            return [max(-1.0, min(1.0, float(s))) for s in scores]
    except Exception:
        pass

    # Fallback to keyword-based sentiment
    return [estimate_article_sentiment(h, s) for h, s in articles]


def _time_decay_weight(published_at: datetime | None, now: datetime | None = None) -> float:
    """Exponential decay: 1.0 within 24h, ~0.5 at 7d, ~0 at 30d."""
    if published_at is None:
        return 0.5
    if now is None:
        now = datetime.now(UTC).replace(tzinfo=None)
    hours = max(0, (now - published_at).total_seconds() / 3600)
    return math.exp(-0.004 * hours)  # half-life ~7 days


def sentiment_aggregate(news: list[NewsItem], hours: int = 24) -> float:
    """Weighted average sentiment of news within `hours`, with time decay.

    Returns:
        Sentiment in [-1, +1], or 0.0 if no news.
    """
    if not news:
        return 0.0

    now = datetime.now(UTC).replace(tzinfo=None)
    cutoff = now - timedelta(hours=hours)

    weighted_sum = 0.0
    weight_sum = 0.0

    for item in news:
        if item.published_at and item.published_at < cutoff:
            continue
        w = _time_decay_weight(item.published_at, now) * max(item.relevance, 0.1)
        weighted_sum += item.sentiment * w
        weight_sum += w

    if weight_sum == 0:
        return 0.0
    return weighted_sum / weight_sum


def recent_news_count(news: list[NewsItem], hours: int = 24) -> int:
    """Count news items published within the recent window."""
    if not news:
        return 0

    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)
    return sum(1 for item in news if item.published_at and item.published_at >= cutoff)


def sentiment_score(sentiment: float) -> int:
    """Convert sentiment [-1, +1] to score [-2, +2]."""
    if sentiment > 0.4:
        return 2
    if sentiment > 0.08:
        return 1
    if sentiment > -0.08:
        return 0
    if sentiment > -0.4:
        return -1
    return -2


def news_volume_zscore(
    news: list[NewsItem],
    window_days: int = 1,
    baseline_days: int = 30,
) -> float:
    """Z-score of recent news count vs baseline period.

    Returns:
        Z-score (>2 = unusual volume of news).
    """
    if not news:
        return 0.0

    now = datetime.now(UTC).replace(tzinfo=None)
    recent_cutoff = now - timedelta(days=window_days)
    baseline_cutoff = now - timedelta(days=baseline_days)

    recent_count = sum(
        1 for n in news if n.published_at and n.published_at >= recent_cutoff
    )
    baseline_items = [
        n for n in news if n.published_at and n.published_at >= baseline_cutoff
    ]

    if not baseline_items:
        return 0.0

    # Daily counts over baseline
    daily_avg = len(baseline_items) / baseline_days
    daily_std = max(daily_avg ** 0.5, 0.5)  # Approximate std with sqrt of mean (Poisson)

    expected = daily_avg * window_days
    return (recent_count - expected) / (daily_std * window_days ** 0.5) if daily_std > 0 else 0.0


STRUCTURAL_KEYWORD_SCORES: dict[str, int] = {
    # Negative events
    "antitrust": -2, "anti-trust": -2, "monopoly": -2,
    "ftc": -1, "doj investigation": -2,
    "ceo departure": -1, "ceo resign": -1, "ceo fired": -2, "ceo step down": -1,
    "layoff": -1, "workforce reduction": -1,
    "sec investigation": -2, "fraud": -2, "lawsuit": -1, "class action": -2,
    "fda reject": -2, "regulation": -1,
    # Positive events
    "fda approval": 2, "patent": 1,
    # Ambiguous events (mildly negative due to uncertainty)
    "acquisition": -1, "acquire": -1, "merger": -1, "takeover": -1, "buyout": -1,
    "spinoff": -1, "spin-off": -1, "restructuring": -1,
}

# Keep the set for backward compat
STRUCTURAL_KEYWORDS = set(STRUCTURAL_KEYWORD_SCORES.keys())


def structural_events(news: list[NewsItem], days: int = 30) -> list[tuple[str, int]]:
    """Detect structural news events from headlines within `days`.

    Returns list of (description, score) tuples.
    """
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
    events: list[tuple[str, int]] = []

    for item in news:
        if item.published_at and item.published_at < cutoff:
            continue
        headline_lower = item.headline.lower()
        for kw, kw_score in STRUCTURAL_KEYWORD_SCORES.items():
            if kw in headline_lower:
                events.append((f"{kw}: {item.headline}", kw_score))
                break  # One match per headline

    return events
