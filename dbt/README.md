# dbt Project: Crypto ETL

This dbt project transforms raw cryptocurrency data into a star schema for analytics.

## Project Structure

```
dbt/
├── dbt_project.yml          # Project configuration
├── profiles.yml              # Database connection
├── packages.yml              # dbt packages (dbt_utils)
├── models/
│   ├── staging/
│   │   ├── stg_raw_coins.sql    # Clean raw data
│   │   └── schema.yml           # Source definitions
│   ├── dimensions/
│   │   ├── dim_coin.sql         # Coin dimension
│   │   ├── dim_category.sql     # Category dimension
│   │   ├── dim_currency.sql     # Currency dimension
│   │   └── dim_date.sql         # Date dimension
│   └── facts/
│       ├── fact_crypto_prices.sql   # Price facts
│       └── schema.yml               # Tests
└── tests/
    └── (custom tests)
```

## How It Works

### Data Flow

```
raw_coins (Python loaded)
     ↓
stg_raw_coins (cleaned)
     ↓
dim_coin, dim_category, dim_currency, dim_date
     ↓
fact_crypto_prices
     ↓
Ready for analytics!
```

### Models

| Model | Type | Description |
|-------|------|-------------|
| `stg_raw_coins` | View | Cleans and validates raw coin data |
| `dim_coin` | Table | Unique coins with category mapping |
| `dim_category` | Table | Distinct categories |
| `dim_currency` | Table | Reporting currency |
| `dim_date` | Table | Hourly calendar dimension |
| `fact_crypto_prices` | Table | Price observations (star schema fact) |

### Target schemas

`profiles.yml` connects to the `public` schema and `dbt_project.yml` appends a
suffix per layer, so dbt builds into `public_staging`, `public_dim` and
`public_fact`. The Python loader writes its own star schema into `public`; the two
sets of tables coexist rather than overwrite each other.

## Running dbt

### Prerequisites

1. Python ETL has loaded data to `raw_coins` table
2. PostgreSQL database is running

### Commands

```bash
# Install dependencies
dbt deps

# Run all models
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate

# Serve documentation
dbt docs serve
```

### Environment Variables

`profiles.yml` and the models read their configuration from the environment:

| Variable | Used by | Purpose |
| --- | --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | `profiles.yml` | Connection |
| `CURRENCY` | `dim_currency`, `fact_crypto_prices` | Reporting currency, same value the Python config uses |
| `PIPELINE_RUN_ID` | `stg_raw_coins` | Stamps each row with the ETL run that produced it; defaults to `manual` |

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=crypto_etl
export CURRENCY=usd
```

### Run Specific Models

```bash
# Run only staging
dbt run --select staging

# Run only dimensions
dbt run --select dimensions

# Run only facts
dbt run --select facts

# Run a specific model
dbt run --select dim_coin
```

## Tests

| Test Type | What it Checks |
|-----------|----------------|
| `unique` | No duplicate values |
| `not_null` | Value is not NULL |
| `relationships` | Foreign key exists |
| `accepted_values` | Value in allowed list |

Run all tests:
```bash
dbt test
```

## Integration with Airflow

dbt runs in its own virtualenv at `/opt/dbt_venv`, because dbt-core and Airflow
both pin `click`, `jinja2` and `protobuf`. The DAG therefore invokes it with a
`BashOperator` rather than a dbt provider operator:

```python
dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command="/opt/dbt_venv/bin/dbt run --project-dir /opt/crypto_etl/dbt",
    env={"PIPELINE_RUN_ID": "{{ ti.xcom_pull(task_ids='run_python_etl') }}"},
    append_env=True,
)
```

`dbt deps` is executed at image build time into `/opt/dbt/dbt_packages`, a path
outside the bind-mounted project directory, so scheduled runs do not depend on
reaching the dbt package hub.

## Documentation

After running `dbt docs generate`:

```bash
dbt docs serve
```

Opens at http://localhost:8081

## Lineage

dbt automatically generates lineage graph showing how models depend on each other:

```
raw_coins → stg_raw_coins → dim_coin → fact_crypto_prices
                      └→ dim_category ↗
                      └→ dim_currency ↗
                      └→ dim_date ↗
```
