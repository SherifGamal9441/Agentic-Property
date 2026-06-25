import os
import sys
import inspect
import logging
from mcp.server.fastmcp import FastMCP
from tools.historical import HistoricalSearchTool
from tools.active import ActiveSearchTool
from tools.compare import CompareTool
from tools.currency import CurrencyTool
from pydantic import BaseModel
from tool_models import (
    SearchHistoricalParams,
    SearchActiveParams,
    CompareListingsParams,
    ConvertCurrencyParams,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP(name="DLD_MCP_Server", host=MCP_HOST, port=MCP_PORT)


def build_tool_fn(
    model_class: type[BaseModel],
    impl,
    *,
    name: str,
    description: str,
):
    sig = inspect.Signature(
        [
            inspect.Parameter(
                name=fname,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=field.default,
                annotation=field.annotation,
            )
            for fname, field in model_class.model_fields.items()
        ]
    )

    async def wrapper(**kwargs) -> dict | str:
        p = model_class(**kwargs)
        return await impl(p)

    wrapper.__name__ = name
    wrapper.__signature__ = sig
    wrapper.__doc__ = description
    return wrapper


# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------

mcp.add_tool(
    fn=build_tool_fn(
        SearchHistoricalParams,
        lambda p: HistoricalSearchTool().search(**p.model_dump(exclude_none=True)),
        name="search_historical_listings",
        description="Search Dubai real estate historical transactions with various filters.",
    ),
)

mcp.add_tool(
    fn=build_tool_fn(
        SearchActiveParams,
        lambda p: ActiveSearchTool().search(**p.model_dump(exclude_none=True)),
        name="search_active_listings",
        description="Search current active Dubai real estate listings with various filters.",
    ),
)

mcp.add_tool(
    fn=build_tool_fn(
        CompareListingsParams,
        lambda p: CompareTool(HistoricalSearchTool(), ActiveSearchTool()).compare(
            **p.model_dump(exclude_none=True)
        ),
        name="compare_listings",
        description="Compare historical and active listings for an area to see price trends and statistics.",
    ),
)


async def _convert_impl(p: ConvertCurrencyParams) -> str:
    result = await CurrencyTool().convert(p.from_currency, p.to_currency, p.amount)
    if result.get("error"):
        return f"Error: {result.get('message')}"
    return f"{result['amount']} {result['from'].upper()} = {result['result']:.2f} {result['to'].upper()}"


mcp.add_tool(
    fn=build_tool_fn(
        ConvertCurrencyParams,
        _convert_impl,
        name="convert_currency",
        description="Convert an amount from one currency to another using real-time exchange rates.",
    ),
)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if len(sys.argv) > 1:
        transport = sys.argv[1]
    logger.info(
        "Starting DLD MCP Server (%s mode on %s:%s)...", transport, MCP_HOST, MCP_PORT
    )
    mcp.run(transport=transport)
