import os
import sys
import time
import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy import UniqueConstraint
from .database import SessionLocal, engine
from .db_tables import HistoricalListing, ActiveListing, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make paths robust to where the script is run from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORICAL_CSV = os.path.join(PROJECT_ROOT, "data", "historical_dld.csv")
ACTIVE_CSV = os.path.join(PROJECT_ROOT, "data", "active_dld.csv")

def wait_for_db(retries=30, delay=2):
    """Wait for Postgres to become available."""
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database is ready.")
                return True
        except OperationalError:
            logger.info(f"Database not ready, retrying in {delay}s... ({i+1}/{retries})")
            time.sleep(delay)
    return False

def clean_row(row):
    """Convert pandas row to a dict, handling NaN and date parsing."""
    data = row.to_dict()
    for k, v in data.items():
        if pd.isna(v):
            data[k] = None
        elif k == "post_date":
            try:
                if isinstance(v, str):
                    # dayfirst=True because CSV uses DD/MM/YYYY
                    dt = pd.to_datetime(v, errors="coerce", dayfirst=True)
                    data[k] = dt.date() if pd.notna(dt) else None
                else:
                    data[k] = v
            except Exception:
                data[k] = None
        elif k == "property_id":
            data[k] = str(v) if v is not None else None
    return data

def seed_table(csv_path: str, model_class, truncate_first: bool = False):
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found: {csv_path}, skipping.")
        return 0, 0

    logger.info(f"Seeding {model_class.__tablename__} from {csv_path}...")

    if truncate_first:
        with SessionLocal() as session:
            session.query(model_class).delete()
            session.commit()
            logger.info(f"Truncated {model_class.__tablename__} before seeding.")

    df = pd.read_csv(csv_path)

    # 🔧 Normalise column names: lowercase, spaces → underscores
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]

    total_rows = len(df)
    logger.info(f"Read {total_rows} rows from {csv_path}")

    records = []
    for _, row in df.iterrows():
        cleaned = clean_row(row)
        # For active listings, require property_id
        if model_class == ActiveListing and not cleaned.get("property_id"):
            continue
        records.append(cleaned)

    if not records:
        logger.warning(f"No valid rows to insert in {csv_path}")
        return 0, total_rows

    with SessionLocal() as session:
        try:
            has_unique = any(
                isinstance(c, UniqueConstraint) and 'property_id' in c.columns
                for c in model_class.__table__.constraints
            )

            if has_unique:
                # Use dialect-specific INSERT ... ON CONFLICT DO NOTHING
                dialect_name = session.bind.dialect.name
                if dialect_name == "postgresql":
                    from sqlalchemy.dialects.postgresql import insert as pg_insert
                    stmt = pg_insert(model_class).values(records).on_conflict_do_nothing(
                        index_elements=["property_id"]
                    )
                elif dialect_name == "sqlite":
                    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
                    stmt = sqlite_insert(model_class).values(records).on_conflict_do_nothing(
                        index_elements=["property_id"]
                    )
                else:
                    # Generic fallback: plain insert (may fail on dupes)
                    stmt = model_class.__table__.insert().values(records)
                session.execute(stmt)
                session.commit()
                inserted = len(records)
                skipped = 0
            else:
                # Plain insert – all rows inserted
                session.add_all([model_class(**rec) for rec in records])
                session.commit()
                inserted = len(records)
                skipped = 0

            logger.info(f"{model_class.__tablename__}: inserted {inserted}, skipped {skipped}")
            return inserted, skipped
        except Exception as e:
            session.rollback()
            logger.error(f"Error during insert: {e}")
            return 0, len(records)

def seed_all():
    logger.info("Starting database seeding...")
    if not wait_for_db():
        logger.error("Could not connect to database after multiple attempts. Exiting.")
        sys.exit(1)
    Base.metadata.create_all(bind=engine)

    hist_ins, hist_skp = seed_table(HISTORICAL_CSV, HistoricalListing, truncate_first=True)
    act_ins, act_skp = seed_table(ACTIVE_CSV, ActiveListing)

    total_ins = hist_ins + act_ins
    total_skp = hist_skp + act_skp
    logger.info(f"Seeding complete. Total inserted: {total_ins}, Total skipped: {total_skp}")

if __name__ == "__main__":
    seed_all()