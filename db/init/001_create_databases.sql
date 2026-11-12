IF DB_ID('expense_db') IS NULL
BEGIN
    CREATE DATABASE expense_db;
END;
GO

IF DB_ID('settlement_db') IS NULL
BEGIN
    CREATE DATABASE settlement_db;
END;
GO