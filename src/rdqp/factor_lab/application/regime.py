"""Deterministic trend, volatility, breadth, and risk-regime engine."""

from __future__ import annotations

from collections.abc import Sequence

from rdqp.factor_lab.domain.regime import (
    BreadthRegime,
    RegimeHistory,
    RegimeObservation,
    RegimePoint,
    RegimeThresholds,
    RegimeTransition,
    RiskRegime,
    TrendRegime,
    VolatilityRegime,
)


class RegimeEngine:
    """Classify market observations and track composite regime transitions."""

    def __init__(self, thresholds: RegimeThresholds | None = None) -> None:
        self.thresholds = thresholds or RegimeThresholds()

    def classify(self, observation: RegimeObservation) -> RegimePoint:
        trend = self._trend(observation.trend_return)
        volatility = self._volatility(observation.annualized_volatility)
        breadth = self._breadth(observation.positive_breadth)
        risk, confidence = self._risk(trend, volatility, breadth)
        return RegimePoint(
            observation.timestamp,
            trend,
            volatility,
            breadth,
            risk,
            confidence,
        )

    def history(self, observations: Sequence[RegimeObservation]) -> RegimeHistory:
        ordered = sorted(observations, key=lambda item: item.timestamp)
        points = tuple(self.classify(item) for item in ordered)
        transitions: list[RegimeTransition] = []
        for previous, current in zip(points, points[1:], strict=False):
            if previous.risk is not current.risk:
                transitions.append(RegimeTransition(current.timestamp, previous.risk, current.risk))
        return RegimeHistory(points, tuple(transitions))

    def _trend(self, value: float) -> TrendRegime:
        if value >= self.thresholds.bull_trend:
            return TrendRegime.BULL
        if value <= self.thresholds.bear_trend:
            return TrendRegime.BEAR
        return TrendRegime.NEUTRAL

    def _volatility(self, value: float) -> VolatilityRegime:
        if value <= self.thresholds.low_volatility:
            return VolatilityRegime.LOW
        if value >= self.thresholds.high_volatility:
            return VolatilityRegime.HIGH
        return VolatilityRegime.NORMAL

    def _breadth(self, value: float) -> BreadthRegime:
        if value >= self.thresholds.strong_breadth:
            return BreadthRegime.STRONG
        if value <= self.thresholds.weak_breadth:
            return BreadthRegime.WEAK
        return BreadthRegime.MIXED

    @staticmethod
    def _risk(
        trend: TrendRegime,
        volatility: VolatilityRegime,
        breadth: BreadthRegime,
    ) -> tuple[RiskRegime, float]:
        score = 0
        score += {TrendRegime.BULL: 1, TrendRegime.NEUTRAL: 0, TrendRegime.BEAR: -1}[trend]
        score += {BreadthRegime.STRONG: 1, BreadthRegime.MIXED: 0, BreadthRegime.WEAK: -1}[breadth]
        score += {VolatilityRegime.LOW: 1, VolatilityRegime.NORMAL: 0, VolatilityRegime.HIGH: -1}[
            volatility
        ]
        confidence = abs(score) / 3
        if score >= 2:
            return RiskRegime.RISK_ON, confidence
        if score <= -2:
            return RiskRegime.RISK_OFF, confidence
        return RiskRegime.NEUTRAL, confidence
