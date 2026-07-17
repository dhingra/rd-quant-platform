from datetime import UTC, datetime, timedelta

import pytest

from rdqp.factor_lab import (
    BreadthRegime,
    RegimeEngine,
    RegimeObservation,
    RegimeThresholds,
    RiskRegime,
    TrendRegime,
    VolatilityRegime,
)


def observation(minutes: int, trend: float, vol: float, breadth: float) -> RegimeObservation:
    return RegimeObservation(
        datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=minutes),
        trend,
        vol,
        breadth,
    )


def test_classifies_risk_on_and_risk_off() -> None:
    engine = RegimeEngine()
    risk_on = engine.classify(observation(0, 0.03, 0.10, 0.80))
    assert risk_on.trend is TrendRegime.BULL
    assert risk_on.volatility is VolatilityRegime.LOW
    assert risk_on.breadth is BreadthRegime.STRONG
    assert risk_on.risk is RiskRegime.RISK_ON
    assert risk_on.confidence == 1.0

    risk_off = engine.classify(observation(1, -0.03, 0.40, 0.20))
    assert risk_off.risk is RiskRegime.RISK_OFF
    assert risk_off.confidence == 1.0


def test_history_sorts_and_detects_transitions() -> None:
    engine = RegimeEngine()
    values = [
        observation(2, -0.03, 0.40, 0.20),
        observation(0, 0.03, 0.10, 0.80),
        observation(1, 0.0, 0.20, 0.50),
    ]
    history = engine.history(values)
    assert [point.risk for point in history.points] == [
        RiskRegime.RISK_ON,
        RiskRegime.NEUTRAL,
        RiskRegime.RISK_OFF,
    ]
    assert len(history.transitions) == 2
    assert history.current is history.points[-1]


def test_threshold_validation_and_observation_validation() -> None:
    with pytest.raises(ValueError):
        RegimeThresholds(bear_trend=0.02, bull_trend=0.01)
    with pytest.raises(ValueError):
        observation(0, 0.0, -0.1, 0.5)
    with pytest.raises(ValueError):
        observation(0, 0.0, 0.2, 1.1)
