from datetime import date, timedelta
from sqlalchemy import create_engine, text
from config.config import CONNECTION_STRING

def get_engine():
    return create_engine(CONNECTION_STRING, fast_executemany=True)

def date_key(d: date) -> int:
    return int(d.strftime("%Y%m%d"))

def day_of_week_mon1(d: date) -> int:
    # Python: Monday=0..Sunday=6 -> convert to 1..7
    return d.weekday() + 1

def main():
    start = date(2024, 1, 1)
    end = date(2026, 2, 20)  # inclusive

    engine = get_engine()
    rows_inserted = 0

    with engine.begin() as conn:
        d = start
        while d <= end:
            dow = day_of_week_mon1(d)
            params = {
                "date_key": date_key(d),
                "date": d.isoformat(),
                "year": d.year,
                "quarter": (d.month - 1) // 3 + 1,
                "month": d.month,
                "day": d.day,
                "day_of_week": dow,
                "is_weekend": 1 if dow in (6, 7) else 0,
            }

            result = conn.execute(text("""
                IF NOT EXISTS (SELECT 1 FROM dw.dim_date WHERE date_key = :date_key)
                BEGIN
                    INSERT INTO dw.dim_date
                        (date_key, [date], [year], [quarter], [month], [day], day_of_week, is_weekend)
                    VALUES
                        (:date_key, :date, :year, :quarter, :month, :day, :day_of_week, :is_weekend);
                END
            """), params)

            # rowcount is unreliable with IF blocks; we’ll count at the end instead.
            d += timedelta(days=1)

        total = conn.execute(text("SELECT COUNT(*) FROM dw.dim_date;")).scalar()

    print(f"✅ dim_date total rows now: {total:,} (range {start} to {end})")

if __name__ == "__main__":
    main()