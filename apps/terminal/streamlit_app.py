"""Thin Streamlit bootstrap for Sprint 1.

No analytics or trading rules are computed here. The page verifies configuration,
plugin discovery, and package boundaries while Sprint 2 migrates the dashboard.
"""

from pathlib import Path

import streamlit as st

from rdqp.platform.config.settings import load_settings
from rdqp.platform.plugins.registry import registry

# Import adapters so decorator-based registration occurs.
import rdqp.datasources.ibkr.provider  # noqa: F401,E402
import rdqp.datasources.simulator.provider  # noqa: F401,E402
import rdqp.datasources.yahoo.provider  # noqa: F401,E402

st.set_page_config(page_title="RD Quant Platform", layout="wide")
settings = load_settings(Path("config/app.yaml"))

st.title("RD Quant Platform")
st.caption("v0.1.0-alpha · Sprint 1 foundation")

col1, col2, col3 = st.columns(3)
col1.metric("Configured provider", settings.market_data.provider.upper())
col2.metric("Watchlist symbols", len(settings.market_data.watchlist))
col3.metric("Execution", "DISABLED" if not settings.execution.enabled else "ENABLED")

st.subheader("Architecture bootstrap")
st.success("Configuration, event bus, dependency injection, provider ports, and plugin registry loaded.")

st.subheader("Registered market-data adapters")
st.dataframe(
    [{"adapter": name, "status": "registered"} for name in registry.list("market_data")],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Configured watchlist")
st.write(", ".join(settings.market_data.watchlist))

st.info("The production dashboard is migrated in Sprint 2. This page intentionally contains no trading logic.")
