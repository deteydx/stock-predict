"""Analysis orchestrator: fetch options chain + compute outlook.

Kept independent from the horizon analyzers — any failure returns ``None`` and
the pipeline simply skips the options section.
"""

from __future__ import annotations

import logging

import pandas as pd

from stockpredict.data.ibkr_client import IBKRClient
from stockpredict.data.options_client import OptionsClient
from stockpredict.indicators.options import (
    compute_options_outlook,
    realized_vol_series,
)
from stockpredict.types import OptionsOutlook

logger = logging.getLogger(__name__)


async def analyze_options(
    ticker: str,
    ibkr_client: IBKRClient | None,
    price_df: pd.DataFrame,
    max_expiries: int = 3,
) -> OptionsOutlook | None:
    """Fetch options chain and compute the options-implied outlook.

    Args:
        ticker: Stock symbol.
        ibkr_client: Optional pre-connected IBKR client (preferred path).
        price_df: Historical daily OHLCV used to derive the HV proxy. Must have
            a ``close`` column.
        max_expiries: Number of nearest expiries to load (default 3).

    Returns:
        ``OptionsOutlook`` on success, ``None`` on any failure or when no
        options data is available.
    """
    try:
        client = OptionsClient(ibkr_client=ibkr_client)
        chain, source = await client.fetch_chain(ticker, max_expiries=max_expiries)
        if not chain:
            logger.info("No options chain available for %s", ticker)
            return None

        if price_df is None or price_df.empty or "close" not in price_df.columns:
            hv_series = pd.Series(dtype=float)
        else:
            hv_series = realized_vol_series(price_df["close"], window=20)
            # Keep last 252 trading days (~52 weeks) as the reference distribution
            hv_series = hv_series.tail(252)

        outlook = compute_options_outlook(chain, hv_series, data_source=source)
        return outlook
    except Exception as e:  # pragma: no cover - network/data dependent
        logger.warning("Options outlook failed for %s: %s", ticker, e)
        return None
