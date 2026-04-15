"""Core domain models shared across the entire application."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Horizon(str, Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


class Verdict(str, Enum):
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"

    @classmethod
    def from_score(cls, score: float) -> Verdict:
        if score >= 60:
            return cls.STRONG_BUY
        if score >= 30:
            return cls.BUY
        if score >= -30:
            return cls.HOLD
        if score >= -60:
            return cls.SELL
        return cls.STRONG_SELL


# ---------------------------------------------------------------------------
# Signal (single indicator output)
# ---------------------------------------------------------------------------

class Signal(BaseModel):
    name: str
    value: float | None = None
    score: int = Field(ge=-2, le=2)  # -2..+2
    weight: float = 1.0
    rationale: str = ""


# ---------------------------------------------------------------------------
# Structured support / resistance levels
# ---------------------------------------------------------------------------

class LevelSource(BaseModel):
    kind: str                  # swing_low, swing_high, ma20, ma60, ma120, fib_0.382, hvn, poc, val, vah, pivot_s1, ...
    price: float
    weight: float              # contribution to cluster strength (already includes volume / recency)
    detail: str = ""           # human-readable note (e.g. "swing low 2025-11-03, vol 1.8x")


class Level(BaseModel):
    price: float               # cluster center
    kind: str                  # "support" | "resistance"
    strength: float            # 0..1 normalized within the response
    distance_pct: float        # (level - current) / current — negative = below price
    sources: list[LevelSource] = []


# ---------------------------------------------------------------------------
# Horizon score (aggregated per time horizon)
# ---------------------------------------------------------------------------

class HorizonScore(BaseModel):
    horizon: Horizon
    raw_score: float           # [-100, +100]
    rule_score: float          # [-100, +100] before ML
    ml_probability_up: float | None = None  # 0..1
    verdict: Verdict
    confidence: float          # 0..1
    signals: list[Signal] = []
    levels: list[Level] = []   # fused support/resistance levels (short-term only, for now)
    caveats: list[str] = []


# ---------------------------------------------------------------------------
# News item
# ---------------------------------------------------------------------------

class NewsItem(BaseModel):
    headline: str
    source: str
    url: str = ""
    published_at: datetime | None = None
    sentiment: float = 0.0     # -1..+1
    relevance: float = 0.0     # 0..1
    summary: str = ""
    category: str = "other"


# ---------------------------------------------------------------------------
# Fundamentals snapshot
# ---------------------------------------------------------------------------

class FundamentalsSnapshot(BaseModel):
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    pe_trailing: float | None = None
    pe_forward: float | None = None
    pb: float | None = None
    peg: float | None = None
    ev_ebitda: float | None = None
    roe: float | None = None
    profit_margin: float | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    debt_to_equity: float | None = None
    free_cash_flow: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None


# ---------------------------------------------------------------------------
# Report (complete analysis output)
# ---------------------------------------------------------------------------

class Report(BaseModel):
    ticker: str
    company_name: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    as_of_price: float | None = None
    price_change_pct: float | None = None

    # Per-horizon results
    short_term: HorizonScore | None = None
    medium_term: HorizonScore | None = None
    long_term: HorizonScore | None = None

    # News
    news: list[NewsItem] = []
    fundamentals: FundamentalsSnapshot | None = None

    # AI analysis (markdown)
    ai_summary: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_language: str | None = None

    # Metadata
    risks: list[str] = []
    caveats: list[str] = []
    data_sources: dict[str, Any] = Field(default_factory=dict)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)

    # Chart data (OHLCV for frontend)
    chart_data: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Progress callback type
# ---------------------------------------------------------------------------

class ProgressUpdate(BaseModel):
    step: str
    progress: int  # 0..100
    message: str
