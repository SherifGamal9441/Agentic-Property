"""Start the FastAPI data service locally."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from config.pydantic.settings import settings
from src.data_service.app import app
from src.data_service.database import SessionLocal
from src.data_service.db_tables import ActiveListing, HistoricalListing


def seed_active_if_empty() -> bool:
    """Check if active listings are empty (need seeding)."""
    with SessionLocal() as session:
        active_count = session.query(ActiveListing).limit(1).count()
        return active_count == 0

if __name__ == "__main__":
    if seed_active_if_empty():
        print("Active listings are empty — seeding from CSV file...")
        from src.data_service.seed import seed_table, ACTIVE_CSV
        seed_table(ACTIVE_CSV, ActiveListing)
        print("Seeding complete.")

    uvicorn.run(app, host=settings.data_service_host, port=settings.data_service_port)

