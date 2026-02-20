import logging
from sqlalchemy import create_engine, text
from config.config import CONNECTION_STRING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def get_engine():
    # fast_executemany speeds bulk inserts later
    return create_engine(CONNECTION_STRING, fast_executemany=True)

def create_etl_run(conn) -> int:
    result = conn.execute(text("""
        INSERT INTO dw.etl_run_audit (status)
        OUTPUT INSERTED.etl_run_id
        VALUES ('RUNNING');
    """))
    return int(result.scalar())

def finish_etl_run(conn, etl_run_id: int, status: str, records_extracted=None, records_loaded=None, error_message=None):
    conn.execute(text("""
        UPDATE dw.etl_run_audit
        SET status = :status,
            run_end_ts = SYSDATETIME(),
            records_extracted = COALESCE(:records_extracted, records_extracted),
            records_loaded = COALESCE(:records_loaded, records_loaded),
            error_message = :error_message
        WHERE etl_run_id = :etl_run_id;
    """), {
        "status": status,
        "records_extracted": records_extracted,
        "records_loaded": records_loaded,
        "error_message": error_message,
        "etl_run_id": etl_run_id
    })

def main():
    logging.info("Starting ETL pipeline (Day 3 connectivity + audit test)")
    engine = get_engine()
    etl_run_id = None

    try:
        with engine.begin() as conn:
            # Start audit row
            etl_run_id = create_etl_run(conn)
            logging.info(f"ETL run started. etl_run_id={etl_run_id}")

            # Connectivity smoke test queries
            dim_count = conn.execute(text("SELECT COUNT(*) FROM dw.dim_portfolio")).scalar()
            rp_count = conn.execute(text("SELECT COUNT(*) FROM dw.dim_risk_profile")).scalar()
            logging.info(f"dim_portfolio rows: {dim_count}")
            logging.info(f"dim_risk_profile rows: {rp_count}")

            # Finish audit row
            finish_etl_run(conn, etl_run_id, status="SUCCESS", records_extracted=0, records_loaded=0)
            logging.info("ETL run marked SUCCESS.")

    except Exception as e:
        logging.exception("ETL pipeline failed.")
        # If we can, record failure in audit table
        try:
            if etl_run_id is not None:
                with engine.begin() as conn:
                    finish_etl_run(conn, etl_run_id, status="FAIL", error_message=str(e))
        except Exception:
            logging.exception("Failed to update audit table after failure.")

if __name__ == "__main__":
    main()