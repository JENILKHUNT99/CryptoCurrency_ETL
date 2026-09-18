# Crypto ETL - Improvement Summary

## Completed Tasks ✅

- [x] **SQL Injection** - Fixed using `psycopg2.sql.Identifier` in `etl/load.py`
- [x] **Pagination** - Analyzed: Not needed (only 101 specific coins requested)
- [x] **Zero Price Bug** - Analyzed: Code is correct (`<= 0` rejects zero)
- [x] **Duplicate Migration** - Removed duplicate CREATE TABLE from migration 002
- [x] **Airflow orchestration** - 4-task DAG: apply_migrations → run_python_etl → dbt_run → dbt_test
- [x] **dbt transformation layer** - dbt owns the star schema; models + 28 data tests
- [x] **ETL → ELT refactor** - Removed the pandas transform + star-schema load; Python is now
      ingestion-only (extract → validate → load raw_coins), dbt does the transform

## Core Concepts Learned ✅

- [x] Raw Snapshot - Preserves the original API response as the immutable record
- [x] Audit Table (pipeline_runs) - Tracks pipeline execution status and metrics
- [x] Migrations - Version-controlled database schema changes, runs once
- [x] Docker - Containerized Airflow + PostgreSQL with docker-compose
- [x] Tests - pytest validates each component, fixtures provide test data
- [x] ETL vs ELT - Transform-before-load vs load-raw-then-transform-in-warehouse

## Future Improvements (Optional)

### Data source reliability — missing coins
Only 94 of the 101 configured coin IDs come back from CoinGecko; the rest are
dropped silently by the API (renamed slugs, delisted coins, or temporary gaps).
- [ ] Log which requested coin IDs are missing from the API response (observability)
- [ ] Fix known rebranded slugs in `config/coins.py` (e.g. `elrond-erd-2` → `multiversx`,
      `fetch-ai` → current slug) and prune dead tokens
- [ ] Decide on a policy: warn-and-continue (current) vs fail if too many IDs go missing

### Code Quality
- [x] Add type hints to all functions
- [ ] Add docstrings to all modules  
- [x] Fix inconsistent spacing in `REQUIRED_FIELDS` list

### Design Improvements
- [ ] Log warning when coins get category_id=99 ("Other")
- [ ] Use "Privacy" category (id=13) or remove it
- [ ] Add dead letter storage for rejected records

### Feature Enhancements
- [ ] Add Great Expectations for data quality
- [ ] Add API key support in config
- [ ] Add `dbt docs generate` for the lineage graph
