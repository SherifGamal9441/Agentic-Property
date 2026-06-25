import os
import httpx

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
        params = {
            'area_name': area_name,
            'address': address,
            'building_name': building_name,
            'type': type,
            'furnishing': furnishing,
            'completion_status': completion_status,
            'price_min': price_min,
            'price_max': price_max,
            'beds_min': beds_min,
            'beds_max': beds_max,
            'baths_min': baths_min,
            'baths_max': baths_max,
            'year_of_completion_min': year_of_completion_min,
            'year_of_completion_max': year_of_completion_max,
            'total_parking_spaces_min': total_parking_spaces_min,
            'total_parking_spaces_max': total_parking_spaces_max,
            'total_floors_min': total_floors_min,
            'total_floors_max': total_floors_max,
            'total_building_area_sqft_min': total_building_area_sqft_min,
            'total_building_area_sqft_max': total_building_area_sqft_max,
            'post_date_min': post_date_min,
            'post_date_max': post_date_max,
            'limit': limit
        }
        for key, value in params.items():
            if value is not None:
                payload[key] = value

        url = f"{DATA_SERVICE_URL}/search/historical"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()