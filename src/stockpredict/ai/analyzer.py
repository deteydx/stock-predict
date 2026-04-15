"""AI Analyzer: orchestrates LLM-based analysis of stock data."""

from __future__ import annotations

import logging

from stockpredict.ai.prompts import build_user_prompt, get_system_prompt
from stockpredict.ai.providers import LLMProvider, create_provider
from stockpredict.types import Report

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Sends collected analysis data to an LLM for comprehensive interpretation."""

    def __init__(self, provider: LLMProvider):
        self._provider = provider

    async def analyze(self, report: Report, language: str = "zh") -> str:
        """Generate AI analysis summary for the given report.

        Args:
            report: Complete Report with all signals and scores populated.
            language: Output language, "zh" or "en".

        Returns:
            Markdown-formatted analysis text.
        """
        lang = "en" if language == "en" else "zh"
        report_data = report.model_dump()
        user_prompt = build_user_prompt(report_data, language=lang)
        system_prompt = get_system_prompt(language=lang)

        logger.info("Sending analysis request to LLM for %s (lang=%s)...", report.ticker, lang)
        summary = await self._provider.complete(system_prompt, user_prompt)
        logger.info("AI analysis complete for %s: %d chars", report.ticker, len(summary))
        return summary


async def create_ai_analyzer(settings) -> AIAnalyzer | None:
    """Create an AIAnalyzer if AI is enabled, else return None."""
    if not settings.ai_enabled:
        return None
    try:
        provider = create_provider(settings.ai_provider, settings)
        return AIAnalyzer(provider)
    except ValueError as e:
        logger.warning("AI analyzer not available: %s", e)
        return None
