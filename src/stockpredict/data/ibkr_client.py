"""IBKR Gateway client for historical bars, quotes, and option chains."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import pandas as pd
from ib_async import IB, Contract, Option, Stock, util

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
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
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

    async def option_chain(
        self,
        ticker: str,
        max_expiries: int = 3,
        strike_window_pct: float = 0.15,
    ) -> dict:
        """Fetch option chain for the nearest ``max_expiries`` expirations.

        Returns a dict keyed by expiry (YYYY-MM-DD) with:
            {
                "spot": float,
                "dte": int,
                "calls": DataFrame[strike, bid, ask, last, iv, delta, volume, open_interest],
                "puts":  DataFrame[...same columns...],
            }
        Strikes are restricted to spot ± ``strike_window_pct`` to keep request volume
        manageable. Returns an empty dict on any failure.
        """
        contract = self._stock_contract(ticker)

        try:
            qualified = await self._ib.qualifyContractsAsync(contract)
            if not qualified:
                logger.warning("Could not qualify stock contract for %s", ticker)
                return {}
            stock = qualified[0]

            # Spot price (needed for strike window & DTE computation)
            self._ib.reqMktData(stock, "", False, False)
            await asyncio.sleep(1.5)
            stock_ticker = self._ib.ticker(stock)
            spot = None
            for candidate in (stock_ticker.last, stock_ticker.close, stock_ticker.marketPrice()):
                if candidate is not None and candidate == candidate and candidate > 0:
                    spot = float(candidate)
                    break
            self._ib.cancelMktData(stock)
            if spot is None:
                logger.warning("No spot price for %s; cannot build option chain", ticker)
                return {}

            params = await self._ib.reqSecDefOptParamsAsync(
                stock.symbol, "", "STK", stock.conId
            )
            smart_params = next((p for p in params if p.exchange == "SMART"), None)
            if smart_params is None and params:
                smart_params = params[0]
            if smart_params is None:
                logger.warning("No option params returned for %s", ticker)
                return {}

            today = datetime.utcnow().date()
            expiries_sorted = sorted(
                e for e in smart_params.expirations if e and len(e) == 8
            )
            selected_expiries: list[str] = []
            for exp in expiries_sorted:
                exp_date = datetime.strptime(exp, "%Y%m%d").date()
                if exp_date < today:
                    continue
                selected_expiries.append(exp)
                if len(selected_expiries) >= max_expiries:
                    break

            if not selected_expiries:
                return {}

            low = spot * (1 - strike_window_pct)
            high = spot * (1 + strike_window_pct)
            strikes = sorted(s for s in smart_params.strikes if low <= s <= high)
            if not strikes:
                # Fallback: pick 15 strikes nearest to spot
                strikes = sorted(smart_params.strikes, key=lambda s: abs(s - spot))[:15]
                strikes.sort()

            chain: dict = {}
            for expiry in selected_expiries:
                contracts: list[Option] = []
                for strike in strikes:
                    for right in ("C", "P"):
                        contracts.append(
                            Option(stock.symbol, expiry, strike, right, "SMART", currency="USD")
                        )
                quotes = await self.option_quotes(contracts)
                calls_rows = []
                puts_rows = []
                for row in quotes:
                    target = calls_rows if row["right"] == "C" else puts_rows
                    target.append(row)

                exp_date = datetime.strptime(expiry, "%Y%m%d").date()
                dte = max((exp_date - today).days, 0)
                chain[exp_date.isoformat()] = {
                    "spot": spot,
                    "dte": dte,
                    "calls": pd.DataFrame(calls_rows),
                    "puts": pd.DataFrame(puts_rows),
                }

            return chain
        except Exception as e:  # pragma: no cover - network-dependent
            logger.warning("IBKR option chain failed for %s: %s", ticker, e)
            return {}

    async def option_quotes(self, contracts: list[Option]) -> list[dict]:
        """Batch-request market data (IV, Greeks, OI) for a list of option contracts."""
        if not contracts:
            return []

        qualified = await self._ib.qualifyContractsAsync(*contracts)
        qualified = [c for c in qualified if getattr(c, "conId", 0)]
        if not qualified:
            return []

        # genericTickList="100,101,106" → option volume, option open interest, option IV
        tickers = [self._ib.reqMktData(c, "100,101,106", False, False) for c in qualified]
        await asyncio.sleep(2.5)

        rows: list[dict] = []
        for contract, t in zip(qualified, tickers):
            greeks = t.modelGreeks or t.lastGreeks or t.bidGreeks or t.askGreeks

            def _num(v):
                return float(v) if v is not None and v == v else None

            oi = None
            if contract.right == "C":
                oi = _num(getattr(t, "callOpenInterest", None))
            else:
                oi = _num(getattr(t, "putOpenInterest", None))

            rows.append({
                "strike": float(contract.strike),
                "right": contract.right,
                "expiry": contract.lastTradeDateOrContractMonth,
                "bid": _num(t.bid),
                "ask": _num(t.ask),
                "last": _num(t.last),
                "volume": _num(t.volume) or 0,
                "open_interest": int(oi) if oi is not None else 0,
                "iv": _num(greeks.impliedVol) if greeks else _num(getattr(t, "impliedVolatility", None)),
                "delta": _num(greeks.delta) if greeks else None,
                "gamma": _num(greeks.gamma) if greeks else None,
                "vega": _num(greeks.vega) if greeks else None,
                "theta": _num(greeks.theta) if greeks else None,
            })

        for c in qualified:
            try:
                self._ib.cancelMktData(c)
            except Exception:
                pass

        return rows

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()
