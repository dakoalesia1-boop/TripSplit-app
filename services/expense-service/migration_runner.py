import os
import time
from pathlib import Path
import pyodbc

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def get_connection():
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        raise RuntimeError("DATABASE_URL is not set")
    for attempt in range(10):
        try:
            return pyodbc.connect(conn_str, timeout=5)
        except pyodbc.Error as e:
            print(f"Connection attempt {attempt + 1}: Could not connect to the database after 10 attempts")
            time.sleep(3)
    raise RuntimeError("Could not connect to the database after 10 attempts")

def ensure_migrations_table(cursor):
    cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sys.tables WHERE name = 'schema_migrations'
        )
        BEGIN
            CREATE TABLE schema_migrations (
                filename NVARCHAR(255) PRIMARY KEY,
                applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            )
        END
    """)

def get_applied_migrations(cursor):
    cursor.execute("SELECT filename FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}

def apply_migrations():
    with get_connection() as conn:
        cursor = conn.cursor()
        ensure_migrations_table(cursor)
        applied = get_applied_migrations(cursor)
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if migration_file.name in applied:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            cursor.execute(sql)
            cursor.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                migration_file.name
            )
            conn.commit()