from datetime import UTC, datetime

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.scanners import FilterOperator, ScanDefinition, ScannerEngine, ScannerFilter


def snapshot(symbol: str, roc: float | None, rvol: float | None, price: float = 100.0):
    return FactorSnapshot(
        symbol=symbol,
        timestamp=datetime.now(UTC),
        price=price,
        volume=1000,
        sector="Technology",
        roc=roc,
        rvol=rvol,
        vwap=99.0,
        vwap_distance=(price / 99.0) - 1,
        gap=0.01,
        opening_range_high=101,
        opening_range_low=98,
        opening_range_state="inside",
        rank=1,
    )


def test_scanner_filters_and_sorts():
    engine = ScannerEngine()
    definition = ScanDefinition(
        name="leaders",
        filters=(ScannerFilter("roc_pct", FilterOperator.GTE, 1.0),),
        sort_by="roc_pct",
    )
    result = engine.run(
        definition,
        [snapshot("AAPL", 0.02, 1.2), snapshot("MSFT", 0.01, 2.0), snapshot("NVDA", -0.01, 3.0)],
    )
    assert [match.symbol for match in result.matches] == ["AAPL", "MSFT"]
    assert result.evaluated_count == 3
    assert result.elapsed_ms >= 0


def test_boolean_scanner_filter():
    engine = ScannerEngine()
    definition = ScanDefinition(
        name="above vwap",
        filters=(ScannerFilter("above_vwap", FilterOperator.IS_TRUE),),
    )
    result = engine.run(
        definition, [snapshot("AAPL", 0.01, 1.0, 100), snapshot("MSFT", 0.01, 1.0, 98)]
    )
    assert [match.symbol for match in result.matches] == ["AAPL"]
