"""
DLD MCP client — exposes search_historical, search_active, compare, and
convert_currency as plain async + sync functions.

Transport is picked from config/mcp.yaml (active: stdio | sse | streamable_http).
Each teammate sets their preference there — zero code changes.

Usage:
    from src.tools.dld_mcp import search_historical, search_active

    listings = await search_historical(area_name="Dubai Marina", limit=5)
    listings = await search_active(type="Apartment", beds_min=2)
"""

import os
import json
import asyncio
from pathlib import Path

import yaml
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# ── Load MCP config from YAML ──────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "mcp.yaml"
_PROJECT_ROOT = _CONFIG_PATH.parent.parent  # repo root (config/ → root)

with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

_ACTIVE = _CFG.get("active", "stdio")
_YAML_ENV = _CFG.get("env", {})


def _build_client():
    """Return an async context manager yielding (read, write) based on active transport."""
    if _ACTIVE == "stdio":
        s = _CFG["stdio"]
        cwd = s.get("cwd")
        if cwd:
            cwd = str((_PROJECT_ROOT / cwd).resolve())
        # Merge: os.environ (secrets from .env via load_dotenv in settings.py)
        #         + YAML env block (connection params like DATA_SERVICE_URL).
        # YAML wins on conflict — it's the config source of truth.
        params = StdioServerParameters(
            command=s["command"],
            args=s["args"],
            env={**os.environ, **_YAML_ENV},
            cwd=cwd,
        )
        return stdio_client(params)

    if _ACTIVE in ("sse", "streamable_http"):
        from mcp.client.sse import sse_client
        url = _CFG[_ACTIVE]["url"]
        return sse_client(url)

    raise ValueError(f"Unknown MCP transport: {_ACTIVE!r}. Expected stdio | sse | streamable_http")


async def _call_tool(tool_name: str, arguments: dict) -> list[dict]:
    """Open a session, call one tool, return parsed listings."""
    # Normalize string enum fields — data-service does exact match
    for key in ("type", "furnishing", "completion_status", "area_name"):
        if key in arguments and arguments[key] is not None:
            arguments[key] = arguments[key].strip().title()
    # ponytail: title-case normalization. Revisit if DB gets mixed-case values.

    async with _build_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            text = result.content[0].text
            data = json.loads(text)
            return data.get("listings", [])


async def search_historical(**filters) -> list[dict]:
    """Search Dubai historical real estate transactions.

    Kwargs: area_name, type, furnishing, price_min, price_max, beds_min,
            beds_max, limit (default 20), etc. All optional.
    """
    return await _call_tool("search_historical_listings", filters)


async def search_active(**filters) -> list[dict]:
    """Search current active Dubai real estate listings.

    Kwargs: same as search_historical (no date filters).
    """
    return await _call_tool("search_active_listings", filters)


async def compare(area_name: str = None, type: str = None, **filters) -> dict:
    """Compare historical vs active listings for an area. Returns stats dict."""
    args = {
        k: v
        for k, v in {**filters, "area_name": area_name, "type": type}.items()
        if v is not None
    }
    async with _build_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("compare_listings", args)
            return json.loads(result.content[0].text)


async def convert_currency(from_currency: str, to_currency: str, amount: float) -> dict:
    """Convert currency via MCP server.

    Returns {"rate": float} on success, {"error": True, "message": str} on failure.
    """
    async with _build_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("convert_currency", {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount,
            })
            text = result.content[0].text
            if result.isError or text.startswith("Error:"):
                return {"error": True, "message": text}
            # Parse "1.0 USD = 3.67 AED"
            try:
                parts = text.split("=")
                rate = float(parts[1].strip().split()[0])
                return {"rate": rate, "text": text}
            except (IndexError, ValueError):
                return {"error": True, "message": f"Could not parse: {text}"}


# ── Sync wrappers for LangGraph nodes ──────────────────────────────────────────


def search_historical_sync(**filters) -> list[dict]:
    return asyncio.run(search_historical(**filters))


def search_active_sync(**filters) -> list[dict]:
    return asyncio.run(search_active(**filters))


def convert_currency_sync(from_currency: str, to_currency: str, amount: float) -> dict:
    return asyncio.run(convert_currency(from_currency, to_currency, amount))
