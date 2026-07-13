"""Parameter robustness and stability analysis."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev

from rdqp.research.domain.models import OptimizationResult


@dataclass(frozen=True, slots=True)
class RobustnessSummary:
    trial_count: int
    positive_trials: int
    positive_ratio: float
    mean_score: float | None
    score_stddev: float | None
    top_decile_mean: float | None
    stability_score: int


def analyze_robustness(result: OptimizationResult) -> RobustnessSummary:
    scores = [trial.score for trial in result.trials if trial.score not in {float("inf"), float("-inf")}]
    if not scores:
        return RobustnessSummary(0, 0, 0.0, None, None, None, 0)
    ordered = sorted(scores, reverse=True)
    top_count = max(1, len(ordered) // 10)
    positive = sum(score > 0 for score in scores)
    mean_score = fmean(scores)
    stddev = pstdev(scores) if len(scores) > 1 else 0.0
    dispersion_penalty = 0.0 if mean_score == 0 else min(1.0, abs(stddev / mean_score))
    stability = round(max(0.0, min(1.0, positive / len(scores) * (1.0 - dispersion_penalty))) * 100)
    return RobustnessSummary(
        trial_count=len(scores),
        positive_trials=positive,
        positive_ratio=positive / len(scores),
        mean_score=mean_score,
        score_stddev=stddev,
        top_decile_mean=fmean(ordered[:top_count]),
        stability_score=stability,
    )
