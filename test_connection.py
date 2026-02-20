from sqlalchemy import create_engine, text
from config.config import CONNECTION_STRING

engine = create_engine(CONNECTION_STRING)

with engine.connect() as conn:
    db = conn.execute(text("SELECT DB_NAME()")).scalar()
    version = conn.execute(text("SELECT @@VERSION")).scalar()
    print("Connected to DB:", db)
    print("SQL Server Version (first line):", version.splitlines()[0])