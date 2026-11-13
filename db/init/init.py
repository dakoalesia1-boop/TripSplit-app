import os
import time
import pyodbc

password = os.getenv("MSSQL_SA_PASSWORD", "YourStrongPassword123!")
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=sqlserver,1433;"
    f"DATABASE=master;"
    f"UID=sa;"
    f"PWD={password};"
    f"Encrypt=no;"
    f"TrustServerCertificate=yes"
)

for attempt in range(20):
    try:
        conn = pyodbc.connect(conn_str, timeout=5, autocommit=True)
        print("Connected to SQL Server")
        break
    except pyodbc.Error as e:
        print(f"Waiting for SQL Server... attempt {attempt + 1}: {e}")
        time.sleep(3)
else:
    raise RuntimeError("Could not connect to SQL Server after 20 attempts")

cursor = conn.cursor()

for db_name in ["expense_db", "settlement_db"]:
    cursor.execute(f"""
        IF DB_ID(N'{db_name}') IS NULL
        BEGIN
            CREATE DATABASE [{db_name}]
        END
    """)
    print(f"Database '{db_name}' ready")

conn.close()
print("Database initialization complete")