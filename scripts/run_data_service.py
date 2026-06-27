"""Start the FastAPI data service locally."""
import uvicorn
from src.data_service.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
