"""Start the FastAPI data service locally."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from config.pydantic.settings import settings
from src.data_service.app import app

if __name__ == "__main__":
    uvicorn.run(app, host=settings.data_service_host, port=settings.data_service_port)
