"""Base class for horizon analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd

from stockpredict.types import Horizon, NewsItem, Signal


@dataclass
class AnalysisContext:
    """All data available to horizon analyzers."""

    ticker: str
    bars: pd.DataFrame               # OHLCV daily bars (index=date)
    fundamentals: dict | None = None  # From yfinance
    macro: dict[str, pd.Series] | None = None  # From FRED
    news: list[NewsItem] | None = None
    benchmark_bars: pd.DataFrame | None = None  # SPY bars for relative strength
    sector_etf_bars: pd.DataFrame | None = None  # Sector ETF bars for trend
    weights: dict[str, float] | None = None     # Signal weights from config


class HorizonAnalyzer(ABC):
    """Abstract base for per-horizon signal analyzers."""

    @property
    @abstractmethod
    def horizon(self) -> Horizon:
        ...

    @abstractmethod
    def analyze(self, ctx: AnalysisContext) -> list[Signal]:
        """Compute all signals for this horizon.

        Must tolerate missing data (None fields in ctx) — skip signals
        that can't be computed and return what's available.
        """
        ...
