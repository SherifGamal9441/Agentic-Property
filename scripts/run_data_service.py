"""Start the FastAPI data service locally."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from config.pydantic.settings import settings
from src.data_service.app import app
from src.data_service.database import SessionLocal
from src.data_service.db_tables import ActiveListing, HistoricalListing


def _is_db_empty() -> bool:
    """Check if both tables are empty (need seeding)."""
    with SessionLocal() as session:
        active_count = session.query(ActiveListing).limit(1).count()
        historical_count = session.query(HistoricalListing).limit(1).count()
        return active_count == 0 and historical_count == 0


if __name__ == "__main__":
    if _is_db_empty():
        print("Database is empty — seeding from CSV files...")
        from src.data_service.seed import seed_all
        seed_all()
        print("Seeding complete.")

    uvicorn.run(app, host=settings.data_service_host, port=settings.data_service_port)

