from mcp.server.fastmcp import FastMCP
from tools.historical import HistoricalSearchTool
from tools.active import ActiveSearchTool
from tools.compare import CompareTool
from tools.currency import CurrencyTool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(name="DLD_MCP_Server")

# ---------------------------------------------------------------------------
# Tool 1: Search Historical Listings
# ---------------------------------------------------------------------------
@mcp.tool(
    name="search_historical_listings",
    description="Search Dubai real estate historical transactions with various filters."
)
async def search_historical(
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
    Search historical transactions. All filters are optional.

    Args:
        area_name: Exact area name (e.g., "Dubai Marina", "Downtown Dubai").
        address: Partial address string to match (case‑insensitive).
        building_name: Name of the building (partial match).
        type: Property type (e.g., "Apartment", "Villa", "Townhouse").
        furnishing: Furnishing status: "Furnished" or "Unfurnished".
        completion_status: "completed" or "under-construction".
        price_min: Minimum price in AED.
        price_max: Maximum price in AED.
        beds_min: Minimum number of bedrooms.
        beds_max: Maximum number of bedrooms.
        baths_min: Minimum number of bathrooms.
        baths_max: Maximum number of bathrooms.
        year_of_completion_min: Earliest year of completion.
        year_of_completion_max: Latest year of completion.
        total_parking_spaces_min: Minimum parking spaces.
        total_parking_spaces_max: Maximum parking spaces.
        total_floors_min: Minimum number of floors in building.
        total_floors_max: Maximum number of floors in building.
        total_building_area_sqft_min: Minimum building area in sqft.
        total_building_area_sqft_max: Maximum building area in sqft.
        post_date_min: Earliest listing date (YYYY-MM-DD).
        post_date_max: Latest listing date (YYYY-MM-DD).
        limit: Maximum number of results to return (default 20, max 100).

    Returns:
        A dictionary with:
            - total_matches: total number of matching records.
            - returned_count: number of listings returned.
            - listings: list of property objects.
    """
    tool = HistoricalSearchTool()
    result = await tool.search(
        area_name=area_name,
        address=address,
        building_name=building_name,
        type=type,
        furnishing=furnishing,
        completion_status=completion_status,
        price_min=price_min,
        price_max=price_max,
        beds_min=beds_min,
        beds_max=beds_max,
        baths_min=baths_min,
        baths_max=baths_max,
        year_of_completion_min=year_of_completion_min,
        year_of_completion_max=year_of_completion_max,
        total_parking_spaces_min=total_parking_spaces_min,
        total_parking_spaces_max=total_parking_spaces_max,
        total_floors_min=total_floors_min,
        total_floors_max=total_floors_max,
        total_building_area_sqft_min=total_building_area_sqft_min,
        total_building_area_sqft_max=total_building_area_sqft_max,
        post_date_min=post_date_min,
        post_date_max=post_date_max,
        limit=limit
    )
    return result


# ---------------------------------------------------------------------------
# Tool 2: Search Active Listings
# ---------------------------------------------------------------------------
@mcp.tool(
    name="search_active_listings",
    description="Search current active Dubai real estate listings with filters (no date filters)."
)
async def search_active(
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
    limit: int = 20
):
    """
    Search active listings. All filters are optional. Date filters are NOT available.

    Args:
        area_name: Exact area name (e.g., "Dubai Marina", "Downtown Dubai").
        address: Partial address string to match (case‑insensitive).
        building_name: Name of the building (partial match).
        type: Property type (e.g., "Apartment", "Villa", "Townhouse").
        furnishing: Furnishing status: "Furnished" or "Unfurnished".
        completion_status: "completed" or "under-construction".
        price_min: Minimum price in AED.
        price_max: Maximum price in AED.
        beds_min: Minimum number of bedrooms.
        beds_max: Maximum number of bedrooms.
        baths_min: Minimum number of bathrooms.
        baths_max: Maximum number of bathrooms.
        year_of_completion_min: Earliest year of completion.
        year_of_completion_max: Latest year of completion.
        total_parking_spaces_min: Minimum parking spaces.
        total_parking_spaces_max: Maximum parking spaces.
        total_floors_min: Minimum number of floors in building.
        total_floors_max: Maximum number of floors in building.
        total_building_area_sqft_min: Minimum building area in sqft.
        total_building_area_sqft_max: Maximum building area in sqft.
        limit: Maximum number of results to return (default 20, max 100).

    Returns:
        A dictionary with:
            - total_matches: total number of matching records.
            - returned_count: number of listings returned.
            - listings: list of property objects.
    """
    tool = ActiveSearchTool()
    result = await tool.search(
        area_name=area_name,
        address=address,
        building_name=building_name,
        type=type,
        furnishing=furnishing,
        completion_status=completion_status,
        price_min=price_min,
        price_max=price_max,
        beds_min=beds_min,
        beds_max=beds_max,
        baths_min=baths_min,
        baths_max=baths_max,
        year_of_completion_min=year_of_completion_min,
        year_of_completion_max=year_of_completion_max,
        total_parking_spaces_min=total_parking_spaces_min,
        total_parking_spaces_max=total_parking_spaces_max,
        total_floors_min=total_floors_min,
        total_floors_max=total_floors_max,
        total_building_area_sqft_min=total_building_area_sqft_min,
        total_building_area_sqft_max=total_building_area_sqft_max,
        limit=limit
    )
    return result


# ---------------------------------------------------------------------------
# Tool 3: Compare Historical vs Active
# ---------------------------------------------------------------------------
@mcp.tool(
    name="compare_listings",
    description="Compare historical and active listings for an area to see price trends and statistics."
)
async def compare_listings(
    area_name: str = None,
    type: str = None,
    furnishing: str = None,
    beds_min: int = None,
    beds_max: int = None,
    price_min: float = None,
    price_max: float = None,
    limit: int = 20
):
    """
    Compare historical and active data for a given area and filters.

    Args:
        area_name: Exact area name to filter (e.g., "Dubai Marina").
        type: Property type (e.g., "Apartment", "Villa").
        furnishing: Furnishing status: "Furnished" or "Unfurnished".
        beds_min: Minimum number of bedrooms.
        beds_max: Maximum number of bedrooms.
        price_min: Minimum price in AED.
        price_max: Maximum price in AED.
        limit: Maximum number of recent properties to analyse from each dataset (default 20).

    Returns:
        A dictionary with:
            - historical_data: total_matches, listings, and stats (avg, median, min, max price).
            - active_data: total_matches, listings, and stats.
            - comparison: price_change_pct (percentage change from historical avg to active avg) and a summary message.
    """
    historical_tool = HistoricalSearchTool()
    active_tool = ActiveSearchTool()
    compare_tool = CompareTool(historical_tool, active_tool)
    result = await compare_tool.compare(
        area_name=area_name,
        type=type,
        furnishing=furnishing,
        beds_min=beds_min,
        beds_max=beds_max,
        price_min=price_min,
        price_max=price_max,
        limit=limit
    )
    return result


# ---------------------------------------------------------------------------
# Tool 4: Currency Conversion
# ---------------------------------------------------------------------------
@mcp.tool(
    name="convert_currency",
    description="Convert an amount from one currency to another using real‑time exchange rates."
)
async def convert_currency_tool(from_currency: str, to_currency: str, amount: float) -> str:
    """
    Convert a monetary amount between two currencies.

    Args:
        from_currency: The source currency code (e.g., "USD", "EUR", "AED").
        to_currency: The target currency code (e.g., "USD", "EUR", "AED").
        amount: The amount of money to convert (must be a positive number).

    Returns:
        A formatted string with the conversion result, e.g.:
        "100.0 USD = 367.25 AED"
    """
    tool = CurrencyTool()
    result = await tool.convert(from_currency, to_currency, amount)

    if result.get("error"):
        return f"❌ Error: {result.get('message')}"

    return (
        f"{result['amount']} {result['from'].upper()} = "
        f"{result['result']:.2f} {result['to'].upper()}"
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting DLD MCP Server...")
    mcp.run()