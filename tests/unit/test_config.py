from pathlib import Path

from rdqp.platform.config.settings import load_settings


def test_load_settings_and_deduplicate_watchlist(tmp_path: Path) -> None:
    path = tmp_path / "app.yaml"
    path.write_text(
        """
market_data:
  provider: simulator
  watchlist: [AAPL, AAPL, NVDA]
execution:
  enabled: false
""",
        encoding="utf-8",
    )
    settings = load_settings(path)
    assert settings.market_data.watchlist == ("AAPL", "NVDA")
