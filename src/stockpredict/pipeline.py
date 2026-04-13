"""Main analysis pipeline: fetch → indicators → score → AI → report."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

import pandas as pd
import yaml

from config.settings import Settings, get_settings
from stockpredict.analysis.base import AnalysisContext
from stockpredict.analysis.long_term import LongTermAnalyzer
from stockpredict.analysis.medium_term import MediumTermAnalyzer
from stockpredict.analysis.short_term import ShortTermAnalyzer
from stockpredict.data.cache import DiskCache, TTL_DAILY_BARS, TTL_FUNDAMENTALS, TTL_NEWS, TTL_MACRO
from stockpredict.data.ibkr_client import IBKRClient
from stockpredict.data.yfinance_client import YFinanceClient
from stockpredict.indicators import news as news_ind
from stockpredict.ml.predictor import NaiveBaselinePredictor
from stockpredict.strategy.aggregator import aggregate
from stockpredict.strategy.scoring import score_horizon
from stockpredict.types import FundamentalsSnapshot, Horizon, NewsItem, ProgressUpdate, Report

logger = logging.getLogger(__name__)

# Type for progress callback
ProgressCallback = Callable[[ProgressUpdate], Coroutine[Any, Any, None]] | None


def _load_weights(weights_file: Path) -> dict[str, dict[str, float]]:
    """Load signal weights from YAML config."""
    if weights_file.exists():
        with open(weights_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _build_fundamentals_snapshot(info: dict[str, Any]) -> FundamentalsSnapshot:
    return FundamentalsSnapshot(
        sector=info.get("sector") or None,
        industry=info.get("industry") or None,
        market_cap=_safe_float(info.get("market_cap")),
        pe_trailing=_safe_float(info.get("pe_trailing")),
        pe_forward=_safe_float(info.get("pe_forward")),
        pb=_safe_float(info.get("pb")),
        peg=_safe_float(info.get("peg")),
        ev_ebitda=_safe_float(info.get("ev_ebitda")),
        roe=_safe_float(info.get("roe")),
        profit_margin=_safe_float(info.get("profit_margin")),
        revenue_growth=_safe_float(info.get("revenue_growth")),
        earnings_growth=_safe_float(info.get("earnings_growth")),
        debt_to_equity=_safe_float(info.get("debt_to_equity")),
        free_cash_flow=_safe_float(info.get("free_cash_flow")),
        dividend_yield=_safe_float(info.get("dividend_yield")),
        beta=_safe_float(info.get("beta")),
    )


async def _notify(callback: ProgressCallback, step: str, progress: int, message: str):
    if callback:
        await callback(ProgressUpdate(step=step, progress=progress, message=message))


async def run_analysis(
    ticker: str,
    ibkr_client: IBKRClient | None = None,
    settings: Settings | None = None,
    progress_callback: ProgressCallback = None,
) -> Report:
    """Execute the full analysis pipeline for a ticker.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        ibkr_client: Optional pre-connected IBKR client. If None, will use yfinance for price data.
        settings: App settings. If None, loads from env.
        progress_callback: Async function called with progress updates.

    Returns:
        Complete Report with all analysis data.
    """
    if settings is None:
        settings = get_settings()

    ticker = ticker.upper()
    cache = DiskCache(settings.cache_dir)
    yf_client = YFinanceClient()
    weights = _load_weights(settings.weights_file)

    report = Report(ticker=ticker, generated_at=datetime.utcnow())

    # -----------------------------------------------------------------------
    # Step 1: Fetch price data
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "fetching_bars", 10, "获取K线数据...")

    bars: pd.DataFrame = pd.DataFrame()

    # Try IBKR first
    if ibkr_client and ibkr_client.connected:
        cached = cache.get_df("ibkr", ticker, "daily_bars", TTL_DAILY_BARS)
        if cached is not None:
            bars = cached
        else:
            try:
                bars = await ibkr_client.historical_bars(ticker, duration="2 Y", bar_size="1 day")
                if not bars.empty:
                    cache.set_df("ibkr", ticker, "daily_bars", bars)
            except Exception as e:
                logger.warning("IBKR bars failed for %s: %s, falling back to yfinance", ticker, e)

    # Fallback to yfinance
    if bars.empty:
        cached = cache.get_df("yfinance", ticker, "daily_bars", TTL_DAILY_BARS)
        if cached is not None:
            bars = cached
        else:
            bars = yf_client.history(ticker, period="2y")
            if not bars.empty:
                cache.set_df("yfinance", ticker, "daily_bars", bars)

    if bars.empty:
        report.caveats.append("No price data available")
        return report

    # Set current price info
    report.as_of_price = float(bars["close"].iloc[-1])
    if len(bars) >= 2:
        report.price_change_pct = float(
            (bars["close"].iloc[-1] - bars["close"].iloc[-2]) / bars["close"].iloc[-2]
        )

    # Chart data for frontend
    chart_df = bars.tail(500)
    report.chart_data = []
    for index_value, row in chart_df.iterrows():
        entry = {
            "time": (
                index_value.strftime("%Y-%m-%d")
                if hasattr(index_value, "strftime")
                else str(index_value)
            )
        }
        for col in ["open", "high", "low", "close", "volume"]:
            if col in row.index:
                entry[col] = float(row[col]) if pd.notna(row[col]) else None
        report.chart_data.append(entry)

    # -----------------------------------------------------------------------
    # Step 2: Fetch fundamentals
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "fetching_fundamentals", 25, "获取基本面数据...")

    fundamentals = cache.get_json("yfinance", ticker, "fundamentals", TTL_FUNDAMENTALS)
    if fundamentals is None:
        try:
            fundamentals = yf_client.fundamentals(ticker)
            cache.set_json("yfinance", ticker, "fundamentals", fundamentals)
        except Exception as e:
            logger.warning("Fundamentals failed for %s: %s", ticker, e)
            report.caveats.append("Fundamentals data unavailable")

    if fundamentals and "info" in fundamentals:
        info = fundamentals["info"]
        report.company_name = info.get("name", "")
        report.fundamentals = _build_fundamentals_snapshot(info)

    # Earnings dates (fetched separately — DataFrame can't go through JSON cache)
    if fundamentals is not None:
        try:
            earnings_dates = yf_client.earnings_dates(ticker)
            if earnings_dates:
                fundamentals["earnings_dates"] = earnings_dates
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Step 3: Fetch news
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "fetching_news", 40, "获取新闻数据...")

    news_items: list[NewsItem] = []
    try:
        if settings.finnhub_api_key:
            from stockpredict.data.finnhub_client import FinnhubClient
            fh = FinnhubClient(settings.finnhub_api_key)
            raw_news = fh.company_news(ticker)
            news_items = [
                item.model_copy(update={
                    "sentiment": news_ind.estimate_article_sentiment(item.headline, item.summary),
                })
                for item in raw_news
            ]
            report.news = news_items[:20]
        else:
            report.caveats.append("News data unavailable (no Finnhub API key)")
    except Exception as e:
        logger.warning("News fetch failed for %s: %s", ticker, e)
        report.caveats.append(f"News data unavailable: {e}")

    # LLM-enhanced sentiment when AI is enabled
    if news_items and settings.ai.ai_enabled:
        try:
            from stockpredict.ai.providers import create_provider
            provider = create_provider(settings.ai.ai_provider, settings.ai)
            pairs = [(item.headline, item.summary or "") for item in news_items]
            ai_sentiments = await news_ind.llm_sentiment_batch(pairs, provider)
            news_items = [
                item.model_copy(update={"sentiment": sent})
                for item, sent in zip(news_items, ai_sentiments)
            ]
            report.news = news_items[:20]
        except Exception as e:
            logger.warning("LLM sentiment failed, using keyword fallback: %s", e)

    # -----------------------------------------------------------------------
    # Step 4: Fetch macro data
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "fetching_macro", 50, "获取宏观数据...")

    macro = None
    if settings.fred_api_key:
        cached_macro = cache.get_json("fred", "_global", "macro_snapshot", TTL_MACRO)
        if cached_macro:
            # Convert back from JSON to pd.Series
            macro = {k: pd.Series(v) for k, v in cached_macro.items() if v}
        else:
            try:
                from stockpredict.data.fred_client import FREDClient
                fred = FREDClient(settings.fred_api_key)
                macro = fred.macro_snapshot()
                # Cache as serializable dict
                cache.set_json("fred", "_global", "macro_snapshot", {
                    k: v.to_dict() for k, v in macro.items()
                })
            except Exception as e:
                logger.warning("FRED data failed: %s", e)
                report.caveats.append(f"Macro data unavailable: {e}")
    else:
        report.caveats.append("Macro data unavailable (no FRED API key)")

    # -----------------------------------------------------------------------
    # Step 5: Fetch benchmark (SPY) for relative strength
    # -----------------------------------------------------------------------
    benchmark_bars = cache.get_df("yfinance", "SPY", "daily_bars", TTL_DAILY_BARS)
    if benchmark_bars is None:
        try:
            benchmark_bars = yf_client.history("SPY", period="2y")
            if not benchmark_bars.empty:
                cache.set_df("yfinance", "SPY", "daily_bars", benchmark_bars)
        except Exception:
            benchmark_bars = None

    # -----------------------------------------------------------------------
    # Step 5b: Fetch sector ETF for sector trend signal
    # -----------------------------------------------------------------------
    sector_etf_bars = None
    if fundamentals and "info" in fundamentals:
        from stockpredict.indicators.technical import SECTOR_ETFS
        sector = fundamentals["info"].get("sector", "")
        etf_ticker = SECTOR_ETFS.get(sector)
        if etf_ticker:
            sector_etf_bars = cache.get_df("yfinance", etf_ticker, "daily_bars", TTL_DAILY_BARS)
            if sector_etf_bars is None:
                try:
                    sector_etf_bars = yf_client.history(etf_ticker, period="1y")
                    if sector_etf_bars is not None and not sector_etf_bars.empty:
                        cache.set_df("yfinance", etf_ticker, "daily_bars", sector_etf_bars)
                except Exception:
                    sector_etf_bars = None

    # -----------------------------------------------------------------------
    # Step 6: Compute indicators & analyze
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "computing_indicators", 60, "计算指标...")

    ctx = AnalysisContext(
        ticker=ticker,
        bars=bars,
        fundamentals=fundamentals,
        macro=macro,
        news=news_items,
        benchmark_bars=benchmark_bars,
        sector_etf_bars=sector_etf_bars,
        weights=None,
    )

    analyzers = [
        ShortTermAnalyzer(),
        MediumTermAnalyzer(),
        LongTermAnalyzer(),
    ]

    # -----------------------------------------------------------------------
    # Step 7: Score each horizon
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "scoring", 70, "评分计算...")

    predictor = NaiveBaselinePredictor()

    for analyzer in analyzers:
        ctx.weights = weights.get(analyzer.horizon.value, {})
        signals = analyzer.analyze(ctx)
        horizon_score = score_horizon(analyzer.horizon, signals, ctx.weights)

        # ML prediction
        ml_prob = predictor.predict_up_probability(pd.DataFrame(), analyzer.horizon)
        final_score = aggregate(
            horizon_score, ml_prob,
            rule_weight=settings.ml.rule_weight,
            ml_weight=settings.ml.weight,
        )

        if analyzer.horizon == Horizon.SHORT:
            report.short_term = final_score
        elif analyzer.horizon == Horizon.MEDIUM:
            report.medium_term = final_score
        elif analyzer.horizon == Horizon.LONG:
            report.long_term = final_score

    # Collect all risks from signals
    for hs in [report.short_term, report.medium_term, report.long_term]:
        if hs:
            report.caveats.extend(hs.caveats)

    # -----------------------------------------------------------------------
    # Step 8: AI Analysis
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "ai_analysis", 80, "AI分析中...")

    if settings.ai.ai_enabled:
        try:
            from stockpredict.ai.analyzer import create_ai_analyzer
            ai_analyzer = await create_ai_analyzer(settings.ai)
            if ai_analyzer:
                report.ai_summary = await ai_analyzer.analyze(report)
                report.ai_provider = settings.ai.ai_provider
                report.ai_model = (
                    settings.ai.openai_model
                    if settings.ai.ai_provider == "openai"
                    else settings.ai.claude_model
                )
        except Exception as e:
            logger.error("AI analysis failed for %s: %s", ticker, e)
            report.caveats.append(f"AI analysis failed: {e}")

    # -----------------------------------------------------------------------
    # Step 9: Finalize
    # -----------------------------------------------------------------------
    await _notify(progress_callback, "saving", 95, "保存结果...")

    report.data_sources = {
        "bars": {"source": "ibkr" if ibkr_client and ibkr_client.connected else "yfinance", "count": len(bars)},
        "fundamentals": {"available": fundamentals is not None},
        "news": {"count": len(news_items)},
        "macro": {"available": macro is not None},
    }

    return report
