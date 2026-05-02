"""Pull top-100 crypto prices from CoinGecko and write a Parquet snapshot.

Usage:
    uv run python ingest.py

Output:
    data/raw/prices_<UTC-timestamp>.parquet
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 100,
    "page": 1,
}
RAW_DIR = Path("data/raw")


class Coin(BaseModel):
    """The subset of fields we keep from CoinGecko's /coins/markets response."""

    id: str
    symbol: str
    name: str
    current_price: float | None = None
    market_cap: int | None = None
    total_volume: float | None = None
    price_change_percentage_24h: float | None = None
    last_updated: datetime


def fetch_top_100() -> list[Coin]:
    """GET top-100 coins by market cap; validate each row with the Coin model."""
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(COINGECKO_URL, params=PARAMS)
        resp.raise_for_status()
    return [Coin.model_validate(item) for item in resp.json()]


def write_parquet(coins: list[Coin], ingested_at: datetime) -> Path:
    """Write the coins list to a timestamped Parquet file under data/raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = [{**c.model_dump(), "ingested_at": ingested_at} for c in coins]
    table = pa.Table.from_pylist(rows)
    path = RAW_DIR / f"prices_{ingested_at.strftime('%Y%m%dT%H%M%SZ')}.parquet"
    pq.write_table(table, path)
    return path


def main() -> None:
    ingested_at = datetime.now(timezone.utc)
    coins = fetch_top_100()
    path = write_parquet(coins, ingested_at)
    print(f"wrote {len(coins)} rows -> {path}")


if __name__ == "__main__":
    main()
