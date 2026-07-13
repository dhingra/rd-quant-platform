"""One-shot IBKR snapshot adapter for TWS/IB Gateway paper accounts."""

from __future__ import annotations

from datetime import datetime, timezone

from rdqp.common.exceptions import ProviderUnavailableError
from rdqp.market.domain.models import Tick


def fetch_snapshot_ticks(
    symbols: list[str], host: str, port: int, client_id: int, market_data_type: int = 3
) -> list[Tick]:
    try:
        from ib_insync import IB, Stock
    except ImportError as exc:
        raise ProviderUnavailableError("Install the ibkr extra: pip install -e .[ibkr,ui]") from exc
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, readonly=True, timeout=5)
        ib.reqMarketDataType(market_data_type)
        contracts = [Stock(symbol, "SMART", "USD") for symbol in symbols]
        ib.qualifyContracts(*contracts)
        tickers = [ib.reqMktData(contract, snapshot=True) for contract in contracts]
        ib.sleep(2)
        result: list[Tick] = []
        for symbol, ticker in zip(symbols, tickers, strict=True):
            price = ticker.marketPrice()
            if price and price == price and price > 0:
                result.append(
                    Tick(
                        symbol,
                        datetime.now(timezone.utc),
                        float(price),
                        float(ticker.volume or 0),
                        "ibkr",
                    )
                )
        return result
    finally:
        if ib.isConnected():
            ib.disconnect()
