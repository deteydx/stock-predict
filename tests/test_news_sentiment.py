from datetime import UTC, datetime, timedelta

from stockpredict.indicators.news import estimate_article_sentiment, recent_news_count
from stockpredict.types import NewsItem


def test_estimate_article_sentiment_positive_headline():
    sentiment = estimate_article_sentiment(
        "Apple beats estimates and raises guidance on strong iPhone demand",
        "",
    )
    assert sentiment > 0.2


def test_estimate_article_sentiment_negative_headline():
    sentiment = estimate_article_sentiment(
        "Tesla cuts guidance after weak demand and antitrust probe",
        "",
    )
    assert sentiment < -0.2


def test_recent_news_count_only_counts_recent_items():
    recent = NewsItem(headline="Recent", source="Test", relevance=1.0)
    old = NewsItem(headline="Old", source="Test", relevance=1.0)
    now = datetime.now(UTC).replace(tzinfo=None)
    recent.published_at = now - timedelta(hours=3)
    old.published_at = now - timedelta(hours=48)

    assert recent_news_count([recent, old], hours=24) == 1
