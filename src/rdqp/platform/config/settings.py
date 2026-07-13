"""Typed configuration and YAML/environment loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from rdqp.common.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class AppSettings:
    name: str = "RD Quant Platform"
    environment: str = "development"
    log_level: str = "INFO"


@dataclass(frozen=True, slots=True)
class SimulatorSettings:
    interval_seconds: float = 1.0
    initial_price: float = 100.0
    volatility: float = 0.002


@dataclass(frozen=True, slots=True)
class YahooSettings:
    interval: str = "1m"
    period: str = "1d"
    poll_seconds: float = 20.0


@dataclass(frozen=True, slots=True)
class IBKRSettings:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 17
    market_data_type: int = 3


@dataclass(frozen=True, slots=True)
class MarketDataSettings:
    provider: str = "simulator"
    watchlist: tuple[str, ...] = ()
    simulator: SimulatorSettings = field(default_factory=SimulatorSettings)
    yahoo: YahooSettings = field(default_factory=YahooSettings)
    ibkr: IBKRSettings = field(default_factory=IBKRSettings)


@dataclass(frozen=True, slots=True)
class AnalyticsSettings:
    roc_window_seconds: int = 120


@dataclass(frozen=True, slots=True)
class ExecutionSettings:
    enabled: bool = False
    broker: str = "paper"
    paper_only: bool = True


@dataclass(frozen=True, slots=True)
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    market_data: MarketDataSettings = field(default_factory=MarketDataSettings)
    analytics: AnalyticsSettings = field(default_factory=AnalyticsSettings)
    execution: ExecutionSettings = field(default_factory=ExecutionSettings)


def _merge_env(data: dict[str, Any], prefix: str = "RDQP") -> dict[str, Any]:
    """Apply environment overrides such as RDQP__MARKET_DATA__PROVIDER=yahoo."""
    for key, value in os.environ.items():
        marker = f"{prefix}__"
        if not key.startswith(marker):
            continue
        path = key[len(marker) :].lower().split("__")
        cursor: dict[str, Any] = data
        for part in path[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[path[-1]] = yaml.safe_load(value)
    return data


def load_settings(path: str | Path = "config/app.yaml") -> Settings:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        raw = _merge_env(raw)
        market = raw.get("market_data", {})
        return Settings(
            app=AppSettings(**raw.get("app", {})),
            market_data=MarketDataSettings(
                provider=str(market.get("provider", "simulator")),
                watchlist=tuple(dict.fromkeys(market.get("watchlist", []))),
                simulator=SimulatorSettings(**market.get("simulator", {})),
                yahoo=YahooSettings(**market.get("yahoo", {})),
                ibkr=IBKRSettings(**market.get("ibkr", {})),
            ),
            analytics=AnalyticsSettings(**raw.get("analytics", {})),
            execution=ExecutionSettings(**raw.get("execution", {})),
        )
    except (TypeError, ValueError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc
