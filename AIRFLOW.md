# Running the ETL Pipeline with Airflow

Airflow schedules the pipeline hourly and runs the dbt transformation layer after
the Python ETL finishes.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ airflow (webserver + LocalExecutor scheduler)  →  postgres   │
│   /opt/airflow      Airflow home and dags/                   │
│   /opt/crypto_etl   ETL project on PYTHONPATH                │
│   /opt/dbt_venv     dbt, isolated from Airflow's deps         │
└──────────────────────────────────────────────────────────────┘
```

The ETL code deliberately lives outside `AIRFLOW_HOME`. Airflow owns
`$AIRFLOW_HOME/config` for `airflow_local_settings.py`, and mounting the project's
own `config` package there shadows it.

## DAG

`crypto_etl_pipeline` runs four tasks in sequence:

| Task | Type | Purpose |
| --- | --- | --- |
| `apply_migrations` | Python | Apply pending SQL migrations |
| `run_python_etl` | Python | `main.run_pipeline()`: extract, snapshot, load `raw_coins`, validate, transform, load star schema, audit |
| `dbt_run` | Bash | Rebuild the dbt models from `raw_coins` |
| `dbt_test` | Bash | Assert the dbt data-quality tests |

`run_python_etl` calls the same `run_pipeline()` used by `python main.py`, so the
scheduled and manual paths cannot drift apart. It returns the pipeline run ID via
XCom, which `dbt_run` and `dbt_test` receive as the `PIPELINE_RUN_ID` environment
variable and record on every row they build.

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set:
   - `DB_PASSWORD` - PostgreSQL password
   - `AIRFLOW_FERNET_KEY` - generate with:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
   - `AIRFLOW_SECRET_KEY` - any random string

3. Start the services:
   ```bash
   docker compose up -d --build
   ```

4. Open http://localhost:8080 and sign in with `admin` / `admin`.

## Using Airflow

- Trigger a run with the play button, or wait for the hourly schedule.
- Click the DAG name to inspect per-task logs.
- The dbt tasks log the full `dbt run` and `dbt test` output.

Run the whole DAG once from the command line:

```bash
docker compose exec airflow airflow dags test crypto_etl_pipeline 2026-09-01
```

Run dbt on its own:

```bash
docker compose exec airflow /opt/dbt_venv/bin/dbt run --project-dir /opt/crypto_etl/dbt
docker compose exec airflow /opt/dbt_venv/bin/dbt test --project-dir /opt/crypto_etl/dbt
```

## Stopping Airflow

```bash
docker compose down
```

## Common issues

**Changes to `docker-compose.yml` or the Dockerfile have no effect.** Only
`dags/`, `etl/`, `config/`, `migrations/`, `dbt/` and `data/` are bind mounts. Image
contents, environment variables and mount definitions are fixed when the container
is created, so recreate it rather than restarting it:

```bash
docker compose up -d --build --force-recreate airflow
```

**DAG import errors.** Check the parse error directly instead of reading the UI banner:

```bash
docker compose exec airflow airflow dags list-import-errors
```

**Database connection errors.** Confirm Postgres is healthy with `docker compose ps`
and that `DB_PASSWORD` in `.env` matches the value the database was initialised with.

**Container won't start.** Verify `.env` defines `AIRFLOW_FERNET_KEY` and
`AIRFLOW_SECRET_KEY`, and give Docker at least 4 GB of memory.
