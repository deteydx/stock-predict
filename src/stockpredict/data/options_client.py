"""Unified options chain loader: IBKR primary, yfinance fallback.

Returns a ``RawOptionsChain`` dict of the shape:

    {
        "<YYYY-MM-DD>": {
            "spot": float,
            "dte": int,
            "calls": pd.DataFrame[strike, bid, ask, last, iv, delta,
                                  volume, open_interest],
            "puts":  pd.DataFrame[...same columns...],
        },
        ...
    }
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from stockpredict.data.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)

RawOptionsChain = dict[str, dict[str, Any]]


class OptionsClient:
    """Best-effort options chain fetcher that prefers IBKR and falls back to yfinance."""

    def __init__(self, ibkr_client: IBKRClient | None = None):
        self._ibkr = ibkr_client

    async def fetch_chain(
        self,
        ticker: str,
        max_expiries: int = 3,
    ) -> tuple[RawOptionsChain, str]:
        """Fetch the nearest ``max_expiries`` expirations.

        Returns (chain, data_source). ``data_source`` is "ibkr", "yfinance", or ""
        when nothing worked.
        """
        ticker = ticker.upper()

        if self._ibkr and self._ibkr.connected:
            try:
                chain = await self._ibkr.option_chain(ticker, max_expiries=max_expiries)
                if chain:
                    logger.info("Options chain for %s via IBKR (%d expiries)", ticker, len(chain))
                    return chain, "ibkr"
            except Exception as e:
                logger.warning("IBKR options fetch failed for %s: %s", ticker, e)

        try:
            chain = self._fetch_yfinance(ticker, max_expiries=max_expiries)
            if chain:
                logger.info("Options chain for %s via yfinance (%d expiries)", ticker, len(chain))
                return chain, "yfinance"
        except Exception as e:
            logger.warning("yfinance options fetch failed for %s: %s", ticker, e)

        return {}, ""

    # ------------------------------------------------------------------
    # yfinance fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _fetch_yfinance(ticker: str, max_expiries: int = 3) -> RawOptionsChain:
        t = yf.Ticker(ticker)
        expiries = list(t.options or [])[:max_expiries]
        if not expiries:
            return {}

        # Spot from fast_info → info → last close
        spot: float | None = None
        try:
            fi = getattr(t, "fast_info", None)
            if fi is not None:
                candidate = getattr(fi, "last_price", None) or getattr(fi, "lastPrice", None)
                if candidate is not None and candidate == candidate:
                    spot = float(candidate)
        except Exception:
            spot = None
        if spot is None:
            try:
                hist = t.history(period="5d", auto_adjust=True)
                if not hist.empty:
                    spot = float(hist["Close"].iloc[-1])
            except Exception:
                pass
        if spot is None:
            return {}

        today = datetime.utcnow().date()
        result: RawOptionsChain = {}
        for expiry_str in expiries:
            try:
                chain = t.option_chain(expiry_str)
            except Exception as e:  # pragma: no cover - network-dependent
                logger.debug("yfinance chain error for %s %s: %s", ticker, expiry_str, e)
                continue

            calls_df = OptionsClient._normalize_yf_df(chain.calls, right="C")
            puts_df = OptionsClient._normalize_yf_df(chain.puts, right="P")

            try:
                exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            dte = max((exp_date - today).days, 0)

            result[exp_date.isoformat()] = {
                "spot": spot,
                "dte": dte,
                "calls": calls_df,
                "puts": puts_df,
            }

        return result

    @staticmethod
    def _normalize_yf_df(df: pd.DataFrame, right: str) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(
                columns=["strike", "bid", "ask", "last", "volume", "open_interest", "iv",
                         "delta", "gamma", "vega", "theta", "right"]
            )
        n = len(df)
        volume = df["volume"] if "volume" in df.columns else pd.Series([0] * n)
        open_interest = df["openInterest"] if "openInterest" in df.columns else pd.Series([0] * n)
        out = pd.DataFrame({
            "strike": df["strike"].astype(float),
            "bid": df["bid"] if "bid" in df.columns else pd.Series([None] * n),
            "ask": df["ask"] if "ask" in df.columns else pd.Series([None] * n),
            "last": df["lastPrice"] if "lastPrice" in df.columns else pd.Series([None] * n),
            "volume": volume.fillna(0).astype(float),
            "open_interest": open_interest.fillna(0).astype(int),
            "iv": df["impliedVolatility"] if "impliedVolatility" in df.columns else pd.Series([None] * n),
        })
        out["delta"] = None  # yfinance does not provide Greeks
        out["gamma"] = None
        out["vega"] = None
        out["theta"] = None
        out["right"] = right
        return out
