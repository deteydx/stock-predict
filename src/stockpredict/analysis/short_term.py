"""Short-term (days–weeks) horizon analyzer."""

from __future__ import annotations

from stockpredict.analysis.base import AnalysisContext, HorizonAnalyzer
from stockpredict.indicators import technical as ta
from stockpredict.indicators import news as news_ind
from stockpredict.types import Horizon, Signal


class ShortTermAnalyzer(HorizonAnalyzer):
    @property
    def horizon(self) -> Horizon:
        return Horizon.SHORT

    def analyze(self, ctx: AnalysisContext) -> list[Signal]:
        signals: list[Signal] = []
        close = ctx.bars["close"] if "close" in ctx.bars.columns else None
        weights = ctx.weights or {}

        if close is None or len(close) < 30:
            return signals

        high = ctx.bars.get("high", close)
        low = ctx.bars.get("low", close)
        volume = ctx.bars.get("volume")

        # 1. MA5 vs MA20 Cross
        score = ta.ma_cross_signal(close, 5, 20)
        signals.append(Signal(
            name="ma_cross",
            value=float(score),
            score=score,
            weight=weights.get("ma_cross", 1.5),
            rationale=f"MA5/MA20 cross signal: {score}",
        ))

        # 2. RSI(14)
        rsi_val = ta.rsi(close, 14)
        if rsi_val.iloc[-1] == rsi_val.iloc[-1]:  # not NaN
            r = float(rsi_val.iloc[-1])
            if r < 30:
                s = 2
                rat = f"RSI {r:.1f} — oversold (contrarian: mean-reversion buy)"
            elif r < 45:
                s = 1
                rat = f"RSI {r:.1f} — approaching oversold (contrarian)"
            elif r < 55:
                s = 0
                rat = f"RSI {r:.1f} — neutral"
            elif r < 70:
                s = -1
                rat = f"RSI {r:.1f} — approaching overbought (contrarian)"
            else:
                s = -2
                rat = f"RSI {r:.1f} — overbought (contrarian: mean-reversion sell)"
            signals.append(Signal(
                name="rsi", value=r, score=s,
                weight=weights.get("rsi", 1.2), rationale=rat,
            ))

        # 3. MACD Histogram
        macd_data = ta.macd(close)
        hist = macd_data["histogram"]
        if hist.iloc[-1] == hist.iloc[-1]:
            h = float(hist.iloc[-1])
            h_prev = float(hist.iloc[-2]) if len(hist) >= 2 else h
            rising = h > h_prev
            if h > 0 and rising:
                s = 2
            elif h > 0:
                s = 1
            elif h < 0 and not rising:
                s = -2
            elif h < 0:
                s = -1
            else:
                s = 0
            signals.append(Signal(
                name="macd", value=h, score=s,
                weight=weights.get("macd", 1.3),
                rationale=f"MACD histogram {h:.4f}, {'rising' if rising else 'falling'}",
            ))

        # 4. Bollinger %B
        bb = ta.bollinger_bands(close, 20, 2.0)
        pct_b = bb["pct_b"]
        if pct_b.iloc[-1] == pct_b.iloc[-1]:
            b = float(pct_b.iloc[-1])
            if b < 0:
                s = 2
            elif b < 0.2:
                s = 1
            elif b < 0.8:
                s = 0
            elif b < 1.0:
                s = -1
            else:
                s = -2
            signals.append(Signal(
                name="bollinger", value=b, score=s,
                weight=weights.get("bollinger", 1.0),
                rationale=f"Bollinger %B = {b:.2f}",
            ))

        # 5. ATR Regime (scored by ATR relative to its rolling median)
        if high is not None and low is not None:
            atr_val = ta.atr(high, low, close, 14)
            if atr_val.iloc[-1] == atr_val.iloc[-1]:
                a = float(atr_val.iloc[-1])
                atr_median = float(atr_val.iloc[-252:].median()) if len(atr_val) >= 252 else a
                ratio = a / atr_median if atr_median > 0 else 1.0
                if ratio > 1.5:
                    s = -1
                    rat = f"ATR {a:.2f} — high volatility ({ratio:.2f}x median)"
                elif ratio < 0.7:
                    s = 1
                    rat = f"ATR {a:.2f} — low volatility ({ratio:.2f}x median)"
                else:
                    s = 0
                    rat = f"ATR {a:.2f} — normal volatility ({ratio:.2f}x median)"
                signals.append(Signal(
                    name="atr_regime", value=ratio, score=s,
                    weight=weights.get("atr_regime", 0.8), rationale=rat,
                ))

        # 6. OBV Trend (multi-window divergence confirmation)
        if volume is not None and len(volume) >= 35:
            slope = ta.obv_slope(close, volume, 20)
            if slope.iloc[-1] == slope.iloc[-1]:
                sl = float(slope.iloc[-1])
                price_up = close.iloc[-1] > close.iloc[-20]

                # Check 3 sample points for divergence confirmation
                divergent_count = 0
                for offset in [0, 5, 10]:
                    idx = -1 - offset
                    price_idx = -20 - offset
                    if abs(idx) <= len(slope) and abs(price_idx) <= len(close):
                        s_val = float(slope.iloc[idx])
                        p_up = close.iloc[idx] > close.iloc[price_idx]
                        if (s_val > 0 and not p_up) or (s_val < 0 and p_up):
                            divergent_count += 1

                if sl > 0 and price_up:
                    s = 1   # Bullish confirmation
                    rat = f"OBV slope {sl:.0f}, price up — confirmed"
                elif sl < 0 and not price_up:
                    s = -1  # Bearish confirmation
                    rat = f"OBV slope {sl:.0f}, price down — confirmed"
                elif sl > 0 and not price_up:
                    # Positive divergence
                    s = 2 if divergent_count >= 3 else 1
                    strength = "confirmed" if divergent_count >= 3 else "weak"
                    rat = f"OBV slope {sl:.0f}, price down — {strength} positive divergence ({divergent_count}/3)"
                elif sl < 0 and price_up:
                    # Negative divergence
                    s = -2 if divergent_count >= 3 else -1
                    strength = "confirmed" if divergent_count >= 3 else "weak"
                    rat = f"OBV slope {sl:.0f}, price up — {strength} negative divergence ({divergent_count}/3)"
                else:
                    s = 0
                    rat = f"OBV slope {sl:.0f}, neutral"

                signals.append(Signal(
                    name="obv_trend", value=sl, score=s,
                    weight=weights.get("obv_trend", 1.0),
                    rationale=rat,
                ))

        # 7. Volume Spike
        if volume is not None and len(volume) >= 20:
            spike = ta.volume_spike(volume, 20)
            if spike.iloc[-1] == spike.iloc[-1]:
                v = float(spike.iloc[-1])
                price_up = close.iloc[-1] > close.iloc[-2]
                if v > 2.0 and price_up:
                    s = 1
                elif v > 2.0 and not price_up:
                    s = -1
                else:
                    s = 0
                signals.append(Signal(
                    name="volume_spike", value=v, score=s,
                    weight=weights.get("volume_spike", 0.8),
                    rationale=f"Volume {v:.1f}x average, price {'up' if price_up else 'down'}",
                ))

        # 8. 5-Day Momentum Percentile
        mom_pct = ta.momentum_percentile(close, 5, 252)
        if mom_pct is not None:
            if mom_pct > 0.8:
                s = 1
            elif mom_pct < 0.2:
                s = -1
            else:
                s = 0
            signals.append(Signal(
                name="momentum_5d", value=mom_pct, score=s,
                weight=weights.get("momentum_5d", 0.7),
                rationale=f"5d momentum at {mom_pct:.0%} percentile",
            ))

        # 9. Pivot Point Support/Resistance
        if high is not None and low is not None:
            pivots = ta.pivot_points(high, low, close)
            if pivots is not None:
                price = float(close.iloc[-1])
                atr_val = ta.atr(high, low, close, 14)
                threshold = float(atr_val.iloc[-1]) if atr_val.iloc[-1] == atr_val.iloc[-1] else price * 0.02
                if price <= pivots["s2"] + threshold:
                    s = 2
                    rat = f"Price {price:.2f} near S2 {pivots['s2']:.2f} — strong support zone"
                elif price <= pivots["s1"] + threshold:
                    s = 1
                    rat = f"Price {price:.2f} near S1 {pivots['s1']:.2f} — support zone"
                elif price >= pivots["r2"] - threshold:
                    s = -2
                    rat = f"Price {price:.2f} near R2 {pivots['r2']:.2f} — strong resistance zone"
                elif price >= pivots["r1"] - threshold:
                    s = -1
                    rat = f"Price {price:.2f} near R1 {pivots['r1']:.2f} — resistance zone"
                else:
                    s = 0
                    rat = f"Price {price:.2f} between pivot levels (P={pivots['pivot']:.2f})"
                signals.append(Signal(
                    name="pivot_sr", value=price, score=s,
                    weight=weights.get("pivot_sr", 1.0),
                    rationale=rat,
                ))

        # 10. News Sentiment (24h)
        if ctx.news:
            recent_news_count = news_ind.recent_news_count(ctx.news, hours=24)
            sent = news_ind.sentiment_aggregate(ctx.news, hours=24)
            s = news_ind.sentiment_score(sent)
            signals.append(Signal(
                name="news_sentiment_24h", value=sent, score=s,
                weight=weights.get("news_sentiment_24h", 1.2),
                rationale=(
                    "No news in the last 24h"
                    if recent_news_count == 0
                    else f"24h news sentiment: {sent:.2f} across {recent_news_count} articles"
                ),
            ))

            # 10. News Volume Z-Score (informational only — non-directional, so weight=0)
            zscore = news_ind.news_volume_zscore(ctx.news, window_days=1, baseline_days=30)
            signals.append(Signal(
                name="news_volume_zscore", value=zscore, score=0,
                weight=0.0,
                rationale=f"News volume z-score: {zscore:.1f} (non-directional)" + (
                    " — ELEVATED" if zscore > 2 else ""
                ),
            ))

        return signals
