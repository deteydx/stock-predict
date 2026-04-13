"""Weighted scoring engine: signals → horizon score → verdict."""

from __future__ import annotations

from stockpredict.types import HorizonScore, Horizon, Signal, Verdict


def score_horizon(
    horizon: Horizon,
    signals: list[Signal],
    expected_weights: dict[str, float] | None = None,
) -> HorizonScore:
    """Compute a weighted score for a single horizon.

    Score range: [-100, +100]
    """
    active_signals = [s for s in signals if s.value is not None]
    if not active_signals:
        return HorizonScore(
            horizon=horizon,
            raw_score=0,
            rule_score=0,
            verdict=Verdict.HOLD,
            confidence=0.0,
            signals=signals,
            caveats=["No signals available for scoring"],
        )

    total_weight = sum(s.weight for s in active_signals)
    max_possible = total_weight * 2  # Each signal can score ±2

    if max_possible == 0:
        raw = 0.0
    else:
        weighted_sum = sum(s.score * s.weight for s in active_signals)
        raw = (weighted_sum / max_possible) * 100  # Normalize to [-100, +100]

    # Confidence calculation — use config weights as denominator when available
    if expected_weights:
        expected_weight = sum(expected_weights.values())
    else:
        expected_weight = sum(s.weight for s in signals)
    coverage = total_weight / expected_weight if expected_weight > 0 else 0

    # Agreement factor: how many signals agree with the majority direction
    positive = sum(1 for s in active_signals if s.score > 0)
    negative = sum(1 for s in active_signals if s.score < 0)
    total_directional = positive + negative
    if total_directional > 0:
        agreement = max(positive, negative) / total_directional
    else:
        agreement = 0.5

    confidence = coverage * agreement

    # Caveats
    caveats = []
    missing = [s.name for s in signals if s.value is None]
    if expected_weights:
        produced_names = {s.name for s in signals}
        not_produced = [name for name in expected_weights if name not in produced_names]
        missing.extend(not_produced)
    if missing:
        caveats.append(f"Missing signals: {', '.join(missing)}")

    return HorizonScore(
        horizon=horizon,
        raw_score=round(raw, 1),
        rule_score=round(raw, 1),
        verdict=Verdict.from_score(raw),
        confidence=round(confidence, 2),
        signals=signals,
        caveats=caveats,
    )
