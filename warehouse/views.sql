/* =========================================================
   views.sql (SQL Server)
   Reporting layer views used by Power BI / SSRS
   ========================================================= */

USE PortfolioDriftDW;
GO

/* Drop views if they exist */
IF OBJECT_ID('dw.vw_drift_alerts', 'V') IS NOT NULL DROP VIEW dw.vw_drift_alerts;
IF OBJECT_ID('dw.vw_portfolio_summary', 'V') IS NOT NULL DROP VIEW dw.vw_portfolio_summary;
GO

/* ---------- vw_drift_alerts ---------- */
CREATE VIEW dw.vw_drift_alerts
AS
SELECT
    d.[date],
    p.portfolio_id,
    p.portfolio_name,
    p.advisor_name,
    rp.risk_profile_name,

    f.total_value,
    f.drift_score,
    f.drift_status,
    f.risk_level,

    -- Helpful for visuals
    f.equity_weight, f.bonds_weight, f.cash_weight,
    f.equity_drift,  f.bonds_drift,  f.cash_drift,

    f.created_at
FROM dw.fact_portfolio_daily f
JOIN dw.dim_date d ON f.date_key = d.date_key
JOIN dw.dim_portfolio p ON f.portfolio_key = p.portfolio_key
JOIN dw.dim_risk_profile rp ON f.risk_profile_key = rp.risk_profile_key;
GO

/* ---------- vw_portfolio_summary ---------- */
-- Latest snapshot per portfolio (for advisor overview)
CREATE VIEW dw.vw_portfolio_summary
AS
WITH ranked AS (
    SELECT
        f.*,
        ROW_NUMBER() OVER (PARTITION BY f.portfolio_key ORDER BY f.date_key DESC) AS rn
    FROM dw.fact_portfolio_daily f
)
SELECT
    d.[date] AS as_of_date,
    p.portfolio_id,
    p.portfolio_name,
    p.advisor_name,
    rp.risk_profile_name,

    r.total_value,
    r.drift_score,
    r.drift_status,
    r.risk_level,

    r.equity_weight, r.bonds_weight, r.cash_weight,
    r.equity_drift,  r.bonds_drift,  r.cash_drift
FROM ranked r
JOIN dw.dim_date d ON r.date_key = d.date_key
JOIN dw.dim_portfolio p ON r.portfolio_key = p.portfolio_key
JOIN dw.dim_risk_profile rp ON r.risk_profile_key = rp.risk_profile_key
WHERE r.rn = 1;
GO