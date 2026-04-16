"""Options-implied indicators.

All functions are pure and accept a ``RawOptionsChain`` (dict keyed by ISO
expiry date with ``{spot, dte, calls, puts}`` entries) plus any auxiliary data.
They return ``OptionsMetric`` / ``ImpliedRange`` / ``OIStrike`` objects defined
in ``stockpredict.types``.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from stockpredict.types import (
    ImpliedRange,
    OIStrike,
    OptionsMetric,
    OptionsOutlook,
)

RawOptionsChain = dict[str, dict[str, Any]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mid(row: pd.Series) -> float | None:
    bid = row.get("bid")
    ask = row.get("ask")
    last = row.get("last")
    if bid is not None and ask is not None and bid == bid and ask == ask and bid > 0 and ask > 0:
        return float((bid + ask) / 2)
    if last is not None and last == last and last > 0:
        return float(last)
    return None


def _nearest_atm(df: pd.DataFrame, spot: float) -> pd.Series | None:
    if df is None or df.empty:
        return None
    idx = (df["strike"] - spot).abs().idxmin()
    return df.loc[idx]


def _weighted_mean(values: list[tuple[float, float]]) -> float | None:
    """values: list of (value, weight). Returns weighted mean, or None."""
    num = 0.0
    den = 0.0
    for v, w in values:
        if v is None or v != v or w is None or w <= 0:
            continue
        num += v * w
        den += w
    return (num / den) if den > 0 else None


# ---------------------------------------------------------------------------
# 1. Implied move / expected range per expiry
# ---------------------------------------------------------------------------

def implied_ranges(chain: RawOptionsChain) -> list[ImpliedRange]:
    """Compute expected 1σ / 2σ price range for each expiry.

    Prefers the ATM straddle price (``(atm_call_mid + atm_put_mid)/spot``) which
    embeds market-implied move directly. Falls back to
    ``spot * IV * sqrt(DTE/365)`` when mids are missing.
    """
    out: list[ImpliedRange] = []
    for expiry, payload in chain.items():
        spot: float = payload["spot"]
        dte: int = payload["dte"]
        calls: pd.DataFrame = payload["calls"]
        puts: pd.DataFrame = payload["puts"]

        atm_call = _nearest_atm(calls, spot)
        atm_put = _nearest_atm(puts, spot)
        if atm_call is None or atm_put is None:
            continue

        # ATM IV = average of call & put IV (when available)
        iv_vals = [v for v in (atm_call.get("iv"), atm_put.get("iv"))
                   if v is not None and v == v and v > 0]
        atm_iv = float(np.mean(iv_vals)) if iv_vals else None

        call_mid = _mid(atm_call)
        put_mid = _mid(atm_put)
        straddle = None
        if call_mid is not None and put_mid is not None:
            straddle = call_mid + put_mid

        expected_move_pct: float | None = None
        if straddle is not None and spot > 0:
            expected_move_pct = straddle / spot
        elif atm_iv is not None and dte > 0:
            expected_move_pct = atm_iv * math.sqrt(dte / 365.0)

        one_sigma = expected_move_pct * spot if expected_move_pct is not None else None
        range_1_low = spot - one_sigma if one_sigma is not None else None
        range_1_high = spot + one_sigma if one_sigma is not None else None
        range_2_low = spot - 2 * one_sigma if one_sigma is not None else None
        range_2_high = spot + 2 * one_sigma if one_sigma is not None else None

        out.append(ImpliedRange(
            expiry=expiry,
            dte=dte,
            atm_iv=atm_iv,
            expected_move_pct=expected_move_pct,
            straddle_price=straddle,
            range_1sigma_low=range_1_low,
            range_1sigma_high=range_1_high,
            range_2sigma_low=range_2_low,
            range_2sigma_high=range_2_high,
        ))
    return out


# ---------------------------------------------------------------------------
# 2. IV Rank proxy (vs trailing realized-vol distribution)
# ---------------------------------------------------------------------------

def iv_rank_vs_hv(atm_iv: float | None, hv_series: pd.Series) -> OptionsMetric:
    """Approximate IV Rank/Percentile using historical volatility as a proxy.

    Real IV Rank requires a trailing IV history (not yet persisted). As a proxy
    we compare current ATM IV to the 52-week distribution of realized (close-to-
    close) volatility. A ratio near 1 means options are priced in line with
    recent realized moves; >1.3 means richly priced; <0.8 cheaply priced.
    """
    if atm_iv is None or hv_series is None or hv_series.empty:
        return OptionsMetric(
            name="iv_rank",
            value=None,
            rationale="当前 ATM IV 或历史波动率不可用，IV Rank 无法估算 / ATM IV or historical volatility unavailable; IV Rank cannot be estimated.",
        )

    hv = hv_series.dropna()
    if hv.empty:
        return OptionsMetric(name="iv_rank", value=None, rationale="HV 序列为空 / HV series empty")

    hv_min, hv_max = float(hv.min()), float(hv.max())
    rank = None
    if hv_max > hv_min:
        rank = (atm_iv - hv_min) / (hv_max - hv_min)
        rank = max(0.0, min(1.0, rank))

    percentile = float((hv < atm_iv).mean())  # fraction of HV observations below current IV
    median_hv = float(hv.median()) if len(hv) else float("nan")
    ratio = atm_iv / median_hv if median_hv > 0 else None

    desc_zh = (
        f"当前 ATM IV={atm_iv:.2%}，相对过去 52 周实现波动率中位数 {median_hv:.2%} 为 {ratio:.2f}×"
        if ratio is not None else f"当前 ATM IV={atm_iv:.2%}"
    )
    desc_zh += f"；IV 分位约 {percentile:.0%}（HV 代理）"
    desc_en = (
        f"ATM IV {atm_iv:.2%} vs 52-wk realized-vol median {median_hv:.2%} → "
        f"{ratio:.2f}× (proxy); percentile ≈ {percentile:.0%}"
        if ratio is not None else f"ATM IV {atm_iv:.2%}, HV-based percentile ≈ {percentile:.0%}"
    )

    return OptionsMetric(
        name="iv_rank",
        value=float(percentile),
        rationale=f"{desc_zh} / {desc_en}",
    )


# ---------------------------------------------------------------------------
# 3. Put / Call ratios
# ---------------------------------------------------------------------------

def put_call_ratio(chain: RawOptionsChain) -> tuple[OptionsMetric, OptionsMetric]:
    """Returns (pcr_volume, pcr_oi) aggregated across the selected expiries."""
    total_call_vol = 0.0
    total_put_vol = 0.0
    total_call_oi = 0
    total_put_oi = 0

    for payload in chain.values():
        calls = payload["calls"]
        puts = payload["puts"]
        if calls is not None and not calls.empty:
            total_call_vol += float(calls.get("volume", pd.Series(dtype=float)).fillna(0).sum())
            total_call_oi += int(calls.get("open_interest", pd.Series(dtype=int)).fillna(0).sum())
        if puts is not None and not puts.empty:
            total_put_vol += float(puts.get("volume", pd.Series(dtype=float)).fillna(0).sum())
            total_put_oi += int(puts.get("open_interest", pd.Series(dtype=int)).fillna(0).sum())

    pcr_vol_val = (total_put_vol / total_call_vol) if total_call_vol > 0 else None
    pcr_oi_val = (total_put_oi / total_call_oi) if total_call_oi > 0 else None

    def _describe(pcr: float | None, kind_zh: str, kind_en: str) -> str:
        if pcr is None:
            return f"{kind_zh} PCR 不可用 / {kind_en} PCR unavailable"
        if pcr > 1.2:
            tone_zh, tone_en = "看跌情绪明显（偏极端，存在反向信号）", "bearish skew (extreme → potential contrarian bullish)"
        elif pcr > 0.9:
            tone_zh, tone_en = "略偏看跌", "mildly bearish"
        elif pcr > 0.6:
            tone_zh, tone_en = "中性偏多", "neutral-to-bullish"
        else:
            tone_zh, tone_en = "看涨情绪明显（偏极端，可能过度乐观）", "bullish skew (possibly over-optimistic)"
        return (
            f"{kind_zh} PCR={pcr:.2f}，{tone_zh} / "
            f"{kind_en} PCR={pcr:.2f}, {tone_en}"
        )

    return (
        OptionsMetric(
            name="pcr_volume",
            value=pcr_vol_val,
            rationale=_describe(pcr_vol_val, "成交量", "Volume"),
        ),
        OptionsMetric(
            name="pcr_oi",
            value=pcr_oi_val,
            rationale=_describe(pcr_oi_val, "未平仓合约", "Open-interest"),
        ),
    )


# ---------------------------------------------------------------------------
# 4. IV Skew (25-delta proxy)
# ---------------------------------------------------------------------------

def iv_skew(chain: RawOptionsChain) -> OptionsMetric:
    """25Δ put IV − 25Δ call IV, using the nearest-term expiry.

    When Greeks are present (IBKR path) we pick the contract whose |delta| is
    closest to 0.25. Otherwise we approximate with the OTM contract nearest
    ±5% from spot.
    """
    if not chain:
        return OptionsMetric(name="iv_skew", value=None, rationale="无期权数据 / no options data")

    # Use the nearest expiry (smallest DTE > 0)
    nearest = min(chain.items(), key=lambda kv: kv[1]["dte"] if kv[1]["dte"] > 0 else 9999)
    payload = nearest[1]
    spot: float = payload["spot"]
    calls: pd.DataFrame = payload["calls"]
    puts: pd.DataFrame = payload["puts"]

    def _pick_delta(df: pd.DataFrame, target: float) -> pd.Series | None:
        if df is None or df.empty or "delta" not in df.columns:
            return None
        sub = df[df["delta"].notna()]
        if sub.empty:
            return None
        idx = (sub["delta"].astype(float).abs() - abs(target)).abs().idxmin()
        return sub.loc[idx]

    def _pick_otm_by_strike(df: pd.DataFrame, target_strike: float) -> pd.Series | None:
        if df is None or df.empty:
            return None
        idx = (df["strike"] - target_strike).abs().idxmin()
        return df.loc[idx]

    put_row = _pick_delta(puts, -0.25)
    if put_row is None:
        put_row = _pick_otm_by_strike(puts, spot * 0.95)
    call_row = _pick_delta(calls, 0.25)
    if call_row is None:
        call_row = _pick_otm_by_strike(calls, spot * 1.05)

    if put_row is None or call_row is None:
        return OptionsMetric(name="iv_skew", value=None, rationale="缺少合适的 OTM 合约 / no suitable OTM contracts")

    put_iv = put_row.get("iv")
    call_iv = call_row.get("iv")
    if put_iv is None or call_iv is None or put_iv != put_iv or call_iv != call_iv:
        return OptionsMetric(name="iv_skew", value=None, rationale="OTM 合约缺少 IV / OTM contracts missing IV")

    skew = float(put_iv) - float(call_iv)
    tone_zh = "下行保护需求偏强（恐慌）" if skew > 0.04 else (
        "下行保护需求温和" if skew > 0.0 else "看涨倾斜（上行追买）"
    )
    tone_en = "downside-protection demand elevated (fear)" if skew > 0.04 else (
        "mild downside bias" if skew > 0.0 else "call-skewed (upside chase)"
    )
    rationale = (
        f"25Δ Put IV={put_iv:.2%}，25Δ Call IV={call_iv:.2%}，skew={skew:+.2%}，{tone_zh} / "
        f"25Δ put IV {put_iv:.2%} − call IV {call_iv:.2%} = {skew:+.2%} → {tone_en}"
    )
    return OptionsMetric(name="iv_skew", value=skew, rationale=rationale)


# ---------------------------------------------------------------------------
# 5. Max Pain
# ---------------------------------------------------------------------------

def max_pain(chain: RawOptionsChain) -> OptionsMetric:
    """Compute max-pain strike across the selected expiries (aggregated).

    Max pain is the strike K that minimises
        Σ_K' [max(K' - K, 0) * putOI(K') + max(K - K', 0) * callOI(K')]
    i.e. the strike at which option holders collectively lose the most at expiry.
    """
    call_oi_by_strike: dict[float, int] = {}
    put_oi_by_strike: dict[float, int] = {}
    spot: float | None = None

    for payload in chain.values():
        spot = payload["spot"] if spot is None else spot
        for _, row in payload["calls"].iterrows():
            k = float(row["strike"])
            call_oi_by_strike[k] = call_oi_by_strike.get(k, 0) + int(row.get("open_interest") or 0)
        for _, row in payload["puts"].iterrows():
            k = float(row["strike"])
            put_oi_by_strike[k] = put_oi_by_strike.get(k, 0) + int(row.get("open_interest") or 0)

    strikes = sorted(set(call_oi_by_strike) | set(put_oi_by_strike))
    if not strikes or spot is None:
        return OptionsMetric(name="max_pain", value=None, rationale="无 OI 数据 / no open-interest data")

    best_strike: float | None = None
    best_pain = math.inf
    for k in strikes:
        pain = 0.0
        for k2 in strikes:
            call_oi = call_oi_by_strike.get(k2, 0)
            put_oi = put_oi_by_strike.get(k2, 0)
            # If settle = k, calls with strike k2 < k are ITM (k - k2), puts with k2 > k ITM (k2 - k)
            pain += max(k - k2, 0) * call_oi
            pain += max(k2 - k, 0) * put_oi
        if pain < best_pain:
            best_pain = pain
            best_strike = k

    if best_strike is None:
        return OptionsMetric(name="max_pain", value=None, rationale="无法计算 / cannot compute")

    distance = (best_strike - spot) / spot if spot > 0 else 0.0
    direction_zh = "低于现价，期权市场隐含下行引力" if distance < 0 else "高于现价，期权市场隐含上行引力"
    direction_en = "below spot — option market implies downward drift" if distance < 0 else "above spot — implies upward drift"
    rationale = (
        f"Max Pain={best_strike:.2f}，距现价 {distance:+.2%}，{direction_zh} / "
        f"Max Pain {best_strike:.2f}, {distance:+.2%} from spot, {direction_en}"
    )
    return OptionsMetric(name="max_pain", value=float(best_strike), rationale=rationale)


# ---------------------------------------------------------------------------
# 6. OI by strike → support / resistance
# ---------------------------------------------------------------------------

def oi_profile(
    chain: RawOptionsChain,
    top_n: int = 3,
    strike_window_pct: float = 0.10,
) -> tuple[list[OIStrike], list[OIStrike]]:
    """Aggregate OI by strike within ±window and return top-N support/resistance.

    High put OI below spot acts as support; high call OI above spot acts as
    resistance (dealers hedge around these strikes).
    """
    call_oi: dict[float, int] = {}
    put_oi: dict[float, int] = {}
    spot: float | None = None

    for payload in chain.values():
        spot = payload["spot"] if spot is None else spot
        for _, row in payload["calls"].iterrows():
            k = float(row["strike"])
            call_oi[k] = call_oi.get(k, 0) + int(row.get("open_interest") or 0)
        for _, row in payload["puts"].iterrows():
            k = float(row["strike"])
            put_oi[k] = put_oi.get(k, 0) + int(row.get("open_interest") or 0)

    if spot is None:
        return [], []

    low = spot * (1 - strike_window_pct)
    high = spot * (1 + strike_window_pct)

    def _strike(k: float, c: int, p: int) -> OIStrike:
        return OIStrike(
            strike=k,
            call_oi=c,
            put_oi=p,
            distance_pct=(k - spot) / spot if spot > 0 else 0.0,
        )

    support_candidates = [
        _strike(k, call_oi.get(k, 0), put_oi.get(k, 0))
        for k in set(put_oi) | set(call_oi)
        if low <= k <= spot
    ]
    resistance_candidates = [
        _strike(k, call_oi.get(k, 0), put_oi.get(k, 0))
        for k in set(put_oi) | set(call_oi)
        if spot <= k <= high
    ]

    support = sorted(support_candidates, key=lambda s: s.put_oi, reverse=True)[:top_n]
    resistance = sorted(resistance_candidates, key=lambda s: s.call_oi, reverse=True)[:top_n]

    return support, resistance


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def compute_options_outlook(
    chain: RawOptionsChain,
    hv_series: pd.Series,
    data_source: str = "",
) -> OptionsOutlook | None:
    """Compose an ``OptionsOutlook`` from a raw chain + historical vol series."""
    if not chain:
        return None

    spot: float = next(iter(chain.values()))["spot"]
    ranges = implied_ranges(chain)

    # Pick nearest-expiry ATM IV for rank proxy
    atm_iv = None
    for r in ranges:
        if r.atm_iv is not None:
            atm_iv = r.atm_iv
            break

    iv_rank_metric = iv_rank_vs_hv(atm_iv, hv_series)
    pcr_vol, pcr_oi = put_call_ratio(chain)
    skew = iv_skew(chain)
    mp = max_pain(chain)
    support, resistance = oi_profile(chain)

    caveats: list[str] = []
    if data_source == "yfinance":
        caveats.append("期权数据来自 yfinance（约 15 分钟延迟，无原生 Greeks） / Options data via yfinance (~15-min delay, no native Greeks)")
    caveats.append("IV Rank 使用 52 周实现波动率作代理，非真实 IV 历史 / IV Rank uses realized-vol proxy, not a true IV history")

    # Short natural-language summary
    summary_parts = []
    if ranges:
        r0 = ranges[0]
        if r0.expected_move_pct is not None and r0.range_1sigma_low is not None:
            summary_parts.append(
                f"最近到期({r0.expiry}, {r0.dte}DTE) 隐含 ±{r0.expected_move_pct:.1%}"
                f" → 1σ 区间 [{r0.range_1sigma_low:.2f}, {r0.range_1sigma_high:.2f}]"
            )
    if mp.value is not None:
        summary_parts.append(f"Max Pain ≈ {mp.value:.2f}")
    if pcr_vol.value is not None:
        summary_parts.append(f"成交量 PCR={pcr_vol.value:.2f}")

    summary = "；".join(summary_parts) if summary_parts else ""

    return OptionsOutlook(
        spot=spot,
        data_source=data_source,
        implied_ranges=ranges,
        iv_rank=iv_rank_metric,
        pcr_volume=pcr_vol,
        pcr_oi=pcr_oi,
        iv_skew=skew,
        max_pain=mp,
        oi_support=support,
        oi_resistance=resistance,
        summary=summary,
        caveats=caveats,
    )


def realized_vol_series(close: pd.Series, window: int = 20) -> pd.Series:
    """Rolling annualised realized (close-to-close) volatility."""
    if close is None or close.empty:
        return pd.Series(dtype=float)
    log_ret = np.log(close / close.shift(1))
    return (log_ret.rolling(window).std() * math.sqrt(252)).dropna()
