"""Parquet-based disk cache with TTL for data sources."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Default TTLs in seconds
TTL_DAILY_BARS = 86400        # 1 day
TTL_INTRADAY_BARS = 60        # 1 minute
TTL_FUNDAMENTALS = 7 * 86400  # 7 days
TTL_MACRO = 86400             # 1 day
TTL_NEWS = 3600               # 1 hour


class DiskCache:
    """Simple file-based cache with TTL, supporting DataFrames (parquet) and dicts (json)."""

    def __init__(self, cache_dir: Path):
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, source: str, ticker: str, field: str, ext: str = "parquet") -> Path:
        subdir = self._dir / source / ticker.upper()
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{field}.{ext}"

    def _meta_path(self, data_path: Path) -> Path:
        return data_path.with_suffix(".meta")

    def _is_fresh(self, data_path: Path, ttl: int) -> bool:
        meta = self._meta_path(data_path)
        if not meta.exists() or not data_path.exists():
            return False
        try:
            saved_at = float(meta.read_text().strip())
            return (time.time() - saved_at) < ttl
        except (ValueError, OSError):
            return False

    def _touch_meta(self, data_path: Path) -> None:
        self._meta_path(data_path).write_text(str(time.time()))

    def _make_json_safe(self, data):
        if isinstance(data, Mapping):
            return {str(key): self._make_json_safe(value) for key, value in data.items()}
        if isinstance(data, (list, tuple, set)):
            return [self._make_json_safe(value) for value in data]
        if data is None or isinstance(data, (str, int, float, bool)):
            return data
        return str(data)

    # --- DataFrame (parquet) ---

    def get_df(self, source: str, ticker: str, field: str, ttl: int) -> pd.DataFrame | None:
        path = self._key_path(source, ticker, field, "parquet")
        if self._is_fresh(path, ttl):
            logger.debug("Cache hit: %s/%s/%s", source, ticker, field)
            return pd.read_parquet(path)
        return None

    def set_df(self, source: str, ticker: str, field: str, df: pd.DataFrame) -> None:
        path = self._key_path(source, ticker, field, "parquet")
        df.to_parquet(path)
        self._touch_meta(path)
        logger.debug("Cache set: %s/%s/%s (%d rows)", source, ticker, field, len(df))

    # --- Dict (json) ---

    def get_json(self, source: str, ticker: str, field: str, ttl: int) -> dict | None:
        path = self._key_path(source, ticker, field, "json")
        if self._is_fresh(path, ttl):
            logger.debug("Cache hit: %s/%s/%s", source, ticker, field)
            return json.loads(path.read_text())
        return None

    def set_json(self, source: str, ticker: str, field: str, data: dict) -> None:
        path = self._key_path(source, ticker, field, "json")
        path.write_text(json.dumps(self._make_json_safe(data), default=str))
        self._touch_meta(path)

    # --- List (json) ---

    def get_list(self, source: str, ticker: str, field: str, ttl: int) -> list | None:
        path = self._key_path(source, ticker, field, "json")
        if self._is_fresh(path, ttl):
            return json.loads(path.read_text())
        return None

    def set_list(self, source: str, ticker: str, field: str, data: list) -> None:
        path = self._key_path(source, ticker, field, "json")
        path.write_text(json.dumps(self._make_json_safe(data), default=str))
        self._touch_meta(path)
