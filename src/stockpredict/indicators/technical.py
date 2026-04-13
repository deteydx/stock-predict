"""Technical indicators computed from OHLCV price data."""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Moving Averages
# ---------------------------------------------------------------------------

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


# ---------------------------------------------------------------------------
# RSI (Relative Strength Index)
# ---------------------------------------------------------------------------

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, pd.Series]:
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def bollinger_bands(
    close: pd.Series, period: int = 20, std_dev: float = 2.0
) -> dict[str, pd.Series]:
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    bandwidth = upper - lower
    pct_b = (close - lower) / bandwidth.replace(0, np.nan)
    return {"upper": upper, "mid": mid, "lower": lower, "pct_b": pct_b}


# ---------------------------------------------------------------------------
# ATR (Average True Range)
# ---------------------------------------------------------------------------

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period).mean()


# ---------------------------------------------------------------------------
# OBV (On Balance Volume)
# ---------------------------------------------------------------------------

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def obv_slope(close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
    """OBV linear regression slope over the last `period` days."""
    _obv = obv(close, volume)
    slopes = _obv.rolling(window=period, min_periods=period).apply(
        lambda x: np.polyfit(range(len(x)), x, 1)[0], raw=True
    )
    return slopes


# ---------------------------------------------------------------------------
# Volume spike
# ---------------------------------------------------------------------------

def volume_spike(volume: pd.Series, period: int = 20) -> pd.Series:
    """Ratio of current volume to rolling average volume."""
    avg = volume.rolling(window=period, min_periods=period).mean()
    return volume / avg.replace(0, np.nan)


# ---------------------------------------------------------------------------
# 52-Week Position
# ---------------------------------------------------------------------------

def week52_position(close: pd.Series, period: int = 252) -> float | None:
    """Current price position within the 52-week range (0=low, 1=high)."""
    if len(close) < period:
        return None
    window = close.iloc[-period:]
    lo, hi = window.min(), window.max()
    if hi == lo:
        return 0.5
    return float((close.iloc[-1] - lo) / (hi - lo))


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def momentum(close: pd.Series, period: int = 5) -> pd.Series:
    """Simple percentage return over `period` days."""
    return close.pct_change(periods=period)


def momentum_percentile(close: pd.Series, period: int = 5, lookback: int = 252) -> float | None:
    """Current `period`-day momentum's percentile rank over the last `lookback` days."""
    mom = momentum(close, period).dropna()
    if len(mom) < lookback:
        return None
    window = mom.iloc[-lookback:]
    current = mom.iloc[-1]
    return float((window < current).sum() / len(window))


# ---------------------------------------------------------------------------
# Relative Strength vs Benchmark
# ---------------------------------------------------------------------------

def relative_strength(
    stock_close: pd.Series,
    benchmark_close: pd.Series,
    period: int = 63,  # ~3 months
) -> float | None:
    """Stock return vs benchmark return over `period` days."""
    if len(stock_close) < period or len(benchmark_close) < period:
        return None
    stock_ret = stock_close.iloc[-1] / stock_close.iloc[-period] - 1
    bench_ret = benchmark_close.iloc[-1] / benchmark_close.iloc[-period] - 1
    return float(stock_ret - bench_ret)


# ---------------------------------------------------------------------------
# MA Cross Detection
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pivot Points (Floor Method)
# ---------------------------------------------------------------------------

def pivot_points(
    high: pd.Series, low: pd.Series, close: pd.Series,
) -> dict[str, float] | None:
    """Standard floor pivot points from the previous day's OHLC."""
    if len(high) < 2:
        return None
    h, l, c = float(high.iloc[-2]), float(low.iloc[-2]), float(close.iloc[-2])
    p = (h + l + c) / 3
    return {
        "pivot": p,
        "s1": 2 * p - h,
        "s2": p - (h - l),
        "r1": 2 * p - l,
        "r2": p + (h - l),
    }


# ---------------------------------------------------------------------------
# Sector ETF Mapping
# ---------------------------------------------------------------------------

SECTOR_ETFS: dict[str, str] = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
    "Utilities": "XLU",
}


# ---------------------------------------------------------------------------
# MA Cross Detection
# ---------------------------------------------------------------------------

def ma_cross_signal(close: pd.Series, fast_period: int, slow_period: int) -> int:
    """Detect MA cross: +2 cross up, +1 above, -1 below, -2 cross down."""
    fast = sma(close, fast_period)
    slow = sma(close, slow_period)
    if fast.iloc[-1] != fast.iloc[-1] or slow.iloc[-1] != slow.iloc[-1]:
        return 0  # NaN
    diff_now = fast.iloc[-1] - slow.iloc[-1]
    diff_prev = fast.iloc[-2] - slow.iloc[-2] if len(fast.dropna()) >= 2 else diff_now
    if diff_prev <= 0 < diff_now:
        return 2   # cross up
    if diff_prev >= 0 > diff_now:
        return -2  # cross down
    if diff_now > 0:
        return 1   # above
    return -1       # below
