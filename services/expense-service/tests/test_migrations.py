
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

SERVICE_DIR = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "expense_migration_runner",
    SERVICE_DIR / "migration_runner.py"
)
migration_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_runner)


def test_normalize_expense_categories_migration_exists():
    migration = (
        SERVICE_DIR
        / "migrations"
        / "002_normalize_expense_categories.sql"
    )

    assert migration.exists()

    sql = migration.read_text(encoding="utf-8")

    assert "UPDATE expenses" in sql
    assert "LTRIM(RTRIM(category))" in sql
    assert "'General'" in sql


def test_apply_migrations_skips_already_applied(monkeypatch):
    conn = MagicMock()
    cursor = MagicMock()

    conn.__enter__.return_value = conn
    conn.cursor.return_value = cursor

    cursor.fetchall.return_value = [
        ("001_init.sql",),
        ("002_normalize_expense_categories.sql",)
    ]

    monkeypatch.setattr(
        migration_runner,
        "get_connection",
        lambda: conn
    )

    migration_runner.apply_migrations()

    executed_sql = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    assert not any(
        "UPDATE expenses" in sql
        for sql in executed_sql
    )
