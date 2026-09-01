# Running the ETL Pipeline with Airflow

Airflow automates the ETL pipeline to run on a schedule.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Airflow Services                       │
│                                                           │
│  airflow-scheduler (runs DAGs) ←→ postgres (database)    │
│  airflow-webserver (UI at :8080)                         │
└─────────────────────────────────────────────────────────┘
```

## Setup

1. Copy .env.example to .env:
   ```bash
   cp .env.example .env
   ```

2. Edit .env and set:
   - `DB_PASSWORD` - Your PostgreSQL password
   - `AIRFLOW_FERNET_KEY` - Generate with:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
   - `AIRFLOW_SECRET_KEY` - Any random string

3. Start Airflow:
   ```bash
   docker compose up -d
   ```

4. Wait for services to be healthy (about 1-2 minutes)

5. Open Airflow UI:
   - URL: http://localhost:8080
   - Username: airflow
   - Password: airflow

## Using Airflow

1. **Enable the DAG**
   - Go to DAGs page
   - Find `crypto_etl_pipeline`
   - Toggle the switch to enable

2. **Trigger a Run**
   - Click the "Play" button next to the DAG
   - Or wait for hourly schedule

3. **View Results**
   - Click on the DAG name
   - Select a run to see task details
   - Check logs for each task

## Stopping Airflow

```bash
docker compose down
```

## Common Issues

### Container won't start
- Check .env has all required variables
- Check Docker has enough memory (4GB+)

### DAG not appearing
- Wait 30 seconds for scheduler to pick it up
- Check logs: `docker compose logs airflow-scheduler`

### Database connection errors
- Ensure postgres is healthy: `docker compose ps`
- Check DB_PASSWORD matches in all services
