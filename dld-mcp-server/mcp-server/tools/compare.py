import os
import httpx

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://data-service:8000")

class CompareTool:
    def __init__(self, historical_tool, active_tool):
        """
        Initialize with instances of HistoricalSearchTool and ActiveSearchTool.
        """
        self.historical = historical_tool
        self.active = active_tool

    async def compare(
        self,
        area_name: str = None,
        type: str = None,
        furnishing: str = None,
        beds_min: int = None,
        beds_max: int = None,
        price_min: float = None,
        price_max: float = None,
        limit: int = 20
    ) -> dict:
        """
        Compare historical and active property data for a specific area/building.

        Args:
            area_name: Area name to filter (e.g., "Dubai Marina")
            type: Property type (e.g., "Apartment", "Villa")
            furnishing: Furnishing status ("Furnished" or "Unfurnished")
            beds_min: Minimum number of bedrooms
            beds_max: Maximum number of bedrooms
            price_min: Minimum price
            price_max: Maximum price
            limit: Number of recent properties to analyze from each dataset

        Returns:
            JSON with statistical comparison
        """
        # Build common filters
        common_filters = {
            "area_name": area_name,
            "type": type,
            "furnishing": furnishing,
            "beds_min": beds_min,
            "beds_max": beds_max,
            "price_min": price_min,
            "price_max": price_max,
            "limit": limit
        }

        # Remove None values
        filters = {k: v for k, v in common_filters.items() if v is not None}

        # --- 1. Fetch Historical Data ---
        try:
            historical_result = await self.historical.search(**filters)
            historical_listings = historical_result.get("listings", [])
            historical_total = historical_result.get("total_matches", 0)
        except Exception as e:
            return {
                "error": True,
                "message": f"Error fetching historical data: {str(e)}",
                "historical_data": None,
                "active_data": None
            }

        # --- 2. Fetch Active Data ---
        try:
            active_result = await self.active.search(**filters)
            active_listings = active_result.get("listings", [])
            active_total = active_result.get("total_matches", 0)
        except Exception as e:
            return {
                "error": True,
                "message": f"Error fetching active data: {str(e)}",
                "historical_data": None,
                "active_data": None
            }

        # --- 3. Check if we have data ---
        if not historical_listings and not active_listings:
            return {
                "error": True,
                "message": f"No data available for '{area_name or 'this location'}'. Please try a different search.",
                "historical_data": None,
                "active_data": None
            }

        # --- 4. Calculate statistics ---
        def calculate_price_stats(listings):
            if not listings:
                return {
                    "avg_price": None,
                    "median_price": None,
                    "min_price": None,
                    "max_price": None
                }
            
            prices = [l.get('price') for l in listings if l.get('price') is not None]
            if not prices:
                return {
                    "avg_price": None,
                    "median_price": None,
                    "min_price": None,
                    "max_price": None
                }
            
            sorted_prices = sorted(prices)
            n = len(sorted_prices)
            
            return {
                "avg_price": round(sum(prices) / n, 2),
                "median_price": sorted_prices[n // 2] if n % 2 == 1 else round((sorted_prices[n//2 - 1] + sorted_prices[n//2]) / 2, 2),
                "min_price": min(prices),
                "max_price": max(prices)
            }

        historical_stats = calculate_price_stats(historical_listings)
        active_stats = calculate_price_stats(active_listings)

        # --- 5. Calculate price change percentage ---
        price_change_pct = None
        if historical_stats.get("avg_price") and active_stats.get("avg_price") and historical_stats["avg_price"] != 0:
            price_change_pct = round(
                ((active_stats["avg_price"] - historical_stats["avg_price"]) / historical_stats["avg_price"]) * 100,
                2
            )

        # --- 6. Build Response ---
        response = {
            "historical_data": {
                "listings": historical_listings,
                "total_matches": historical_total,
                "stats": historical_stats
            },
            "active_data": {
                "listings": active_listings,
                "total_matches": active_total,
                "stats": active_stats
            },
            "comparison": {
                "price_change_pct": price_change_pct,
                "message": None
            }
        }

        # Add summary message
        if not historical_listings and active_listings:
            response["comparison"]["message"] = "No historical data available. Showing current active listings only."
        elif historical_listings and not active_listings:
            response["comparison"]["message"] = "No active listings available. Showing historical data only."
        elif historical_listings and active_listings:
            response["comparison"]["message"] = f"Found {len(historical_listings)} historical and {len(active_listings)} active listings for comparison."

        return response