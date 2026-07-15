"""First-run PostgreSQL bootstrap with an auditable SQLite fallback repair."""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ACTIVE_CSV = DATA_DIR / "active_dld.csv"
HISTORICAL_CSV = DATA_DIR / "historical_dld.csv"
SQLITE_PATH = PROJECT_ROOT / "data" / "dld_local.db"
SQLITE_URL = "sqlite:///data/dld_local.db"
ACTIVE_COLUMNS = (
    "property_id", "price", "type", "beds", "baths", "address", "furnishing",
    "completion_status", "post_date", "building_name", "year_of_completion",
    "building_total_parking_spaces", "building_floors", "building_total_area_sqft", "building_elevators",
    "area_name", "latitude", "longitude", "link",
)
DATABASE_COLUMN = {
    "building_total_parking_spaces": "total_parking_spaces",
    "building_floors": "total_floors",
    "building_total_area_sqft": "total_building_area_sqft",
    "building_elevators": "elevators",
}


def _normalise(value):
    if pd.isna(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return float(value)
    return str(value)


def _active_csv_rows(csv_path: Path) -> dict[str, dict]:
    frame = pd.read_csv(csv_path)
    frame.columns = [column.lower().replace(" ", "_") for column in frame.columns]
    return {
        str(row["property_id"]): {
            column: _normalise(row.get(column)) for column in ACTIVE_COLUMNS
        }
        for _, row in frame.iterrows()
    }


def _active_database_rows(database_url: str) -> dict[str, dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            select_columns = [f"{DATABASE_COLUMN.get(column, column)} AS {column}" for column in ACTIVE_COLUMNS]
            rows = connection.execute(text(f"SELECT {', '.join(select_columns)} FROM active_listings")).mappings()
            return {
                str(row["property_id"]): {column: _normalise(row[column]) for column in ACTIVE_COLUMNS}
                for row in rows
            }
    except SQLAlchemyError:
        return {}
    finally:
        engine.dispose()


def audit_active_rows(csv_path: Path, database_url: str) -> dict:
    csv_rows = _active_csv_rows(csv_path)
    database_rows = _active_database_rows(database_url)
    changed_fields: dict[str, int] = {}
    for property_id in csv_rows.keys() & database_rows.keys():
        for column in ACTIVE_COLUMNS:
            if csv_rows[property_id][column] != database_rows[property_id][column]:
                changed_fields[column] = changed_fields.get(column, 0) + 1
    return {
        "csv_rows": len(csv_rows),
        "database_rows": len(database_rows),
        "csv_only_ids": len(csv_rows.keys() - database_rows.keys()),
        "database_only_ids": len(database_rows.keys() - csv_rows.keys()),
        "changed_fields": changed_fields,
    }


def _table_count(database_url: str, table_name: str) -> int | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()
    except SQLAlchemyError:
        return None
    finally:
        engine.dispose()


def audit_listing_data(primary_url: str) -> dict:
    return {
        "active": {
            "sqlite": audit_active_rows(ACTIVE_CSV, SQLITE_URL),
            "postgres": audit_active_rows(ACTIVE_CSV, primary_url),
        },
        "historical": {
            "csv_rows": len(pd.read_csv(HISTORICAL_CSV)),
            "sqlite_rows": _table_count(SQLITE_URL, "historical_listings"),
            "postgres_rows": _table_count(primary_url, "historical_listings"),
        },
    }


def _wait_for_postgres(database_url: str) -> bool:
    retries = int(os.getenv("BOOTSTRAP_CONNECT_RETRIES", "30"))
    for _ in range(retries):
        engine = create_engine(database_url, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            pass
        finally:
            engine.dispose()
        time.sleep(float(os.getenv("DATABASE_CONNECT_DELAY_SECONDS", "1")))
    return False


def _require_seed_files() -> None:
    missing = [path for path in (ACTIVE_CSV, HISTORICAL_CSV) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Required seed data is missing: {', '.join(map(str, missing))}")


def _repair_sqlite() -> None:
    environment = os.environ | {
        "DATABASE_URL": SQLITE_URL,
        "DATABASE_CONNECT_RETRIES": "1",
        "RESET_ACTIVE_LISTINGS": "1",
    }
    subprocess.run([sys.executable, "-m", "src.data_service.seed"], check=True, env=environment)


def bootstrap() -> bool:
    marker = Path(os.getenv("BOOTSTRAP_MARKER", "/state/postgres-seeded"))
    primary_url = os.getenv("DATABASE_URL", "")
    if marker.exists():
        logger.info("bootstrap: PostgreSQL already seeded")
        return True
    if not primary_url or primary_url.startswith("sqlite") or not _wait_for_postgres(primary_url):
        logger.warning("bootstrap: PostgreSQL unavailable; data service will use SQLite fallback")
        return False

    _require_seed_files()
    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = backup_dir / f"listing-audit-{timestamp}.json"
    report = {"before": audit_listing_data(primary_url)}

    if SQLITE_PATH.exists():
        shutil.copy2(SQLITE_PATH, backup_dir / f"dld_local-{timestamp}.db")
    subprocess.run(
        ["pg_dump", f"--dbname={primary_url}", "--format=custom", f"--file={backup_dir / f'postgres-{timestamp}.dump'}"],
        check=True,
    )

    _repair_sqlite()
    from . import seed

    seed.seed_all(reset_active=True)
    report["after"] = audit_listing_data(primary_url)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    logger.info("bootstrap: PostgreSQL seeded; audit written to %s", report_path)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bootstrap()
