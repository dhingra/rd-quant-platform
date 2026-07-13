"""Logging configuration helpers."""

import logging
import logging.config
from pathlib import Path

import yaml


def configure_logging(path: str | Path = "config/logging.yaml", level: str | None = None) -> None:
    config_path = Path(path)
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if level:
            config["root"]["level"] = level.upper()
            for handler in config.get("handlers", {}).values():
                handler["level"] = level.upper()
        logging.config.dictConfig(config)
        return
    logging.basicConfig(
        level=getattr(logging, (level or "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
