"""DLD MCP Server — Dubai real estate search + currency conversion tools.

Single file, three tools. FastMCP reads the type hints + docstrings to
generate the tool input schemas — no separate param models or signature
gymnastics needed. Adding a filter = adding one kwarg to the signature.

Tools:
    search_historical_listings — historical DLD transactions
    search_active_listings      — current active listings
    convert_currency            — real-time FX conversion

Config:
    config/mcp.yaml        — server host/port/transport + DATA_SERVICE_URL (env vars override)
    .env / environ         — EXCHANGERATE_API_KEY (secrets stay out of yaml)
"""

import os
import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path so absolute imports work when
# this file is executed standalone by `mcp run src/mcp/server.py`.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import httpx
import yaml
from mcp.server.fastmcp import FastMCP

from src.mcp.schemas import BasePropertyFilters, HistoricalFilters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Load config from config/mcp.yaml (env vars override for Docker) ───────────
_CFG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "mcp.yaml"
_CFG = {}
if _CFG_PATH.exists():
    with open(_CFG_PATH) as f:
        _CFG = yaml.safe_load(f)
    logger.info("Loaded config from %s", _CFG_PATH)
else:
    logger.info("config/mcp.yaml not found — using env vars / defaults")

_srv = _CFG.get("server", {})
_env = _CFG.get("env", {})

MCP_HOST = os.getenv("MCP_HOST") or _srv.get("host", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT") or _srv.get("port", 8001))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT") or _srv.get("transport", "stdio")

# Make DATA_SERVICE_URL from config available (env overrides config)
if "DATA_SERVICE_URL" in _env and "DATA_SERVICE_URL" not in os.environ:
    os.environ["DATA_SERVICE_URL"] = _env["DATA_SERVICE_URL"]
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://data-service:8000")

mcp = FastMCP(
    name="DLD_MCP_Server",
    host=MCP_HOST,
    port=MCP_PORT,
)


@mcp.tool()
async def search_historical_listings(filters: HistoricalFilters) -> dict:
    """Search Dubai real estate historical transactions with various filters."""
    payload = filters.model_dump(exclude_none=True)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{DATA_SERVICE_URL}/search/historical", json=payload)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def search_active_listings(filters: BasePropertyFilters) -> dict:
    """Search current active Dubai real estate listings with various filters."""
    payload = filters.model_dump(exclude_none=True)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{DATA_SERVICE_URL}/search/active", json=payload)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def convert_currency(from_currency: str, to_currency: str, amount: float) -> str:
    """Convert an amount from one currency to another using real-time exchange rates."""
    api_key = os.getenv("EXCHANGERATE_API_KEY")
    if not api_key:
        return "Error: EXCHANGERATE_API_KEY is not configured"
    params = {
        "access_key": api_key,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": amount,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.exchangerate.host/convert", params=params
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: Currency API request failed: {exc}"
    if not data.get("success", False):
        err = data.get("error", {})
        msg = err.get("info", str(err)) if isinstance(err, dict) else str(err)
        return f"Error: {msg}"
    result = data.get("result")
    if result is None:
        return "Error: Currency API returned no result"
    return f"{amount} {from_currency.upper()} = {result:.2f} {to_currency.upper()}"


if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else MCP_TRANSPORT
    logger.info("Starting DLD MCP Server (%s mode)...", transport)
    mcp.run(transport=transport)
