"""ML predictor interface and implementations."""

from __future__ import annotations

import pandas as pd

from stockpredict.types import Horizon


class NaiveBaselinePredictor:
    """Always returns 0.5 — used when ML is disabled or no model is trained."""

    def predict_up_probability(self, features: pd.DataFrame, horizon: Horizon) -> float | None:
        return None
