import os
import httpx
from dotenv import load_dotenv

load_dotenv() 

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://data-service:8000")

class HistoricalSearchTool:
    async def search(
        self,
        area_name: str = None,
        address: str = None,
        building_name: str = None,
        type: str = None,
        furnishing: str = None,
        completion_status: str = None,
        price_min: float = None,
        price_max: float = None,
        beds_min: int = None,
        beds_max: int = None,
        baths_min: int = None,
        baths_max: int = None,
        year_of_completion_min: int = None,
        year_of_completion_max: int = None,
        total_parking_spaces_min: int = None,
        total_parking_spaces_max: int = None,
        total_floors_min: int = None,
        total_floors_max: int = None,
        total_building_area_sqft_min: float = None,
        total_building_area_sqft_max: float = None,
        post_date_min: str = None,
        post_date_max: str = None,
        limit: int = 20
    ):
        """
        Search historical properties by calling the data-service API.
        All parameters are optional; omitted parameters are not sent.
        """
        # Build request payload with only non-None values
        payload = {}
        for key, value in locals().items():
            if key != 'self' and value is not None:
                payload[key] = value

        # If limit is set, include it (default 20 but if omitted we don't send, API uses its default)
        if limit is not None:
            payload['limit'] = limit

        url = f"{DATA_SERVICE_URL}/search/historical"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()