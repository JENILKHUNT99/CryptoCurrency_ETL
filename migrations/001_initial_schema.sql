-- Python owns ingestion and the pipeline audit trail. The star schema
-- (dim_* and fact_crypto_prices) is built and owned by dbt, so it is not
-- created here.

CREATE TABLE IF NOT EXISTS pipeline_runs (
    pipeline_run_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    extracted_count INTEGER NOT NULL DEFAULT 0,
    valid_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
