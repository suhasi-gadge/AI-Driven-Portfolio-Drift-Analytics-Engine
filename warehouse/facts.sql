/* =========================================================
   facts.sql (SQL Server)
   Creates fact table (portfolio-day grain) + audit table
   ========================================================= */

USE PortfolioDriftDW;
GO

/* ---------- etl_run_audit ---------- */
IF OBJECT_ID('dw.etl_run_audit', 'U') IS NOT NULL DROP TABLE dw.etl_run_audit;
GO

CREATE TABLE dw.etl_run_audit (
    etl_run_id          BIGINT IDENTITY(1,1) NOT NULL,
    run_start_ts        DATETIME2(0)         NOT NULL DEFAULT(SYSDATETIME()),
    run_end_ts          DATETIME2(0)         NULL,
    [status]            VARCHAR(20)          NOT NULL DEFAULT('RUNNING'), -- RUNNING/SUCCESS/FAIL
    records_extracted   INT                  NULL,
    records_loaded      INT                  NULL,
    error_message       NVARCHAR(2000)       NULL,
    CONSTRAINT pk_etl_run_audit PRIMARY KEY (etl_run_id),
    CONSTRAINT ck_etl_run_status CHECK ([status] IN ('RUNNING', 'SUCCESS', 'FAIL'))
);
GO

/* ---------- fact_portfolio_daily ---------- */
IF OBJECT_ID('dw.fact_portfolio_daily', 'U') IS NOT NULL DROP TABLE dw.fact_portfolio_daily;
GO

CREATE TABLE dw.fact_portfolio_daily (
    portfolio_daily_id  BIGINT IDENTITY(1,1) NOT NULL,

    -- Grain: 1 row per portfolio per day
    portfolio_key       INT                 NOT NULL,
    date_key            INT                 NOT NULL,
    risk_profile_key    INT                 NOT NULL,

    -- Measures (values)
    total_value         DECIMAL(19,4)       NOT NULL,
    equity_value        DECIMAL(19,4)       NOT NULL,
    bonds_value         DECIMAL(19,4)       NOT NULL,
    cash_value          DECIMAL(19,4)       NOT NULL,

    -- Weights (0..1)
    equity_weight       DECIMAL(10,7)       NOT NULL,
    bonds_weight        DECIMAL(10,7)       NOT NULL,
    cash_weight         DECIMAL(10,7)       NOT NULL,

    -- Drift by class (abs difference)
    equity_drift        DECIMAL(10,7)       NOT NULL,
    bonds_drift         DECIMAL(10,7)       NOT NULL,
    cash_drift          DECIMAL(10,7)       NOT NULL,

    -- Drift score and status
    drift_score         DECIMAL(10,7)       NOT NULL,   -- MAX of drifts
    drift_status        VARCHAR(20)         NOT NULL,   -- Normal/Watch/Rebalance Flag
    risk_level          VARCHAR(20)         NOT NULL,   -- Stable/Elevated/High (pre-ML)

    -- Governance
    data_quality_flag   BIT                 NOT NULL DEFAULT(1),
    etl_run_id          BIGINT              NULL,
    created_at          DATETIME2(0)        NOT NULL DEFAULT(SYSDATETIME()),

    CONSTRAINT pk_fact_portfolio_daily PRIMARY KEY (portfolio_daily_id),

    CONSTRAINT fk_fpd_portfolio FOREIGN KEY (portfolio_key) REFERENCES dw.dim_portfolio(portfolio_key),
    CONSTRAINT fk_fpd_date      FOREIGN KEY (date_key)      REFERENCES dw.dim_date(date_key),
    CONSTRAINT fk_fpd_risk      FOREIGN KEY (risk_profile_key) REFERENCES dw.dim_risk_profile(risk_profile_key),
    CONSTRAINT fk_fpd_etlrun    FOREIGN KEY (etl_run_id)    REFERENCES dw.etl_run_audit(etl_run_id),

    -- Ensure no duplicate daily snapshots for same portfolio/day
    CONSTRAINT uq_fact_portfolio_day UNIQUE (portfolio_key, date_key),

    -- Basic sanity checks
    CONSTRAINT ck_values_nonnegative CHECK (
        total_value >= 0 AND equity_value >= 0 AND bonds_value >= 0 AND cash_value >= 0
    ),
    CONSTRAINT ck_weights_range CHECK (
        equity_weight BETWEEN 0 AND 1 AND
        bonds_weight BETWEEN 0 AND 1 AND
        cash_weight  BETWEEN 0 AND 1
    ),
    CONSTRAINT ck_weights_sum CHECK (
        ABS((equity_weight + bonds_weight + cash_weight) - 1.0000000) <= 0.00001
    ),
    CONSTRAINT ck_drift_status CHECK (drift_status IN ('Normal', 'Watch', 'Rebalance Flag')),
    CONSTRAINT ck_risk_level CHECK (risk_level IN ('Stable', 'Elevated', 'High'))
);
GO

/* ---------- Performance Indexes ---------- */
-- Common filters: by date, by drift_status, by advisor (via portfolio), by risk profile
CREATE INDEX ix_fpd_date ON dw.fact_portfolio_daily(date_key);
CREATE INDEX ix_fpd_portfolio ON dw.fact_portfolio_daily(portfolio_key);
CREATE INDEX ix_fpd_risk_profile ON dw.fact_portfolio_daily(risk_profile_key);
CREATE INDEX ix_fpd_drift_status ON dw.fact_portfolio_daily(drift_status);
GO