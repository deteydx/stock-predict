"""FRED client for macroeconomic data."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

# Key FRED series IDs
SERIES = {
    "fed_funds": "FEDFUNDS",         # Federal Funds Effective Rate
    "cpi": "CPIAUCSL",               # CPI All Urban Consumers
    "unemployment": "UNRATE",        # Unemployment Rate
    "yield_curve": "T10Y2Y",         # 10Y-2Y Treasury Spread
    "dxy": "DTWEXBGS",              # Trade Weighted Dollar Index
    "gdp": "GDP",                    # Gross Domestic Product
    "sp500": "SP500",                # S&P 500
}


class FREDClient:
    """Fetch macroeconomic data from FRED (Federal Reserve Economic Data)."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("FRED API key is required. Get one at https://fred.stlouisfed.org/docs/api/api_key.html")
        from fredapi import Fred

        self._fred = Fred(api_key=api_key)

    def get_series(
        self,
        series_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> pd.Series:
        """Fetch a single FRED series."""
        if start is None:
            start = datetime.now() - timedelta(days=365 * 5)
        if end is None:
            end = datetime.now()
        data = self._fred.get_series(series_id, observation_start=start, observation_end=end)
        return data.dropna()

    def macro_snapshot(self) -> dict[str, pd.Series]:
        """Fetch all key macro series for analysis.

        Returns dict with keys matching SERIES above.
        """
        result = {}
        for name, series_id in SERIES.items():
            try:
                result[name] = self.get_series(series_id)
                logger.info("Fetched FRED series %s (%s): %d points", name, series_id, len(result[name]))
            except Exception as e:
                logger.warning("Failed to fetch FRED series %s: %s", series_id, e)
                result[name] = pd.Series(dtype=float)
        return result
