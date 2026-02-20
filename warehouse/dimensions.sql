/* =========================================================
   dimensions.sql (SQL Server)
   Creates dimension tables for star schema
   ========================================================= */

USE PortfolioDriftDW;
GO

/* ---------- dim_date ---------- */
IF OBJECT_ID('dw.dim_date', 'U') IS NOT NULL DROP TABLE dw.dim_date;
GO

CREATE TABLE dw.dim_date (
    date_key        INT         NOT NULL,            -- e.g. 20260220
    [date]          DATE        NOT NULL,
    [year]          SMALLINT    NOT NULL,
    [quarter]       TINYINT     NOT NULL,
    [month]         TINYINT     NOT NULL,
    [day]           TINYINT     NOT NULL,
    day_of_week     TINYINT     NOT NULL,            -- 1=Mon..7=Sun (your convention)
    is_weekend      BIT         NOT NULL,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key),
    CONSTRAINT uq_dim_date_date UNIQUE ([date])
);
GO

/* ---------- dim_risk_profile ---------- */
IF OBJECT_ID('dw.dim_risk_profile', 'U') IS NOT NULL DROP TABLE dw.dim_risk_profile;
GO

CREATE TABLE dw.dim_risk_profile (
    risk_profile_key        INT IDENTITY(1,1) NOT NULL,
    risk_profile_name       VARCHAR(30)       NOT NULL,   -- Conservative/Moderate/Aggressive
    target_equity_weight    DECIMAL(6,5)      NOT NULL,   -- 0.35000
    target_bonds_weight     DECIMAL(6,5)      NOT NULL,   -- 0.55000
    target_cash_weight      DECIMAL(6,5)      NOT NULL,   -- 0.10000
    is_active               BIT               NOT NULL DEFAULT(1),
    created_at              DATETIME2(0)      NOT NULL DEFAULT(SYSDATETIME()),
    CONSTRAINT pk_dim_risk_profile PRIMARY KEY (risk_profile_key),
    CONSTRAINT uq_dim_risk_profile_name UNIQUE (risk_profile_name),
    CONSTRAINT ck_risk_profile_weights_sum CHECK (
        ABS((target_equity_weight + target_bonds_weight + target_cash_weight) - 1.00000) <= 0.00001
    )
);
GO

/* ---------- dim_asset_class ---------- */
IF OBJECT_ID('dw.dim_asset_class', 'U') IS NOT NULL DROP TABLE dw.dim_asset_class;
GO

CREATE TABLE dw.dim_asset_class (
    asset_class_key     INT IDENTITY(1,1) NOT NULL,
    asset_class_name    VARCHAR(20)       NOT NULL,   -- Equity/Bonds/Cash
    CONSTRAINT pk_dim_asset_class PRIMARY KEY (asset_class_key),
    CONSTRAINT uq_dim_asset_class_name UNIQUE (asset_class_name)
);
GO

/* ---------- dim_portfolio ---------- */
IF OBJECT_ID('dw.dim_portfolio', 'U') IS NOT NULL DROP TABLE dw.dim_portfolio;
GO

CREATE TABLE dw.dim_portfolio (
    portfolio_key       INT IDENTITY(1,1) NOT NULL,
    portfolio_id        VARCHAR(50)       NOT NULL,   -- business key from source
    portfolio_name      VARCHAR(120)      NULL,
    advisor_name        VARCHAR(120)      NULL,       -- keep simple now; normalize later if needed
    base_currency       CHAR(3)           NOT NULL DEFAULT('USD'),
    created_at          DATETIME2(0)      NOT NULL DEFAULT(SYSDATETIME()),
    is_active           BIT               NOT NULL DEFAULT(1),
    CONSTRAINT pk_dim_portfolio PRIMARY KEY (portfolio_key),
    CONSTRAINT uq_dim_portfolio_portfolio_id UNIQUE (portfolio_id)
);
GO

/* ---------- Seed basic dimensions ---------- */

-- Asset classes
IF NOT EXISTS (SELECT 1 FROM dw.dim_asset_class)
BEGIN
    INSERT INTO dw.dim_asset_class (asset_class_name)
    VALUES ('Equity'), ('Bonds'), ('Cash');
END
GO

-- Risk profiles
IF NOT EXISTS (SELECT 1 FROM dw.dim_risk_profile)
BEGIN
    INSERT INTO dw.dim_risk_profile (risk_profile_name, target_equity_weight, target_bonds_weight, target_cash_weight)
    VALUES
      ('Conservative', 0.35000, 0.55000, 0.10000),
      ('Moderate',     0.60000, 0.35000, 0.05000),
      ('Aggressive',   0.80000, 0.15000, 0.05000);
END
GO