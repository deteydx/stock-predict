"""Macro indicators derived from FRED economic data."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DateOffset


def _value_at_offset(series: pd.Series, months: int) -> float | None:
    """Look up the value closest to N months before the last data point.

    Uses the date index instead of positional indexing so the result is
    correct regardless of data frequency or missing observations.
    """
    if series.empty or not isinstance(series.index, pd.DatetimeIndex):
        # Fall back to positional if no datetime index
        idx = -months if len(series) >= months else 0
        return float(series.iloc[idx])
    target = series.index[-1] - DateOffset(months=months)
    loc = series.index.get_indexer([target], method="nearest")[0]
    if loc < 0:
        return None
    return float(series.iloc[loc])


def yield_curve_state(t10y2y: pd.Series) -> int:
    """Score yield curve: inverted = bearish, steep = bullish.

    Args:
        t10y2y: 10Y-2Y Treasury spread series

    Returns:
        Score in [-2, +2]
    """
    if t10y2y.empty:
        return 0
    current = t10y2y.iloc[-1]
    if current < -0.5:
        return -2  # Deeply inverted → recession signal
    if current < 0:
        return -1  # Inverted
    if current < 0.5:
        return 0   # Flat
    if current < 1.5:
        return 1   # Normal
    return 2        # Steep → expansion signal


def fed_cycle_state(fed_funds: pd.Series) -> int:
    """Score Fed cycle: cutting = bullish, hiking = bearish.

    Uses 6-month rate of change (date-based lookback).
    """
    if len(fed_funds) < 2:
        return 0
    current = float(fed_funds.iloc[-1])
    past = _value_at_offset(fed_funds, months=6)
    if past is None:
        return 0
    change = current - past

    if change < -0.75:
        return 2   # Aggressive cutting
    if change < -0.25:
        return 1   # Cutting
    if change < 0.25:
        return 0   # Pausing
    if change < 0.75:
        return -1  # Hiking
    return -2       # Aggressive hiking


def cpi_trend_state(cpi: pd.Series) -> int:
    """Score CPI trend: falling inflation = bullish, rising = bearish.

    Computes YoY CPI change and its 3-month trend (date-based lookback).
    """
    if len(cpi) < 13:
        return 0

    # YoY inflation rate
    yoy = cpi.pct_change(periods=12) * 100
    current_yoy = yoy.iloc[-1]

    # 3-month trend using date-based lookback
    past_yoy = _value_at_offset(yoy, months=3)
    trend = (current_yoy - past_yoy) if past_yoy is not None else 0

    # Score based on level and direction
    if current_yoy < 2 and trend <= 0:
        return 2   # Low and falling
    if current_yoy < 3 and trend <= 0:
        return 1   # Moderate and falling
    if current_yoy < 4:
        return 0   # Moderate
    if current_yoy < 5 or trend > 0.5:
        return -1  # Elevated or rising
    return -2       # High and rising


def unemployment_state(unrate: pd.Series) -> int:
    """Score unemployment: low and falling = bullish (date-based lookback)."""
    if len(unrate) < 2:
        return 0
    current = float(unrate.iloc[-1])
    past = _value_at_offset(unrate, months=6)
    if past is None:
        return 0
    change = current - past

    if current < 4 and change <= 0:
        return 1   # Low and stable/falling
    if current < 5 and change < 0.5:
        return 0   # Normal
    if change > 1:
        return -2  # Rising sharply
    if current > 6:
        return -1  # Elevated
    return 0


def macro_summary(macro_data: dict[str, pd.Series]) -> dict[str, int]:
    """Compute all macro scores from FRED data.

    Args:
        macro_data: dict from FREDClient.macro_snapshot()

    Returns:
        dict of {indicator_name: score}
    """
    scores = {}

    if "yield_curve" in macro_data:
        scores["yield_curve"] = yield_curve_state(macro_data["yield_curve"])

    if "fed_funds" in macro_data:
        scores["fed_cycle"] = fed_cycle_state(macro_data["fed_funds"])

    if "cpi" in macro_data:
        scores["cpi_trend"] = cpi_trend_state(macro_data["cpi"])

    if "unemployment" in macro_data:
        scores["unemployment"] = unemployment_state(macro_data["unemployment"])

    return scores
