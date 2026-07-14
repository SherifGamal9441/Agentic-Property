# data-service/database.py
import os
import logging
import threading
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from .db_tables import Base
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SQLITE_URL = "sqlite:///data/dld_local.db"

# A missing URL means local SQLite development. An unavailable explicit URL
# falls back visibly so callers can distinguish degraded service from Postgres.
DATABASE_URL = os.getenv("DATABASE_URL", SQLITE_URL)
_lock = threading.Lock()
_backend = "sqlite"
_degraded = DATABASE_URL != SQLITE_URL


def _try_connect(url: str) -> bool:
    try:
        eng = create_engine(url, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return True
    except Exception:
        return False


def _create_engine(url: str):
    if url.startswith("sqlite"):
        db_path = url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return create_engine(url)
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def _activate(url: str, backend: str, degraded: bool) -> None:
    global engine, SessionLocal, is_sqlite, _backend, _degraded

    new_engine = _create_engine(url)
    Base.metadata.create_all(bind=new_engine)
    old_engine = globals().get("engine")
    engine = new_engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    is_sqlite = backend == "sqlite"
    _backend = backend
    _degraded = degraded
    if old_engine is not None and old_engine is not new_engine:
        old_engine.dispose()


def _connect_primary_or_fallback() -> None:
    if DATABASE_URL.startswith("sqlite"):
        _activate(DATABASE_URL, "sqlite", False)
        return

    retries = int(os.getenv("DATABASE_CONNECT_RETRIES", "1"))
    delay_seconds = float(os.getenv("DATABASE_CONNECT_DELAY_SECONDS", "1"))
    for attempt in range(retries):
        if _try_connect(DATABASE_URL):
            _activate(DATABASE_URL, "postgresql", False)
            return
        if attempt + 1 < retries:
            time.sleep(delay_seconds)

    logger.warning("database: PostgreSQL unavailable; serving from SQLite fallback at %s", SQLITE_URL)
    _activate(SQLITE_URL, "sqlite", True)


_connect_primary_or_fallback()


def get_database_status() -> dict[str, str | bool]:
    return {"database_backend": _backend, "degraded": _degraded}


def get_db() -> Session:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except OperationalError:
        db.close()
        if _backend != "postgresql":
            raise
        with _lock:
            if _backend == "postgresql":
                logger.warning("database: PostgreSQL connection failed; switching to SQLite fallback")
                _activate(SQLITE_URL, "sqlite", True)
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

