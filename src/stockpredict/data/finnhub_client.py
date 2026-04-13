"""Finnhub client for company news, sentiment, and recommendations."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import finnhub

from stockpredict.types import NewsItem

logger = logging.getLogger(__name__)


class FinnhubClient:
    """Fetch news and sentiment data from Finnhub (free tier: 60 req/min)."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "Finnhub API key is required. Get one free at https://finnhub.io/register"
            )
        self._client = finnhub.Client(api_key=api_key)

    def company_news(
        self,
        ticker: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[NewsItem]:
        """Fetch recent company news with sentiment."""
        if to_date is None:
            to_date = datetime.now()
        if from_date is None:
            from_date = to_date - timedelta(days=30)

        raw = self._client.company_news(
            ticker.upper(),
            _from=from_date.strftime("%Y-%m-%d"),
            to=to_date.strftime("%Y-%m-%d"),
        )

        items = []
        for article in raw:
            items.append(
                NewsItem(
                    headline=article.get("headline", ""),
                    source=article.get("source", ""),
                    url=article.get("url", ""),
                    published_at=datetime.utcfromtimestamp(article["datetime"])
                    if article.get("datetime")
                    else None,
                    summary=article.get("summary", ""),
                    # Finnhub news doesn't have per-article sentiment in free tier;
                    # we'll estimate it later in the pipeline.
                    sentiment=0.0,
                    relevance=1.0,
                    category=article.get("category", "other"),
                )
            )

        logger.info("Fetched %d news articles for %s", len(items), ticker)
        return items

    def recommendation_trends(self, ticker: str) -> list[dict]:
        """Get analyst recommendation trends (buy/hold/sell counts by month)."""
        try:
            return self._client.recommendation_trends(ticker.upper())
        except Exception as e:
            logger.warning("Failed to fetch recommendation trends for %s: %s", ticker, e)
            return []

    def company_profile(self, ticker: str) -> dict:
        """Get company profile (name, sector, market cap, etc.)."""
        try:
            return self._client.company_profile2(symbol=ticker.upper())
        except Exception as e:
            logger.warning("Failed to fetch company profile for %s: %s", ticker, e)
            return {}

    def basic_financials(self, ticker: str) -> dict:
        """Get basic financial metrics."""
        try:
            return self._client.company_basic_financials(ticker.upper(), "all")
        except Exception as e:
            logger.warning("Failed to fetch financials for %s: %s", ticker, e)
            return {}
