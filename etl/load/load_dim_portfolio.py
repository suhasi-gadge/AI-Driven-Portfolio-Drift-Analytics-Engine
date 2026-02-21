import os
import pandas as pd
from sqlalchemy import create_engine, text
from config.config import CONNECTION_STRING

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

def get_engine():
    return create_engine(CONNECTION_STRING, fast_executemany=True)

def main():
    path = os.path.join(RAW_DIR, "portfolios_raw.csv")
    df = pd.read_csv(path)

    df_dim = df[["portfolio_id", "portfolio_name", "advisor_name", "base_currency"]].copy()

    engine = get_engine()

    with engine.begin() as conn:
        # Insert only new portfolio IDs (idempotent)
        insert_sql = text("""
            INSERT INTO dw.dim_portfolio (portfolio_id, portfolio_name, advisor_name, base_currency)
            SELECT :portfolio_id, :portfolio_name, :advisor_name, :base_currency
            WHERE NOT EXISTS (
                SELECT 1 FROM dw.dim_portfolio WHERE portfolio_id = :portfolio_id
            );
        """)

        rows_inserted = 0
        for r in df_dim.to_dict(orient="records"):
            result = conn.execute(insert_sql, r)
            rows_inserted += result.rowcount

        total = conn.execute(text("SELECT COUNT(*) FROM dw.dim_portfolio;")).scalar()

    print(f"✅ Inserted {rows_inserted:,} new portfolios")
    print(f"✅ dim_portfolio total rows now: {total:,}")

if __name__ == "__main__":
    main()