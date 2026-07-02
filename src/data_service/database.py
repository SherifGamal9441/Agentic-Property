# data-service/database.py
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from .db_tables import Base
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SQLITE_URL = "sqlite:///data/dld_local.db"

# Get the database URL from environment, fallback to local SQLite for dev
DATABASE_URL = os.getenv("DATABASE_URL", SQLITE_URL)


def _try_connect(url: str) -> bool:
    """Quick connectivity check — returns True if the DB is reachable."""
    try:
        eng = create_engine(url, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return True
    except Exception:
        return False


# If a non-SQLite URL is configured but unreachable (e.g. Docker Postgres),
# fall back to SQLite so local dev still works.
if not DATABASE_URL.startswith("sqlite") and not _try_connect(DATABASE_URL):
    logger.warning(
        "database: configured DATABASE_URL (%s) is unreachable — "
        "falling back to local SQLite at %s",
        DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        SQLITE_URL,
    )
    DATABASE_URL = SQLITE_URL

is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {}
if not is_sqlite:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600
else:
    # ensure data directory exists for sqlite
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)

# Eagerly create tables so the first request doesn't 500 on a fresh DB
Base.metadata.create_all(bind=engine)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

