import os
import time
import pyodbc

password = os.environ["MSSQL_SA_PASSWORD"]
expense_password = os.environ["EXPENSE_DB_PASSWORD"]
settlement_password = os.environ["SETTLEMENT_DB_PASSWORD"]
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
service_accounts = [
    ("expense_db", "expense_service_user", expense_password),
    ("settlement_db", "settlement_service_user", settlement_password),
]

# Create SQL Server logins if they do not already exist
for db_name, username, service_password in service_accounts:
    escaped_password = service_password.replace("'", "''")

    cursor.execute(f"""
        IF SUSER_ID(N'{username}') IS NULL
        BEGIN
            CREATE LOGIN [{username}]
            WITH PASSWORD = N'{escaped_password}';
        END
    """)

for db_name, username, service_password in service_accounts:
    cursor.execute(f"""
        IF DB_ID(N'{db_name}') IS NULL
        BEGIN
            CREATE DATABASE [{db_name}]
        END
    """)
    print(f"Database '{db_name}' ready")
    cursor.execute(f"USE [{db_name}]")

    cursor.execute(f"""
        IF DATABASE_PRINCIPAL_ID(N'{username}') IS NULL
        BEGIN
            CREATE USER [{username}] FOR LOGIN [{username}];
        END

        IF IS_ROLEMEMBER(N'db_owner', N'{username}') <> 1
        BEGIN
            ALTER ROLE db_owner ADD MEMBER [{username}];
        END
    """)

    print(f"User '{username}' configured in '{db_name}'")

conn.close()
print("Database initialization complete")
