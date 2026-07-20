from pathlib import Path

import pandas as pd

from etl.load import save_snapshots
from tests.fixtures import SAMPLE_COINS_VALID


def test_save_snapshots_creates_immutable_partitioned_files(tmp_path, monkeypatch):
    monkeypatch.setattr("etl.load.RAW_DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr("etl.load.CURATED_DATA_DIR", str(tmp_path / "curated"))
    fact = pd.DataFrame([{"price_id": "bitcoin_1", "price": 95000.5}])

    raw_path, curated_path = save_snapshots(
        SAMPLE_COINS_VALID,
        fact,
        "11111111-1111-1111-1111-111111111111",
        pd.Timestamp("2025-07-20T10:00:00Z"),
        upload_to_s3=False,
    )

    assert raw_path == Path(tmp_path / "raw/run_date=2025-07-20/run_hour=10/11111111-1111-1111-1111-111111111111.json")
    assert curated_path.exists()
    assert "bitcoin" in raw_path.read_text(encoding="utf-8")
