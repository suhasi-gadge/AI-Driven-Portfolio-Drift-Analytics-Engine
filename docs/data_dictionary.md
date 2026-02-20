# Data Dictionary — Portfolio Drift Analytics Engine (SQL Server)

This document defines the tables, columns, data types, and business meaning for the `PortfolioDriftDW` warehouse (schema: `dw`).

---

## dw.dim_date
**Purpose:** Calendar dimension for time-series analysis and reporting.

| Column | Data Type | Key | Description |
|---|---|---|---|
| date_key | INT | PK | Surrogate key in `YYYYMMDD` format (e.g., 20260220). |
| date | DATE | UQ | Actual calendar date. |
| year | SMALLINT |  | Calendar year (e.g., 2026). |
| quarter | TINYINT |  | Calendar quarter (1–4). |
| month | TINYINT |  | Calendar month (1–12). |
| day | TINYINT |  | Day of month (1–31). |
| day_of_week | TINYINT |  | Day of week (convention defined by ETL, e.g., 1=Mon..7=Sun). |
| is_weekend | BIT |  | Weekend flag based on `day_of_week`. |

---

## dw.dim_risk_profile
**Purpose:** Defines portfolio risk profiles and their target allocation weights.

| Column | Data Type | Key | Description |
|---|---|---|---|
| risk_profile_key | INT IDENTITY | PK | Surrogate key for risk profile. |
| risk_profile_name | VARCHAR(30) | UQ | Risk profile name: Conservative, Moderate, Aggressive. |
| target_equity_weight | DECIMAL(6,5) |  | Target weight for Equity asset class (0–1). |
| target_bonds_weight | DECIMAL(6,5) |  | Target weight for Bonds asset class (0–1). |
| target_cash_weight | DECIMAL(6,5) |  | Target weight for Cash asset class (0–1). |
| is_active | BIT |  | Indicates whether profile is active for assignment. |
| created_at | DATETIME2(0) |  | Record creation timestamp. |

**Constraints:** Target weights must sum to ~1.0.

---

## dw.dim_asset_class
**Purpose:** Reference dimension for asset class grouping.

| Column | Data Type | Key | Description |
|---|---|---|---|
| asset_class_key | INT IDENTITY | PK | Surrogate key for asset class. |
| asset_class_name | VARCHAR(20) | UQ | Asset class name: Equity, Bonds, Cash. |

> Note: In later phases (Option 2), a `dim_asset` table can be added for ticker-level holdings.

---

## dw.dim_portfolio
**Purpose:** Portfolio master dimension representing a client portfolio/account.

| Column | Data Type | Key | Description |
|---|---|---|---|
| portfolio_key | INT IDENTITY | PK | Surrogate portfolio key. |
| portfolio_id | VARCHAR(50) | UQ | Business identifier for portfolio (from source data). |
| portfolio_name | VARCHAR(120) |  | Human-readable portfolio name (optional). |
| advisor_name | VARCHAR(120) |  | Advisor associated with the portfolio (denormalized for simplicity). |
| base_currency | CHAR(3) |  | Portfolio currency (default: USD). |
| created_at | DATETIME2(0) |  | Record creation timestamp. |
| is_active | BIT |  | Active portfolio flag. |

---

## dw.etl_run_audit
**Purpose:** Tracks ETL runs for governance, monitoring, and troubleshooting.

| Column | Data Type | Key | Description |
|---|---|---|---|
| etl_run_id | BIGINT IDENTITY | PK | Unique ID for each ETL pipeline run. |
| run_start_ts | DATETIME2(0) |  | ETL run start timestamp. |
| run_end_ts | DATETIME2(0) |  | ETL run end timestamp. |
| status | VARCHAR(20) |  | RUNNING, SUCCESS, or FAIL. |
| records_extracted | INT |  | Number of records extracted (optional). |
| records_loaded | INT |  | Number of records loaded (optional). |
| error_message | NVARCHAR(2000) |  | Error details when run fails. |

---

## dw.fact_portfolio_daily
**Grain:** **1 row per portfolio per day** (daily portfolio snapshot).  
**Purpose:** Stores daily portfolio valuation, allocation weights, drift metrics, and alert/risk classifications.

| Column | Data Type | Key | Description |
|---|---|---|---|
| portfolio_daily_id | BIGINT IDENTITY | PK | Surrogate key for the daily snapshot record. |
| portfolio_key | INT | FK | Links to `dw.dim_portfolio`. |
| date_key | INT | FK | Links to `dw.dim_date`. |
| risk_profile_key | INT | FK | Links to `dw.dim_risk_profile`. |
| total_value | DECIMAL(19,4) |  | Total portfolio market value on date. |
| equity_value | DECIMAL(19,4) |  | Total market value of Equity holdings. |
| bonds_value | DECIMAL(19,4) |  | Total market value of Bonds holdings. |
| cash_value | DECIMAL(19,4) |  | Total market value of Cash holdings. |
| equity_weight | DECIMAL(10,7) |  | Equity allocation weight (0–1). |
| bonds_weight | DECIMAL(10,7) |  | Bonds allocation weight (0–1). |
| cash_weight | DECIMAL(10,7) |  | Cash allocation weight (0–1). |
| equity_drift | DECIMAL(10,7) |  | Absolute difference: `abs(equity_weight - target_equity_weight)`. |
| bonds_drift | DECIMAL(10,7) |  | Absolute difference: `abs(bonds_weight - target_bonds_weight)`. |
| cash_drift | DECIMAL(10,7) |  | Absolute difference: `abs(cash_weight - target_cash_weight)`. |
| drift_score | DECIMAL(10,7) |  | Portfolio drift score = `max(equity_drift, bonds_drift, cash_drift)`. |
| drift_status | VARCHAR(20) |  | Drift alert category: Normal / Watch / Rebalance Flag. |
| risk_level | VARCHAR(20) |  | Baseline risk: Stable / Elevated / High (pre-ML). |
| data_quality_flag | BIT |  | Indicates whether validation checks passed for this record. |
| etl_run_id | BIGINT | FK | Links to `dw.etl_run_audit` for lineage. |
| created_at | DATETIME2(0) |  | Load timestamp for this fact row. |

**Constraints & Rules:**
- Uniqueness enforced on `(portfolio_key, date_key)` to prevent duplicate daily snapshots.
- Weight sum must be ~1.0 and weights must be between 0 and 1.
- Values must be non-negative.

---

## dw.vw_drift_alerts
**Purpose:** Reporting view for dashboards showing drift alerts by date and portfolio.

**Source:** Joins `fact_portfolio_daily` with `dim_date`, `dim_portfolio`, `dim_risk_profile`.

---

## dw.vw_portfolio_summary
**Purpose:** Reporting view returning latest daily snapshot per portfolio (used for Advisor Overview).

**Logic:** Uses `ROW_NUMBER()` to rank snapshots by date per portfolio and returns the most recent row.