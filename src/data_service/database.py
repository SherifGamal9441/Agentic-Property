# data-service/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .db_tables import Base
from dotenv import load_dotenv

load_dotenv() 

# Get the database URL from environment, fallback to local SQLite for dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/dld_local.db")

is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {}
if not is_sqlite:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600
else:
    # ensure data directory exists for sqlite
    os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
