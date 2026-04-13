"""IBKR Gateway client for historical bars, quotes, and option chains."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import pandas as pd
from ib_async import IB, Contract, Stock, util

from config.settings import IBKRSettings

logger = logging.getLogger(__name__)


class IBKRClient:
    """Thin async wrapper around ib_async for market data retrieval."""

    def __init__(self, settings: IBKRSettings | None = None):
        self._settings = settings or IBKRSettings()
        self._ib = IB()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected and self._ib.isConnected()

    async def connect(self) -> None:
        if self.connected:
            return
        await self._ib.connectAsync(
            host=self._settings.host,
            port=self._settings.port,
            clientId=self._settings.client_id,
            readonly=self._settings.readonly,
        )
        self._connected = True
        logger.info(
            "Connected to IBKR at %s:%s (clientId=%s)",
            self._settings.host,
            self._settings.port,
            self._settings.client_id,
        )

    async def disconnect(self) -> None:
        if self._ib.isConnected():
            self._ib.disconnect()
        self._connected = False
        logger.info("Disconnected from IBKR")

    def _stock_contract(self, ticker: str) -> Stock:
        return Stock(ticker.upper(), "SMART", "USD")

    async def historical_bars(
        self,
        ticker: str,
        duration: str = "2 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES",
        use_rth: bool = True,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV bars.

        Args:
            ticker: Stock symbol (e.g. "AAPL")
            duration: How far back, e.g. "1 Y", "6 M", "30 D"
            bar_size: Bar granularity, e.g. "1 day", "1 hour", "5 mins"
            what_to_show: "TRADES", "MIDPOINT", "BID", "ASK"
            use_rth: Regular trading hours only

        Returns:
            DataFrame with columns: date, open, high, low, close, volume, average, barCount
        """
        contract = self._stock_contract(ticker)
        bars = await self._ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1,
        )
        if not bars:
            logger.warning("No bars returned for %s", ticker)
            return pd.DataFrame()

        df = util.df(bars)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        # Normalize timezone to tz-naive UTC
        if df.index.tz is not None:
            df.index = df.index.tz_convert("UTC").tz_localize(None)
        logger.info("Fetched %d bars for %s (%s, %s)", len(df), ticker, duration, bar_size)
        return df

    async def quote(self, ticker: str) -> dict:
        """Get current/delayed quote snapshot."""
        contract = self._stock_contract(ticker)
        self._ib.reqMktData(contract, "", False, False)
        await asyncio.sleep(2)  # Wait for data to arrive
        ticker_obj = self._ib.ticker(contract)
        self._ib.cancelMktData(contract)

        return {
            "last": ticker_obj.last if ticker_obj.last == ticker_obj.last else None,
            "bid": ticker_obj.bid if ticker_obj.bid == ticker_obj.bid else None,
            "ask": ticker_obj.ask if ticker_obj.ask == ticker_obj.ask else None,
            "high": ticker_obj.high if ticker_obj.high == ticker_obj.high else None,
            "low": ticker_obj.low if ticker_obj.low == ticker_obj.low else None,
            "close": ticker_obj.close if ticker_obj.close == ticker_obj.close else None,
            "volume": ticker_obj.volume if ticker_obj.volume == ticker_obj.volume else None,
        }

    async def contract_details(self, ticker: str) -> dict:
        """Get contract details (company name, industry, etc.)."""
        contract = self._stock_contract(ticker)
        details_list = await self._ib.reqContractDetailsAsync(contract)
        if not details_list:
            return {}
        d = details_list[0]
        return {
            "long_name": d.longName,
            "industry": d.industry,
            "category": d.category,
            "subcategory": d.subcategory,
        }

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()
