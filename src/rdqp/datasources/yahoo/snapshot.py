"""Recent Yahoo bars normalized as ticks for interactive applications."""

from __future__ import annotations

from datetime import timezone

from rdqp.common.exceptions import ProviderUnavailableError
from rdqp.market.domain.models import Tick


def fetch_latest_ticks(
    symbols: list[str], period: str = "1d", interval: str = "1m", max_bars: int = 240
) -> list[Tick]:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ProviderUnavailableError("Install the yahoo extra: pip install -e .[yahoo,ui]") from exc
    if not symbols:
        return []
    frame = yf.download(
        symbols, period=period, interval=interval, group_by="ticker", progress=False,
        threads=True, auto_adjust=False,
    )
    ticks: list[Tick] = []
    for symbol in symbols:
        try:
            sf = frame[symbol] if len(symbols) > 1 else frame
            valid = sf.dropna(subset=["Close"]).tail(max_bars)
            for timestamp, row in valid.iterrows():
                dt = timestamp.to_pydatetime()
                dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
                ticks.append(
                    Tick(symbol, dt, float(row["Close"]), float(row.get("Volume", 0)), "yahoo")
                )
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return ticks
