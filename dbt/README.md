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
| `dim_currency` | View | Reporting currency |
| `dim_date` | Table | Hourly calendar dimension |
| `fact_crypto_prices` | Table | Price observations (star schema fact) |

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

Set before running:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=crypto_etl
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

In Airflow DAG:

```python
from airflow.providers.dbt.operators.dbt import DbtRunOperator

dbt_run = DbtRunOperator(
    task_id='dbt_run',
    dbt_dir='/opt/airflow/dbt',
)
```

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
