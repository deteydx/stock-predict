"""Medium-term (1–6 months) horizon analyzer."""

from __future__ import annotations

import pandas as pd

from stockpredict.analysis.base import AnalysisContext, HorizonAnalyzer
from stockpredict.indicators import technical as ta
from stockpredict.types import Horizon, Signal


class MediumTermAnalyzer(HorizonAnalyzer):
    @property
    def horizon(self) -> Horizon:
        return Horizon.MEDIUM

    def analyze(self, ctx: AnalysisContext) -> list[Signal]:
        signals: list[Signal] = []
        close = ctx.bars["close"] if "close" in ctx.bars.columns else None
        weights = ctx.weights or {}

        if close is None or len(close) < 60:
            return signals

        # 1. MA50 vs MA200 (Golden/Death Cross)
        if len(close) >= 200:
            score = ta.ma_cross_signal(close, 50, 200)
            ma50 = ta.sma(close, 50).iloc[-1]
            ma200 = ta.sma(close, 200).iloc[-1]
            signals.append(Signal(
                name="ma50_ma200", value=float(score), score=score,
                weight=weights.get("ma50_ma200", 1.5),
                rationale=f"MA50={ma50:.2f} vs MA200={ma200:.2f}",
            ))

        # 2. Price vs MA200
        if len(close) >= 200:
            ma200 = ta.sma(close, 200).iloc[-1]
            if ma200 > 0:
                dist = (close.iloc[-1] - ma200) / ma200
                if dist > 0.10:
                    s = 2
                elif dist > 0:
                    s = 1
                elif dist > -0.05:
                    s = 0
                elif dist > -0.10:
                    s = -1
                else:
                    s = -2
                signals.append(Signal(
                    name="price_vs_ma200", value=float(dist), score=s,
                    weight=weights.get("price_vs_ma200", 1.2),
                    rationale=f"Price {dist:+.1%} from MA200",
                ))

        # 3. 52-Week Position
        pos = ta.week52_position(close, 252)
        if pos is not None:
            if pos < 0.2:
                s = 2  # Near 52w low — potential value
            elif pos < 0.4:
                s = 1
            elif pos < 0.6:
                s = 0
            elif pos < 0.8:
                s = -1
            else:
                s = -2  # Near 52w high
            signals.append(Signal(
                name="week52_position", value=pos, score=s,
                weight=weights.get("week52_position", 1.0),
                rationale=f"52-week position: {pos:.0%}",
            ))

        # 4. Relative Strength vs SPY (average of 3m and 6m)
        if ctx.benchmark_bars is not None and "close" in ctx.benchmark_bars.columns:
            spy_close = ctx.benchmark_bars["close"]
            rs_values = {}
            for period, name in [(63, "3m"), (126, "6m")]:
                rs = ta.relative_strength(close, spy_close, period)
                if rs is not None:
                    rs_values[name] = rs
            if rs_values:
                avg_rs = sum(rs_values.values()) / len(rs_values)
                if avg_rs > 0.10:
                    s = 2
                elif avg_rs > 0.03:
                    s = 1
                elif avg_rs > -0.03:
                    s = 0
                elif avg_rs > -0.10:
                    s = -1
                else:
                    s = -2
                detail = ", ".join(f"{k}: {v:+.1%}" for k, v in rs_values.items())
                signals.append(Signal(
                    name="relative_strength_spy",
                    value=avg_rs, score=s,
                    weight=weights.get("relative_strength_spy", 1.3),
                    rationale=f"Relative strength vs SPY ({detail})",
                ))

        # 5. EPS Growth Trend (from yfinance fundamentals)
        if ctx.fundamentals and "info" in ctx.fundamentals:
            info = ctx.fundamentals["info"]
            eg = info.get("earnings_growth")
            if eg is not None:
                if eg > 0.25:
                    s = 2
                elif eg > 0.10:
                    s = 1
                elif eg > 0:
                    s = 0
                elif eg > -0.10:
                    s = -1
                else:
                    s = -2
                signals.append(Signal(
                    name="eps_growth_trend", value=eg, score=s,
                    weight=weights.get("eps_growth_trend", 1.5),
                    rationale=f"Earnings growth: {eg:.1%}",
                ))

            # 6. Revenue Growth
            rg = info.get("revenue_growth")
            if rg is not None:
                if rg > 0.20:
                    s = 2
                elif rg > 0.08:
                    s = 1
                elif rg > 0:
                    s = 0
                elif rg > -0.05:
                    s = -1
                else:
                    s = -2
                signals.append(Signal(
                    name="revenue_growth", value=rg, score=s,
                    weight=weights.get("revenue_growth", 1.2),
                    rationale=f"Revenue growth: {rg:.1%}",
                ))

        # 7. Earnings Proximity
        if ctx.fundamentals and "earnings_dates" in ctx.fundamentals:
            from datetime import datetime, date
            earnings_dates = ctx.fundamentals["earnings_dates"]
            today = date.today()
            # Find the nearest future earnings date
            future_dates = []
            if isinstance(earnings_dates, pd.DataFrame):
                # DataFrame with datetime index
                future_dates = [
                    d.date() if hasattr(d, "date") else d
                    for d in earnings_dates.index
                    if (d.date() if hasattr(d, "date") else d) >= today
                ]
            elif isinstance(earnings_dates, (list, tuple)):
                for d in earnings_dates:
                    dt = d.date() if hasattr(d, "date") else d
                    if dt >= today:
                        future_dates.append(dt)
            if future_dates:
                next_earnings = min(future_dates)
                days_until = (next_earnings - today).days
                if days_until <= 7:
                    s = 0   # High uncertainty
                    rat = f"Earnings in {days_until}d — high uncertainty"
                elif days_until <= 30:
                    s = -1  # Volatility expansion risk
                    rat = f"Earnings in {days_until}d — vol expansion risk"
                else:
                    s = 1   # Safe to trade on technicals
                    rat = f"Earnings in {days_until}d — low near-term event risk"
                signals.append(Signal(
                    name="earnings_proximity", value=float(days_until), score=s,
                    weight=weights.get("earnings_proximity", 0.5),
                    rationale=rat,
                ))

        # 8. Volatility Regime Shift
        if len(close) >= 60:
            high = ctx.bars.get("high", close)
            low = ctx.bars.get("low", close)
            atr_val = ta.atr(high, low, close, 14)
            if len(atr_val) >= 60:
                recent_atr = float(atr_val.iloc[-5:].mean())
                prev_atr = float(atr_val.iloc[-60:-30].mean())
                if prev_atr > 0:
                    change = (recent_atr - prev_atr) / prev_atr
                    if change > 0.5:
                        s = -1  # Volatility expanding
                        rat = f"Volatility expanding {change:+.0%} from 2-month avg"
                    elif change < -0.3:
                        s = 1   # Volatility contracting
                        rat = f"Volatility contracting {change:+.0%}"
                    else:
                        s = 0
                        rat = f"Volatility stable ({change:+.0%})"
                    signals.append(Signal(
                        name="volatility_regime", value=change, score=s,
                        weight=weights.get("volatility_regime", 0.7),
                        rationale=rat,
                    ))

        # 9. Sector ETF Trend
        if ctx.sector_etf_bars is not None and "close" in ctx.sector_etf_bars.columns:
            etf_close = ctx.sector_etf_bars["close"]
            if len(etf_close) >= 50:
                ma50 = ta.sma(etf_close, 50)
                if ma50.iloc[-1] == ma50.iloc[-1]:
                    etf_price = float(etf_close.iloc[-1])
                    etf_ma50 = float(ma50.iloc[-1])
                    ma50_rising = ma50.iloc[-1] > ma50.iloc[-5] if len(ma50.dropna()) >= 5 else False
                    dist = (etf_price - etf_ma50) / etf_ma50 if etf_ma50 > 0 else 0
                    if dist > 0.03 and ma50_rising:
                        s = 2
                    elif dist > 0 and ma50_rising:
                        s = 1
                    elif dist < -0.03 and not ma50_rising:
                        s = -2
                    elif dist < 0:
                        s = -1
                    else:
                        s = 0
                    signals.append(Signal(
                        name="sector_etf_trend", value=float(dist), score=s,
                        weight=weights.get("sector_etf_trend", 0.8),
                        rationale=f"Sector ETF {dist:+.1%} from MA50, MA50 {'rising' if ma50_rising else 'falling'}",
                    ))

        return signals
