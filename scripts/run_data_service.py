"""Start the FastAPI data service locally."""

import sys
from pathlib import Path
import uvicorn

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_service.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
