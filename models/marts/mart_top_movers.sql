-- Top 10 gainers + top 10 losers by 24h % change, from the latest snapshot.
-- Uses window functions to rank each direction separately.

with latest_snapshot as (
    select max(snapshot_at) as snapshot_at
    from {{ ref('stg_prices') }}
),

latest_prices as (
    select s.*
    from {{ ref('stg_prices') }} s
    inner join latest_snapshot ls
        on s.snapshot_at = ls.snapshot_at
    where s.price_change_pct_24h is not null
),

ranked as (
    select
        *,
        row_number() over (order by price_change_pct_24h desc) as gain_rank,
        row_number() over (order by price_change_pct_24h asc)  as loss_rank
    from latest_prices
)

select
    coin_id,
    symbol,
    coin_name,
    current_price,
    price_change_pct_24h,
    snapshot_at,
    case
        when gain_rank <= 10 then 'top_gainer'
        when loss_rank <= 10 then 'top_loser'
    end as mover_type
from ranked
where gain_rank <= 10
   or loss_rank <= 10
order by price_change_pct_24h desc
