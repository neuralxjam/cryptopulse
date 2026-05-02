-- Latest price + 24h return for every coin, from the most recent snapshot.
-- Materialized as a table so the dashboard reads instantly.

with latest_snapshot as (
    select max(snapshot_at) as snapshot_at
    from {{ ref('stg_prices') }}
),

latest_prices as (
    select s.*
    from {{ ref('stg_prices') }} s
    inner join latest_snapshot ls
        on s.snapshot_at = ls.snapshot_at
)

select
    coin_id,
    symbol,
    coin_name,
    current_price,
    market_cap,
    total_volume,
    price_change_pct_24h,
    last_updated,
    snapshot_at
from latest_prices
order by market_cap desc nulls last
