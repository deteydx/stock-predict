"""yfinance client for fundamentals, earnings, and analyst data."""

from __future__ import annotations

import logging
from datetime import date, datetime

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class YFinanceClient:
    """Fetch fundamental data via yfinance (free, no API key needed)."""

    def fundamentals(self, ticker: str) -> dict:
        """Get key fundamental ratios and financial data.

        Returns dict with keys: info, income_stmt, balance_sheet, cash_flow,
        earnings_dates, recommendations.
        """
        t = yf.Ticker(ticker)
        info = t.info or {}

        result = {
            "info": {
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap"),
                "pe_trailing": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "pb": info.get("priceToBook"),
                "peg": info.get("pegRatio"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "roe": info.get("returnOnEquity"),
                "profit_margin": info.get("profitMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "debt_to_equity": info.get("debtToEquity"),
                "free_cash_flow": info.get("freeCashflow"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "fifty_day_average": info.get("fiftyDayAverage"),
                "two_hundred_day_average": info.get("twoHundredDayAverage"),
            },
        }

        # Income statement (annual)
        try:
            income = t.income_stmt
            if income is not None and not income.empty:
                result["income_stmt"] = income.to_dict()
        except Exception:
            logger.warning("Failed to fetch income statement for %s", ticker)

        # Balance sheet (annual)
        try:
            bs = t.balance_sheet
            if bs is not None and not bs.empty:
                result["balance_sheet"] = bs.to_dict()
        except Exception:
            logger.warning("Failed to fetch balance sheet for %s", ticker)

        # Cash flow (annual)
        try:
            cf = t.cashflow
            if cf is not None and not cf.empty:
                result["cash_flow"] = cf.to_dict()
        except Exception:
            logger.warning("Failed to fetch cash flow for %s", ticker)

        # Quarterly earnings
        try:
            qe = t.quarterly_earnings
            if qe is not None and not qe.empty:
                result["quarterly_earnings"] = qe.to_dict()
        except Exception:
            pass

        logger.info("Fetched fundamentals for %s", ticker)
        return result

    def earnings_dates(self, ticker: str) -> list[datetime]:
        """Get upcoming and recent earnings dates."""
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal and "Earnings Date" in cal:
                raw = cal["Earnings Date"]
                if isinstance(raw, list):
                    return [
                        datetime.combine(d, datetime.min.time()) if isinstance(d, date) else d
                        for d in raw
                    ]
        except Exception:
            logger.warning("Failed to fetch earnings dates for %s", ticker)
        return []

    def analyst_recommendations(self, ticker: str) -> pd.DataFrame:
        """Get analyst recommendation trends."""
        try:
            t = yf.Ticker(ticker)
            recs = t.recommendations
            if recs is not None and not recs.empty:
                return recs
        except Exception:
            logger.warning("Failed to fetch recommendations for %s", ticker)
        return pd.DataFrame()

    def history(self, ticker: str, period: str = "10y") -> pd.DataFrame:
        """Get historical price data (backup for when IBKR is unavailable)."""
        t = yf.Ticker(ticker)
        df = t.history(period=period, auto_adjust=True)
        if df.index.tz is not None:
            df.index = df.index.tz_convert("UTC").tz_localize(None)
        df.index.name = "date"
        df.columns = [c.lower() for c in df.columns]
        return df
