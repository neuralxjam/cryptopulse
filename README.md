# 📈 CryptoPulse

> Daily crypto market ETL pipeline + live dashboard — Python · DuckDB · dbt · Streamlit · GitHub Actions

**[🚀 Live Demo](https://cryptopulse.streamlit.app)** &nbsp;|&nbsp; **[GitHub Actions runs](../../actions)**

---

## What it does

Every **6 hours**, a GitHub Actions cron job:
1. Fetches the top-100 cryptocurrencies by market cap from the [CoinGecko free API](https://www.coingecko.com/en/api) (no API key required)
2. Writes a timestamped Parquet snapshot to `data/raw/`
3. Loads the snapshot into **DuckDB** (idempotent — re-running never duplicates rows)
4. Runs **dbt** to rebuild staging + mart models and assert data-quality tests
5. Commits the updated `cryptopulse.duckdb` back to the repo

The **Streamlit dashboard** reads from the DuckDB marts and shows:
- Top 10 gainers & losers (24h)
- Price history chart with coin picker
- Full top-100 leaderboard sorted by market cap

---

## Architecture

```
GitHub Actions (cron 0 */6 * * *)
  │
  ├─ ingest.py ──► data/raw/prices_<UTC>.parquet
  │                        │
  ├─ load.py ──────────────► cryptopulse.duckdb
  │                                   │
  │              ┌────────────────────┤  raw_prices (table)
  │              │                    │
  ├─ dbt run ────┤         stg_prices (view)
  │              │                    │
  │              ├── mart_daily_returns (table)
  │              └── mart_top_movers   (table)
  │
  └─ git commit ──► pushes cryptopulse.duckdb back to main [skip ci]

Streamlit app reads from the marts → live public dashboard
```

---

## Stack

| Layer | Tech | Why |
|---|---|---|
| Ingest | Python · `httpx` · `pydantic` | Type-validated API fetch |
| Storage | DuckDB (file-based) | Zero-infra OLAP; reads Parquet natively |
| Transform | `dbt-duckdb` (staging → marts) | Industry-standard DE transform pattern |
| Orchestration | GitHub Actions `schedule:` | Free, no Airflow/Prefect needed for v1 |
| Dashboard | Streamlit | Fast Python dashboards; 1-click cloud deploy |
| Tests | dbt `unique` · `not_null` · `accepted_values` | Data contract on every pipeline run |

---

## Local dev quickstart

```bash
# 1. Clone
git clone https://github.com/neuralxjam/cryptopulse
cd cryptopulse

# 2. Install deps (requires uv — https://docs.astral.sh/uv/)
uv sync

# 3. Run the pipeline once
uv run python ingest.py          # fetch from CoinGecko → Parquet
uv run python load.py            # Parquet → DuckDB
uv run dbt run  --profiles-dir . # rebuild marts
uv run dbt test --profiles-dir . # assert data quality

# 4. Launch the dashboard
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Project structure

```
cryptopulse/
├── ingest.py              # CoinGecko fetcher → Parquet writer
├── load.py                # idempotent Parquet → DuckDB loader
├── app.py                 # Streamlit dashboard
├── dbt_project.yml
├── profiles.yml           # DuckDB connection (--profiles-dir . in CI)
├── models/
│   ├── staging/
│   │   ├── stg_prices.sql
│   │   └── schema.yml
│   └── marts/
│       ├── mart_daily_returns.sql
│       ├── mart_top_movers.sql
│       └── schema.yml
├── .github/workflows/etl.yml   # cron pipeline
├── pyproject.toml              # uv project manifest
└── requirements.txt            # pip-compatible export for Streamlit Cloud
```

---

## Known limitations / roadmap

- **Git history grows** — the DuckDB binary is committed on every pipeline run. Fine for a portfolio project; production would use S3/R2.
- **Single-file DuckDB** — no concurrent writes; safe because only one Actions job runs at a time.
- **CoinGecko free tier** — rate-limited; occasional 429s are handled gracefully (next run picks up the data).
