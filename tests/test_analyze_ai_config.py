from __future__ import annotations

from config.settings import Settings
from stockpredict.api.routes.analyze import (
    AnalyzeAIRequest,
    RequestedAIConfig,
    _build_runtime_settings,
    _matches_requested_ai_config,
)
from stockpredict.db.models import Analysis


def test_request_ai_settings_override_runtime_provider_and_model():
    settings = Settings()

    runtime_settings, requested_ai = _build_runtime_settings(
        settings,
        AnalyzeAIRequest(
            provider="claude",
            model="claude-3-5-haiku-latest",
            api_key="  test-claude-key  ",
        ),
    )

    assert runtime_settings.ai.ai_enabled is True
    assert runtime_settings.ai.ai_provider == "claude"
    assert runtime_settings.ai.anthropic_api_key == "test-claude-key"
    assert runtime_settings.ai.openai_api_key == ""
    assert runtime_settings.ai.claude_model == "claude-3-5-haiku-latest"
    assert requested_ai == RequestedAIConfig(
        enabled=True,
        provider="claude",
        model="claude-3-5-haiku-latest",
    )


def test_blank_request_api_key_disables_ai_for_runtime_settings():
    settings = Settings()
    settings.ai.ai_enabled = True
    settings.ai.ai_provider = "openai"
    settings.ai.openai_api_key = "server-key"
    settings.ai.openai_model = "gpt-4o"

    runtime_settings, requested_ai = _build_runtime_settings(
        settings,
        AnalyzeAIRequest(provider="openai", model="gpt-4.1", api_key="   "),
    )

    assert runtime_settings.ai.ai_enabled is False
    assert runtime_settings.ai.ai_provider == "openai"
    assert runtime_settings.ai.openai_api_key == ""
    assert runtime_settings.ai.openai_model == "gpt-4.1"
    assert requested_ai == RequestedAIConfig(enabled=False)


def test_analysis_matches_requested_ai_config():
    openai_analysis = Analysis(
        ticker="AAPL",
        status="completed",
        ai_provider="openai",
        ai_model="gpt-4.1",
    )
    no_ai_analysis = Analysis(
        ticker="AAPL",
        status="completed",
    )

    assert _matches_requested_ai_config(
        openai_analysis,
        RequestedAIConfig(enabled=True, provider="openai", model="gpt-4.1"),
    ) is True
    assert _matches_requested_ai_config(
        openai_analysis,
        RequestedAIConfig(enabled=True, provider="claude", model="claude-sonnet-4-20250514"),
    ) is False
    assert _matches_requested_ai_config(
        no_ai_analysis,
        RequestedAIConfig(enabled=False),
    ) is True


def test_request_uses_provider_default_model_when_model_is_omitted():
    settings = Settings()
    settings.ai.claude_model = "claude-sonnet-server-default"

    runtime_settings, requested_ai = _build_runtime_settings(
        settings,
        AnalyzeAIRequest(
            provider="claude",
            api_key="claude-key",
        ),
    )

    assert runtime_settings.ai.ai_enabled is True
    assert runtime_settings.ai.claude_model == "claude-sonnet-server-default"
    assert requested_ai == RequestedAIConfig(
        enabled=True,
        provider="claude",
        model="claude-sonnet-server-default",
    )
