/* =========================================================
   schema.sql  (SQL Server)
   Creates database and schema for the portfolio drift engine
   ========================================================= */

-- Create DB (run once). Comment out if DB already exists.
IF DB_ID('PortfolioDriftDW') IS NULL
BEGIN
    CREATE DATABASE PortfolioDriftDW;
END
GO

USE PortfolioDriftDW;
GO

-- Create a dedicated schema
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dw')
BEGIN
    EXEC('CREATE SCHEMA dw');
END
GO