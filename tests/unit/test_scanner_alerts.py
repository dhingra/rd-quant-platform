from datetime import UTC, datetime

from rdqp.scanners.application.alerts import AlertEngine
from rdqp.scanners.domain.models import ScanDefinition, ScanMatch, ScanResult


def result(symbols):
    definition = ScanDefinition(name="Momentum", filters=())
    matches = tuple(
        ScanMatch(symbol=s, timestamp=datetime.now(UTC), values={"symbol": s}) for s in symbols
    )
    return ScanResult(definition, matches, len(matches), 0.1, datetime.now(UTC))


def test_alerts_only_for_new_entries():
    engine = AlertEngine()
    assert {a.symbol for a in engine.evaluate(result(["AAPL", "MSFT"]))} == {"AAPL", "MSFT"}
    assert engine.evaluate(result(["AAPL", "MSFT"])) == ()
    assert [a.symbol for a in engine.evaluate(result(["AAPL", "NVDA"]))] == ["NVDA"]
