"""Load Parquet snapshots from data/raw/ into DuckDB.

Idempotent: re-running on the same files inserts zero new rows because
(id, ingested_at) is a composite primary key on raw_prices.

Usage:
    uv run python load.py

Output:
    cryptopulse.duckdb (DuckDB file in repo root, gitignored)
"""
from __future__ import annotations

from pathlib import Path

import duckdb

DUCKDB_PATH = Path("cryptopulse.duckdb")
RAW_GLOB = "data/raw/*.parquet"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_prices (
    id                            VARCHAR     NOT NULL,
    symbol                        VARCHAR     NOT NULL,
    name                          VARCHAR     NOT NULL,
    current_price                 DOUBLE,
    market_cap                    BIGINT,
    total_volume                  DOUBLE,
    price_change_percentage_24h   DOUBLE,
    last_updated                  TIMESTAMPTZ NOT NULL,
    ingested_at                   TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, ingested_at)
)
"""

# INSERT OR IGNORE skips rows that would violate the PK — that's our idempotency.
INSERT_SQL = f"""
INSERT OR IGNORE INTO raw_prices
SELECT
    id,
    symbol,
    name,
    current_price,
    market_cap,
    total_volume,
    price_change_percentage_24h,
    last_updated,
    ingested_at
FROM read_parquet('{RAW_GLOB}')
"""


def load() -> None:
    snapshot_files = sorted(Path().glob(RAW_GLOB))
    if not snapshot_files:
        print(f"no parquet files matched {RAW_GLOB}; run ingest.py first")
        return

    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        con.execute(CREATE_TABLE_SQL)

        before = con.execute("SELECT COUNT(*) FROM raw_prices").fetchone()[0]
        con.execute(INSERT_SQL)
        after = con.execute("SELECT COUNT(*) FROM raw_prices").fetchone()[0]

        snapshot_count = con.execute(
            "SELECT COUNT(DISTINCT ingested_at) FROM raw_prices"
        ).fetchone()[0]

        print(
            f"matched {len(snapshot_files)} parquet file(s) -> "
            f"appended {after - before} new row(s) "
            f"(table now: {after} rows across {snapshot_count} snapshot(s))"
        )
    finally:
        con.close()


if __name__ == "__main__":
    load()
