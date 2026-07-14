from datetime import UTC, datetime

from rdqp.analytics.application.factor_ranking import FactorWeights, rank_factors
from rdqp.analytics.domain.models import FactorSnapshot


def snap(symbol: str, roc: float, rvol: float, sector: str) -> FactorSnapshot:
    return FactorSnapshot(
        symbol=symbol,
        timestamp=datetime.now(UTC),
        price=100.0,
        volume=1_000.0,
        sector=sector,
        roc=roc,
        rvol=rvol,
        vwap=99.0,
        vwap_distance=0.01,
        gap=0.0,
        opening_range_high=101.0,
        opening_range_low=98.0,
        opening_range_state="Inside",
    )


def test_factor_ranking_prefers_stronger_symbol() -> None:
    ranked = rank_factors(
        [snap("A", 0.03, 2.0, "Tech"), snap("B", -0.01, 0.5, "Finance")],
        FactorWeights(roc=0.8, rvol=0.2, vwap_distance=0.0, gap=0.0, sector_strength=0.0),
    )
    assert ranked[0].symbol == "A"
    assert ranked[0].rank == 1


def test_factor_weights_require_positive_total() -> None:
    try:
        FactorWeights(0, 0, 0, 0, 0).normalized()
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
