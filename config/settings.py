from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class IBKRSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="IBKR_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 17
    readonly: bool = True


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_enabled: bool = True
    ai_provider: Literal["openai", "claude"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"


class MLSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ML_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = False
    rule_weight: float = 0.7
    weight: float = 0.3
    model_dir: Path = PROJECT_ROOT / "models"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Sub-configs
    ibkr: IBKRSettings = Field(default_factory=IBKRSettings)
    ai: AISettings = Field(default_factory=AISettings)
    ml: MLSettings = Field(default_factory=MLSettings)

    # Data source keys
    fred_api_key: str = ""
    finnhub_api_key: str = ""

    # Storage
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'stockpredict.db'}"
    cache_dir: Path = PROJECT_ROOT / "cache"
    reports_dir: Path = PROJECT_ROOT / "reports"
    weights_file: Path = PROJECT_ROOT / "config" / "weights.yaml"

    # Auth
    auth_session_days: int = 30
    auth_cookie_name: str = "stockpredict_session"
    auth_cookie_secure: bool = False


def get_settings() -> Settings:
    return Settings()
