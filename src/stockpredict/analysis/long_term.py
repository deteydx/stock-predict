"""Long-term (1–3+ years) horizon analyzer."""

from __future__ import annotations

from stockpredict.analysis.base import AnalysisContext, HorizonAnalyzer
from stockpredict.indicators import fundamental as fund
from stockpredict.indicators import macro as macro_ind
from stockpredict.indicators import news as news_ind
from stockpredict.types import Horizon, Signal


class LongTermAnalyzer(HorizonAnalyzer):
    @property
    def horizon(self) -> Horizon:
        return Horizon.LONG

    def analyze(self, ctx: AnalysisContext) -> list[Signal]:
        signals: list[Signal] = []
        weights = ctx.weights or {}
        info = {}
        if ctx.fundamentals and "info" in ctx.fundamentals:
            info = ctx.fundamentals["info"]

        # === Valuation Signals (sector-relative) ===

        sector = info.get("sector", "")

        # 1. P/E
        pe = info.get("pe_trailing")
        if pe is not None and pe > 0:
            s = fund.pe_score(pe, sector)
            signals.append(Signal(
                name="pe_percentile", value=pe, score=s,
                weight=weights.get("pe_percentile", 1.3),
                rationale=f"Trailing P/E = {pe:.1f} (sector: {sector or 'unknown'})",
            ))

        # 2. P/B
        pb = info.get("pb")
        if pb is not None and pb > 0:
            s = fund.pb_score(pb, sector)
            signals.append(Signal(
                name="pb_percentile", value=pb, score=s,
                weight=weights.get("pb_percentile", 0.8),
                rationale=f"P/B = {pb:.1f} (sector: {sector or 'unknown'})",
            ))

        # 3. PEG
        peg = info.get("peg")
        if peg is not None:
            s = fund.peg_score(peg)
            signals.append(Signal(
                name="peg", value=peg, score=s,
                weight=weights.get("peg", 1.2),
                rationale=f"PEG = {peg:.2f}",
            ))

        # 4. EV/EBITDA
        ev_ebitda = info.get("ev_ebitda")
        if ev_ebitda is not None and ev_ebitda > 0:
            s = fund.ev_ebitda_score(ev_ebitda, sector)
            signals.append(Signal(
                name="ev_ebitda", value=ev_ebitda, score=s,
                weight=weights.get("ev_ebitda", 1.0),
                rationale=f"EV/EBITDA = {ev_ebitda:.1f} (sector: {sector or 'unknown'})",
            ))

        # === Quality / Growth Signals ===

        # 5. Revenue Growth (single quarter YoY — NOT multi-year CAGR)
        rg = info.get("revenue_growth")
        if rg is not None:
            s = fund.cagr_score(rg)
            signals.append(Signal(
                name="revenue_growth_qoq", value=rg, score=s,
                weight=weights.get("revenue_growth_qoq", 0.8),
                rationale=f"Revenue growth (latest quarter YoY): {rg:.1%}",
            ))

        # 6. Earnings Growth (single quarter YoY — NOT multi-year CAGR)
        eg = info.get("earnings_growth")
        if eg is not None:
            s = fund.cagr_score(eg)
            signals.append(Signal(
                name="earnings_growth_qoq", value=eg, score=s,
                weight=weights.get("earnings_growth_qoq", 0.8),
                rationale=f"Earnings growth (latest quarter YoY): {eg:.1%}",
            ))

        # 7. ROE
        roe = info.get("roe")
        if roe is not None:
            s = fund.roe_score(roe)
            signals.append(Signal(
                name="roe_trend", value=roe, score=s,
                weight=weights.get("roe_trend", 1.2),
                rationale=f"ROE = {roe:.1%}",
            ))

        # 8. ROIC Trend
        income_stmt = ctx.fundamentals.get("income_stmt", {}) if ctx.fundamentals else {}
        balance_sheet = ctx.fundamentals.get("balance_sheet", {}) if ctx.fundamentals else {}
        if income_stmt and balance_sheet:
            # Get the two most recent periods for trend
            bs_cols = sorted(balance_sheet.keys(), reverse=True) if balance_sheet else []
            is_cols = sorted(income_stmt.keys(), reverse=True) if income_stmt else []
            roic_values = []
            for bs_col, is_col in zip(bs_cols[:2], is_cols[:2]):
                net_income = income_stmt[is_col].get("Net Income")
                total_assets = balance_sheet[bs_col].get("Total Assets")
                current_liabilities = balance_sheet[bs_col].get("Current Liabilities")
                if net_income is not None and total_assets and current_liabilities is not None:
                    invested_capital = total_assets - current_liabilities
                    if invested_capital > 0:
                        roic_values.append(net_income / invested_capital)
            if roic_values:
                roic = roic_values[0]
                improving = len(roic_values) >= 2 and roic_values[0] > roic_values[1]
                if roic > 0.15 and improving:
                    s = 2
                elif roic > 0.10:
                    s = 1
                elif roic > 0.05:
                    s = 0
                elif roic > 0:
                    s = -1
                else:
                    s = -2
                trend_str = "improving" if improving else ("declining" if len(roic_values) >= 2 else "single period")
                signals.append(Signal(
                    name="roic_trend", value=roic, score=s,
                    weight=weights.get("roic_trend", 1.0),
                    rationale=f"ROIC = {roic:.1%} ({trend_str})",
                ))

        # 9. Profitability margin
        # Use actual FCF margin if both FCF and revenue are available;
        # otherwise fall back to profit margin with reduced weight.
        fcf = info.get("free_cash_flow")
        income_stmt = ctx.fundamentals.get("income_stmt", {}) if ctx.fundamentals else {}
        total_revenue = None
        if income_stmt:
            # income_stmt is {date_col: {row_name: value}} — grab most recent
            latest_col = max(income_stmt.keys()) if income_stmt else None
            if latest_col:
                total_revenue = income_stmt[latest_col].get("Total Revenue")

        if fcf is not None and total_revenue and total_revenue > 0:
            margin = fcf / total_revenue
            label = "FCF margin"
            w = weights.get("profitability_margin", 1.0)
        else:
            margin = info.get("profit_margin")
            label = "Profit margin (FCF unavailable)"
            w = weights.get("profitability_margin", 0.6)

        if margin is not None:
            if margin > 0.20:
                s = 2
            elif margin > 0.10:
                s = 1
            elif margin > 0:
                s = 0
            else:
                s = -2
            signals.append(Signal(
                name="profitability_margin", value=margin, score=s,
                weight=w,
                rationale=f"{label}: {margin:.1%}",
            ))

        # 9. Debt/Equity
        de = info.get("debt_to_equity")
        if de is not None:
            s = fund.debt_equity_score(de)
            signals.append(Signal(
                name="debt_equity_trend", value=de, score=s,
                weight=weights.get("debt_equity_trend", 0.8),
                rationale=f"D/E ratio = {de:.0f}%",
            ))

        # === Macro Signals ===

        if ctx.macro:
            macro_scores = macro_ind.macro_summary(ctx.macro)

            if "yield_curve" in macro_scores:
                s = macro_scores["yield_curve"]
                signals.append(Signal(
                    name="yield_curve", value=float(s), score=s,
                    weight=weights.get("yield_curve", 0.7),
                    rationale=f"Yield curve score: {s}",
                ))

            if "fed_cycle" in macro_scores:
                s = macro_scores["fed_cycle"]
                signals.append(Signal(
                    name="fed_cycle", value=float(s), score=s,
                    weight=weights.get("fed_cycle", 0.8),
                    rationale=f"Fed cycle score: {s}",
                ))

            if "cpi_trend" in macro_scores:
                s = macro_scores["cpi_trend"]
                signals.append(Signal(
                    name="cpi_trend", value=float(s), score=s,
                    weight=weights.get("cpi_trend", 0.6),
                    rationale=f"CPI trend score: {s}",
                ))

        # === Structural News ===

        if ctx.news:
            events = news_ind.structural_events(ctx.news, days=30)
            if events:
                descriptions = [desc for desc, _ in events]
                avg_score = sum(sc for _, sc in events) / len(events)
                s = max(-2, min(2, round(avg_score)))
                signals.append(Signal(
                    name="structural_news", value=float(len(events)), score=s,
                    weight=weights.get("structural_news", 0.5),
                    rationale=f"Structural events ({len(events)}): {'; '.join(descriptions[:3])}",
                ))

        return signals
