from unittest.mock import MagicMock

from etl.migrations import apply_migrations


def test_apply_migrations_skips_applied_versions_and_commits_new_files(tmp_path, monkeypatch):
    (tmp_path / "001_applied.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "002_new.sql").write_text("SELECT 2;", encoding="utf-8")
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [("001_applied.sql",)]
    monkeypatch.setattr("etl.migrations.MIGRATIONS_DIR", tmp_path)
    monkeypatch.setattr("etl.migrations.psycopg2.connect", MagicMock(return_value=connection))

    apply_migrations()

    executed = [call.args for call in cursor.execute.call_args_list]
    assert ("SELECT 1;",) not in executed
    assert ("SELECT 2;",) in executed
    assert (
        "INSERT INTO schema_migrations (version) VALUES (%s)",
        ("002_new.sql",),
    ) in executed
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once_with()
