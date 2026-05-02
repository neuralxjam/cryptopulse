-- Staging model: clean view on top of raw_prices.
--
-- All marts should reference stg_prices (not raw_prices directly).
-- This is the single place to fix field names if the source schema changes.

select
    id                            as coin_id,
    symbol,
    name                          as coin_name,
    current_price,
    market_cap,
    total_volume,
    price_change_percentage_24h   as price_change_pct_24h,
    last_updated,
    ingested_at                   as snapshot_at
from {{ source('raw', 'raw_prices') }}
