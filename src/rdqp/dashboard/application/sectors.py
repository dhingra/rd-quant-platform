"""Small default sector catalogue for the starter watchlist."""

SECTORS: dict[str, str] = {
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Semiconductors",
    "AMZN": "Consumer", "META": "Communication", "GOOGL": "Communication",
    "TSLA": "Consumer", "AMD": "Semiconductors", "NFLX": "Communication",
    "JPM": "Financials", "CLS": "Technology", "CRDO": "Semiconductors",
    "MU": "Semiconductors", "SPCX": "Other", "PLTR": "Software",
    "CRWD": "Software", "INTC": "Semiconductors",
}


def sector_for(symbol: str) -> str:
    return SECTORS.get(symbol.upper(), "Other")
