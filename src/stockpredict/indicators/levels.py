"""Professional multi-source support / resistance level detection.

Combines swing pivots (volume-weighted), moving averages, Fibonacci
retracements, and a day-bar volume profile (POC / Value Area / HVN)
into a single set of fused support and resistance levels. Candidates
are weighted by source quality, volume at formation, and time decay,
then clustered with an ATR-based radius.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from stockpredict.indicators.technical import atr, sma
from stockpredict.types import Level, LevelSource


@dataclass
class _Candidate:
    price: float
    kind: str            # "support" | "resistance"
    weight: float
    source_kind: str
    detail: str


# ---------------------------------------------------------------------------
# Swing (fractal) pivots, volume-weighted
# ---------------------------------------------------------------------------

def _swing_candidates(
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series | None,
    left: int = 3,
    right: int = 3,
    half_life_days: float = 60.0,
    max_age_days: int = 250,
) -> tuple[list[_Candidate], list[_Candidate]]:
    lows: list[_Candidate] = []
    highs: list[_Candidate] = []
    n = len(high)
    if n < left + right + 1:
        return lows, highs

    h = high.to_numpy(dtype=float)
    l = low.to_numpy(dtype=float)
    v = volume.to_numpy(dtype=float) if volume is not None else np.ones(n)
    idx = high.index

    baseline_vol = float(np.nanmean(v[-120:])) if n >= 20 else float(np.nanmean(v))
    if not math.isfinite(baseline_vol) or baseline_vol <= 0:
        baseline_vol = 1.0

    decay_k = math.log(2) / max(half_life_days, 1.0)

    start = max(left, n - right - max_age_days)
    for i in range(start, n - right):
        age = n - 1 - i
        decay = math.exp(-decay_k * age)

        seg_low = l[i - left : i + right + 1]
        if l[i] == seg_low.min():
            vol_mult = min(3.0, v[i] / baseline_vol) if baseline_vol > 0 else 1.0
            lows.append(_Candidate(
                price=float(l[i]),
                kind="support",
                weight=1.5 * decay * vol_mult,
                source_kind="swing_low",
                detail=f"swing low {idx[i].date()} vol×{vol_mult:.2f}",
            ))

        seg_high = h[i - left : i + right + 1]
        if h[i] == seg_high.max():
            vol_mult = min(3.0, v[i] / baseline_vol) if baseline_vol > 0 else 1.0
            highs.append(_Candidate(
                price=float(h[i]),
                kind="resistance",
                weight=1.5 * decay * vol_mult,
                source_kind="swing_high",
                detail=f"swing high {idx[i].date()} vol×{vol_mult:.2f}",
            ))
    return lows, highs


# ---------------------------------------------------------------------------
# Moving averages
# ---------------------------------------------------------------------------

def _ma_candidates(close: pd.Series, current_price: float) -> list[_Candidate]:
    out: list[_Candidate] = []
    for period, weight in ((20, 1.1), (60, 1.4), (120, 1.3)):
        if len(close) < period:
            continue
        ma_val = float(sma(close, period).iloc[-1])
        if not math.isfinite(ma_val):
            continue
        kind = "support" if ma_val <= current_price else "resistance"
        out.append(_Candidate(
            price=ma_val,
            kind=kind,
            weight=weight,
            source_kind=f"ma{period}",
            detail=f"MA{period}",
        ))
    return out


# ---------------------------------------------------------------------------
# Fibonacci retracements
# ---------------------------------------------------------------------------

def _fib_candidates(close: pd.Series, lookback: int = 180) -> list[_Candidate]:
    n = min(lookback, len(close))
    if n < 20:
        return []
    window = close.iloc[-n:]
    hi = float(window.max())
    lo = float(window.min())
    if hi <= lo:
        return []
    hi_idx = int(window.values.argmax())
    lo_idx = int(window.values.argmin())
    rng = hi - lo
    out: list[_Candidate] = []

    if hi_idx > lo_idx:
        # uptrend: retracements from hi are potential support
        for ratio, w in ((0.382, 0.9), (0.5, 1.0), (0.618, 1.1)):
            out.append(_Candidate(
                price=hi - rng * ratio,
                kind="support",
                weight=w,
                source_kind=f"fib_{ratio:.3f}",
                detail=f"fib {ratio:.3f} retrace of {lo:.2f}→{hi:.2f}",
            ))
    else:
        # downtrend: bounces from lo are potential resistance
        for ratio, w in ((0.382, 0.9), (0.5, 1.0), (0.618, 1.1)):
            out.append(_Candidate(
                price=lo + rng * ratio,
                kind="resistance",
                weight=w,
                source_kind=f"fib_{ratio:.3f}",
                detail=f"fib {ratio:.3f} bounce of {hi:.2f}→{lo:.2f}",
            ))
    return out


# ---------------------------------------------------------------------------
# Volume profile from daily OHLCV (intra-day volume spread uniformly across
# each bar's [low, high] range)
# ---------------------------------------------------------------------------

def _volume_profile(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series | None,
    lookback: int = 180,
    bins: int = 50,
) -> dict:
    if volume is None:
        return {}
    n = min(lookback, len(close))
    if n < 20:
        return {}
    h = high.iloc[-n:].to_numpy(dtype=float)
    l = low.iloc[-n:].to_numpy(dtype=float)
    v = volume.iloc[-n:].to_numpy(dtype=float)

    p_lo = float(np.nanmin(l))
    p_hi = float(np.nanmax(h))
    if not (math.isfinite(p_lo) and math.isfinite(p_hi)) or p_hi <= p_lo:
        return {}

    edges = np.linspace(p_lo, p_hi, bins + 1)
    bin_vol = np.zeros(bins)
    for i in range(n):
        lo_i, hi_i, vol_i = l[i], h[i], v[i]
        if not math.isfinite(vol_i) or vol_i <= 0 or hi_i <= lo_i:
            continue
        start = int(np.searchsorted(edges, lo_i, side="right") - 1)
        end = int(np.searchsorted(edges, hi_i, side="left"))
        start = max(0, start)
        end = min(bins, max(end, start + 1))
        span = end - start
        bin_vol[start:end] += vol_i / span

    total = float(bin_vol.sum())
    if total <= 0:
        return {}

    centers = (edges[:-1] + edges[1:]) / 2
    poc_idx = int(np.argmax(bin_vol))
    poc_price = float(centers[poc_idx])

    # Value Area = smallest price range around POC that holds 70% of volume
    target = total * 0.70
    lo_i, hi_i = poc_idx, poc_idx
    acc = float(bin_vol[poc_idx])
    while acc < target and (lo_i > 0 or hi_i < bins - 1):
        left_v = float(bin_vol[lo_i - 1]) if lo_i > 0 else -1.0
        right_v = float(bin_vol[hi_i + 1]) if hi_i < bins - 1 else -1.0
        if right_v >= left_v and hi_i < bins - 1:
            hi_i += 1
            acc += float(bin_vol[hi_i])
        elif lo_i > 0:
            lo_i -= 1
            acc += float(bin_vol[lo_i])
        else:
            break
    val = float(centers[lo_i])
    vah = float(centers[hi_i])

    # High Volume Nodes: local maxima >= 1.5× mean bin volume
    mean_v = float(bin_vol.mean())
    hvn: list[tuple[float, float]] = []
    for i in range(1, bins - 1):
        if (
            bin_vol[i] >= 1.5 * mean_v
            and bin_vol[i] >= bin_vol[i - 1]
            and bin_vol[i] >= bin_vol[i + 1]
        ):
            hvn.append((float(centers[i]), float(bin_vol[i] / total)))

    return {"poc": poc_price, "val": val, "vah": vah, "hvn": hvn}


def _profile_candidates(profile: dict, current_price: float) -> list[_Candidate]:
    out: list[_Candidate] = []
    if not profile:
        return out

    poc = profile["poc"]
    out.append(_Candidate(
        price=poc,
        kind="support" if poc <= current_price else "resistance",
        weight=1.6,
        source_kind="poc",
        detail="volume profile POC",
    ))

    val = profile["val"]
    out.append(_Candidate(
        price=val,
        kind="support" if val <= current_price else "resistance",
        weight=1.1,
        source_kind="val",
        detail="value area low",
    ))

    vah = profile["vah"]
    out.append(_Candidate(
        price=vah,
        kind="support" if vah <= current_price else "resistance",
        weight=1.1,
        source_kind="vah",
        detail="value area high",
    ))

    for p, share in profile["hvn"]:
        out.append(_Candidate(
            price=p,
            kind="support" if p <= current_price else "resistance",
            weight=0.8 + 6.0 * share,
            source_kind="hvn",
            detail=f"HVN {share * 100:.1f}% of volume",
        ))
    return out


# ---------------------------------------------------------------------------
# ATR-based 1D clustering
# ---------------------------------------------------------------------------

def _cluster(cands: list[_Candidate], radius: float) -> list[tuple[float, float, list[_Candidate]]]:
    if not cands:
        return []
    ordered = sorted(cands, key=lambda c: c.price)
    clusters: list[list[_Candidate]] = []
    for c in ordered:
        if clusters:
            last = clusters[-1]
            last_w = sum(x.weight for x in last) or 1e-9
            last_center = sum(x.price * x.weight for x in last) / last_w
            if abs(c.price - last_center) <= radius:
                last.append(c)
                continue
        clusters.append([c])

    out: list[tuple[float, float, list[_Candidate]]] = []
    for grp in clusters:
        total_w = sum(c.weight for c in grp)
        if total_w <= 0:
            continue
        center = sum(c.price * c.weight for c in grp) / total_w
        # bonus: more distinct source kinds = stronger confluence
        distinct = len({c.source_kind.split("_")[0] for c in grp})
        confluence_bonus = 1.0 + 0.25 * (distinct - 1)
        out.append((center, total_w * confluence_bonus, grp))
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_levels(
    bars: pd.DataFrame,
    max_support: int = 3,
    max_resistance: int = 3,
) -> list[Level]:
    """Compute fused support/resistance levels from daily OHLCV bars.

    Returns a combined list (supports + resistances), each with a normalized
    strength in [0, 1] and a list of contributing sources.
    """
    if not {"high", "low", "close"}.issubset(bars.columns):
        return []
    if len(bars) < 30:
        return []

    high = bars["high"]
    low = bars["low"]
    close = bars["close"]
    volume = bars["volume"] if "volume" in bars.columns else None
    price = float(close.iloc[-1])
    if not math.isfinite(price) or price <= 0:
        return []

    atr_series = atr(high, low, close, 14)
    last_atr = float(atr_series.iloc[-1])
    if not math.isfinite(last_atr) or last_atr <= 0:
        last_atr = price * 0.02
    radius = max(last_atr * 0.6, price * 0.005)

    lows, highs = _swing_candidates(high, low, volume)
    mas = _ma_candidates(close, price)
    fibs = _fib_candidates(close)
    profile = _volume_profile(high, low, close, volume)
    profile_cands = _profile_candidates(profile, price)

    all_cands = lows + highs + mas + fibs + profile_cands
    supports = [c for c in all_cands if c.kind == "support" and c.price < price]
    resistances = [c for c in all_cands if c.kind == "resistance" and c.price > price]

    sup_clusters = _cluster(supports, radius)
    res_clusters = _cluster(resistances, radius)

    def _build(clusters, kind: str, limit: int) -> list[Level]:
        clusters = sorted(clusters, key=lambda x: x[1], reverse=True)[:limit]
        if not clusters:
            return []
        max_w = max(w for _, w, _ in clusters) or 1.0
        out: list[Level] = []
        for center, w, members in clusters:
            sources = [
                LevelSource(
                    kind=m.source_kind,
                    price=round(m.price, 4),
                    weight=round(m.weight, 4),
                    detail=m.detail,
                )
                for m in sorted(members, key=lambda x: x.weight, reverse=True)
            ]
            out.append(Level(
                price=round(center, 4),
                kind=kind,
                strength=round(w / max_w, 3),
                distance_pct=round((center - price) / price, 4),
                sources=sources,
            ))
        return out

    supports_out = _build(sup_clusters, "support", max_support)
    resistances_out = _build(res_clusters, "resistance", max_resistance)
    # order: supports nearest-to-price first, then resistances nearest-to-price first
    supports_out.sort(key=lambda lv: -lv.price)
    resistances_out.sort(key=lambda lv: lv.price)
    return supports_out + resistances_out
