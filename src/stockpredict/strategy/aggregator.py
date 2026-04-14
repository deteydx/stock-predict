"""Aggregate rule-based scores with ML predictions into final verdicts."""

from __future__ import annotations

from stockpredict.types import HorizonScore, Verdict


def aggregate(
    horizon_score: HorizonScore,
    ml_prob_up: float | None = None,
    rule_weight: float = 0.7,
    ml_weight: float = 0.3,
) -> HorizonScore:
    """Combine rule-based score with ML probability to produce final score.

    Args:
        horizon_score: Rule-based HorizonScore
        ml_prob_up: ML model's predicted probability of price going up (0..1),
                    or None if ML is disabled
        rule_weight: Weight for rule-based score (default 0.7)
        ml_weight: Weight for ML prediction (default 0.3)

    Returns:
        Updated HorizonScore with final combined score and verdict.
    """
    if ml_prob_up is None:
        # ML disabled — use rule score directly
        return horizon_score

    # Normalize both to [-1, +1]
    rule_norm = horizon_score.rule_score / 100.0
    ml_norm = (ml_prob_up - 0.5) * 2.0

    # Weighted combination
    combined = rule_weight * rule_norm + ml_weight * ml_norm
    final_score = combined * 100.0

    # Adjust confidence based on ML agreement
    rule_direction = 1 if horizon_score.rule_score > 0 else -1
    ml_direction = 1 if ml_prob_up > 0.5 else -1
    ml_conviction = abs(ml_prob_up - 0.5) * 2  # 0..1

    if rule_direction == ml_direction:
        # Agreement → boost confidence
        confidence = min(1.0, horizon_score.confidence * (1 + 0.2 * ml_conviction))
    else:
        # Disagreement → reduce confidence
        confidence = max(0.0, horizon_score.confidence * (1 - 0.3 * ml_conviction))

    return HorizonScore(
        horizon=horizon_score.horizon,
        raw_score=round(final_score, 1),
        rule_score=horizon_score.rule_score,
        ml_probability_up=ml_prob_up,
        verdict=Verdict.from_score(final_score),
        confidence=round(confidence, 2),
        signals=horizon_score.signals,
        levels=horizon_score.levels,
        caveats=horizon_score.caveats,
    )
