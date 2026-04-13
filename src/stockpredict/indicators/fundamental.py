"""Fundamental indicators derived from financial statements and valuation ratios."""

from __future__ import annotations

# Sector-relative valuation medians.  Sources: Damodaran, Finviz sector stats.
# Each tuple = (pe_median, pb_median, ev_ebitda_median)
SECTOR_MEDIANS: dict[str, tuple[float, float, float]] = {
    "Technology":          (30.0, 7.0, 20.0),
    "Communication Services": (22.0, 3.5, 14.0),
    "Consumer Cyclical":   (20.0, 4.0, 14.0),
    "Consumer Defensive":  (22.0, 4.5, 15.0),
    "Healthcare":          (25.0, 4.0, 16.0),
    "Financial Services":  (13.0, 1.5,  0.0),  # EV/EBITDA not meaningful
    "Industrials":         (20.0, 4.0, 14.0),
    "Energy":              (12.0, 1.8,  7.0),
    "Basic Materials":     (14.0, 2.0,  9.0),
    "Real Estate":         (35.0, 2.5, 20.0),
    "Utilities":           (18.0, 2.0, 12.0),
}

_DEFAULT_MEDIANS = (20.0, 3.5, 14.0)


def _relative_valuation_score(value: float, sector_median: float) -> int:
    """Score a valuation ratio relative to its sector median.

    ratio = value / median.  <0.6 → +2, 0.6-0.85 → +1, 0.85-1.15 → 0,
    1.15-1.5 → -1, >1.5 → -2.
    """
    if sector_median <= 0:
        return 0
    ratio = value / sector_median
    if ratio < 0.6:
        return 2
    if ratio < 0.85:
        return 1
    if ratio < 1.15:
        return 0
    if ratio < 1.5:
        return -1
    return -2


def pe_score(pe: float, sector: str = "") -> int:
    median = SECTOR_MEDIANS.get(sector, _DEFAULT_MEDIANS)[0]
    return _relative_valuation_score(pe, median)


def pb_score(pb: float, sector: str = "") -> int:
    median = SECTOR_MEDIANS.get(sector, _DEFAULT_MEDIANS)[1]
    return _relative_valuation_score(pb, median)


def ev_ebitda_score(ev_ebitda: float, sector: str = "") -> int:
    median = SECTOR_MEDIANS.get(sector, _DEFAULT_MEDIANS)[2]
    return _relative_valuation_score(ev_ebitda, median)


def peg_score(peg: float | None) -> int:
    """Score PEG ratio: <1 great, 1-2 good, 2-3 fair, >3 expensive."""
    if peg is None:
        return 0
    if peg < 0:
        return -1  # Negative growth
    if peg < 1:
        return 2
    if peg < 2:
        return 1
    if peg < 3:
        return -1
    return -2


def cagr_score(growth_rate: float | None) -> int:
    """Score a CAGR: >15% excellent, 5-15% good, 0-5% fair, <0 bad."""
    if growth_rate is None:
        return 0
    if growth_rate > 0.15:
        return 2
    if growth_rate > 0.05:
        return 1
    if growth_rate > 0:
        return 0
    if growth_rate > -0.05:
        return -1
    return -2


def roe_score(roe: float | None) -> int:
    """Score ROE: >20% excellent, 15-20% good, 10-15% fair, <10% poor."""
    if roe is None:
        return 0
    if roe > 0.20:
        return 2
    if roe > 0.15:
        return 1
    if roe > 0.10:
        return 0
    if roe > 0.05:
        return -1
    return -2


def debt_equity_score(de_ratio: float | None) -> int:
    """Score Debt/Equity: <0.5 great, 0.5-1 good, 1-2 fair, >2 risky."""
    if de_ratio is None:
        return 0
    if de_ratio < 50:     # yfinance returns as percentage
        return 2
    if de_ratio < 100:
        return 1
    if de_ratio < 200:
        return -1
    return -2

