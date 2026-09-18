from pathlib import Path
from typing import NoReturn

import psycopg2  # type: ignore

from config.config import POSTGRES_CONFIG
from etl.logger import get_logger

logger = get_logger(__name__)
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def apply_migrations() -> None:
    """Apply each versioned SQL migration once, within one transaction."""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute("SELECT version FROM schema_migrations")
            applied_versions = {row[0] for row in cursor.fetchall()}
            for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
                if migration_file.name not in applied_versions:
                    logger.info(f"Applying migration {migration_file.name}")
                    cursor.execute(migration_file.read_text(encoding="utf-8"))
                    cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (migration_file.name,))
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database migration failed")
        raise
    finally:
        conn.close()
