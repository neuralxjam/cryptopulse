"""CryptoPulse — Streamlit dashboard.

Reads directly from the DuckDB file that the GitHub Actions ETL pipeline
keeps up-to-date every 6 hours.

Run locally:
    uv run streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CryptoPulse",
    page_icon="📈",
    layout="wide",
)

DUCKDB_PATH = Path(__file__).parent / "cryptopulse.duckdb"


# ---------------------------------------------------------------------------
# Data loading — cached for 5 minutes so rapid reruns don't hammer the file
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (daily_returns, top_movers, price_history) as pandas DataFrames."""
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        daily = con.execute("SELECT * FROM mart_daily_returns").df()
        movers = con.execute("SELECT * FROM mart_top_movers").df()
        history = con.execute("""
            SELECT id AS coin_id, symbol, name AS coin_name,
                   current_price, ingested_at AS snapshot_at
            FROM raw_prices
            ORDER BY ingested_at
        """).df()
    finally:
        con.close()
    return daily, movers, history


daily, movers, history = load_data()

# Derive last-updated from the mart (all rows share the same snapshot_at).
last_updated = pd.Timestamp(daily["snapshot_at"].max()).strftime("%Y-%m-%d %H:%M UTC")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📈 CryptoPulse")
st.caption(
    f"Top-100 crypto prices · Source: CoinGecko (free tier, no API key) · "
    f"Updated every 6 h via GitHub Actions · Last snapshot: **{last_updated}**"
)

st.divider()

# ---------------------------------------------------------------------------
# Section 1 — Top movers
# ---------------------------------------------------------------------------
st.subheader("24-Hour Movers")

gainers = (
    movers[movers["mover_type"] == "top_gainer"]
    .sort_values("price_change_pct_24h", ascending=False)
    .reset_index(drop=True)
)
losers = (
    movers[movers["mover_type"] == "top_loser"]
    .sort_values("price_change_pct_24h")
    .reset_index(drop=True)
)

MOVER_COLS = {
    "symbol": "Ticker",
    "coin_name": "Name",
    "current_price": "Price (USD)",
    "price_change_pct_24h": "24h %",
}

col_gain, col_lose = st.columns(2)

with col_gain:
    st.markdown("### 🚀 Top Gainers")
    st.dataframe(
        gainers[list(MOVER_COLS)].rename(columns=MOVER_COLS),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price (USD)": st.column_config.NumberColumn(format="$%.4f"),
            "24h %": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

with col_lose:
    st.markdown("### 📉 Top Losers")
    st.dataframe(
        losers[list(MOVER_COLS)].rename(columns=MOVER_COLS),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price (USD)": st.column_config.NumberColumn(format="$%.4f"),
            "24h %": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Price history chart
# ---------------------------------------------------------------------------
st.subheader("Price History")

symbols = sorted(daily["symbol"].tolist())
default_idx = symbols.index("btc") if "btc" in symbols else 0
selected_symbol = st.selectbox("Select a coin", symbols, index=default_idx)

coin_history = (
    history[history["symbol"] == selected_symbol]
    .sort_values("snapshot_at")
    .set_index("snapshot_at")
)

if len(coin_history) >= 2:
    st.line_chart(coin_history["current_price"], use_container_width=True)
else:
    st.info(
        "Only one snapshot so far — the chart will fill in as the pipeline runs every 6 hours. "
        "Check back later or trigger the workflow manually from the GitHub Actions tab."
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Full leaderboard
# ---------------------------------------------------------------------------
st.subheader("Full Leaderboard (Top 100 by Market Cap)")

LEADERBOARD_COLS = {
    "symbol": "Ticker",
    "coin_name": "Name",
    "current_price": "Price (USD)",
    "market_cap": "Market Cap",
    "total_volume": "Volume (24h)",
    "price_change_pct_24h": "24h %",
}

st.dataframe(
    daily[list(LEADERBOARD_COLS)].rename(columns=LEADERBOARD_COLS),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Price (USD)": st.column_config.NumberColumn(format="$%.4f"),
        "Market Cap": st.column_config.NumberColumn(format="$%.0f"),
        "Volume (24h)": st.column_config.NumberColumn(format="$%.0f"),
        "24h %": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
