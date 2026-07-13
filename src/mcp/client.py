"""
DLD MCP client — exposes search_historical, search_active, and
convert_currency as plain async + sync functions.

Uses a persistent background thread and event loop to maintain a singleton
MCP session, avoiding connection overhead per call.
"""

import os
import json
import asyncio
import threading
import contextlib
import logging
from pathlib import Path

import yaml
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

logger = logging.getLogger(__name__)

# ── Load MCP config from YAML ──────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "mcp.yaml"
_PROJECT_ROOT = _CONFIG_PATH.parent.parent

with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

_ACTIVE = _CFG.get("active", "stdio")
_YAML_ENV = _CFG.get("env", {})

# ── Singleton Session State ───────────────────────────────────────────────────

_loop = None
_thread = None
_session = None
_exit_stack = None
_init_lock = threading.Lock()


def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


@contextlib.asynccontextmanager
async def _build_client():
    """Return an async context manager yielding (read, write) based on active transport."""
    if _ACTIVE == "stdio":
        s = _CFG["stdio"]
        cwd = s.get("cwd")
        if cwd:
            cwd = str((_PROJECT_ROOT / cwd).resolve())
        params = StdioServerParameters(
            command=s["command"],
            args=s["args"],
            env={**os.environ, **_YAML_ENV},
            cwd=cwd,
        )
        async with stdio_client(params) as (read, write):
            yield read, write
    elif _ACTIVE == "sse":
        from mcp.client.sse import sse_client
        url = _CFG["sse"]["url"]
        async with sse_client(url) as (read, write):
            yield read, write
    elif _ACTIVE == "streamable_http":
        from mcp.client.streamable_http import streamablehttp_client
        url = _CFG["streamable_http"]["url"]
        async with streamablehttp_client(url) as (read, write, _session_id):
            yield read, write
    else:
        raise ValueError(f"Unknown MCP transport: {_ACTIVE!r}")


async def _connect_async():
    global _session, _exit_stack
    _exit_stack = contextlib.AsyncExitStack()
    read, write = await _exit_stack.enter_async_context(_build_client())
    _session = await _exit_stack.enter_async_context(ClientSession(read, write))
    await _session.initialize()


def _ensure_connected():
    global _loop, _thread
    if _session is not None:
        return
    with _init_lock:
        if _session is not None:
            return
        logger.info("Initializing persistent MCP session...")
        _loop = asyncio.new_event_loop()
        _thread = threading.Thread(target=_start_background_loop, args=(_loop,), daemon=True)
        _thread.start()
        future = asyncio.run_coroutine_threadsafe(_connect_async(), _loop)
        future.result()  # wait until initialized


# ── Internal Call Logic ───────────────────────────────────────────────────────

async def _call_raw_async(tool_name: str, arguments: dict) -> str:
    call_result = await _session.call_tool(tool_name, arguments)
    if call_result.isError:
        error_text = (
            call_result.content[0].text if call_result.content
            else "Unknown error (no content)"
        )
        raise RuntimeError(f"MCP tool '{tool_name}' returned error: {error_text}")
    if not call_result.content:
        raise RuntimeError(f"MCP tool '{tool_name}' returned empty content")
    return call_result.content[0].text


def _call_raw_sync(tool_name: str, arguments: dict) -> str:
    _ensure_connected()
    future = asyncio.run_coroutine_threadsafe(_call_raw_async(tool_name, arguments), _loop)
    return future.result()


def _call_tool_sync(tool_name: str, arguments: dict) -> list[dict]:
    for key in ("type", "furnishing", "completion_status", "area_name"):
        if key in arguments and arguments[key] is not None:
            arguments[key] = arguments[key].strip().title()
            
    # LLMs sometimes stubbornly extract "Dubai" as the area_name. 
    # Since area_name in the DB refers to specific communities, this breaks the search.
    if arguments.get("area_name") == "Dubai":
        del arguments["area_name"]

    # Server tools expect a single `filters` parameter (Pydantic model),
    # so wrap the flat kwargs under a "filters" key.
    # Errors propagate as RuntimeError — callers can distinguish "MCP failed"
    # from "query matched 0 rows" (empty list = no match, exception = failure).
    text = _call_raw_sync(tool_name, {"filters": arguments})
    result = json.loads(text)
    listings = result.get("listings", [])
    if not listings:
        logger.warning(
            "_call_tool: %s returned 0 listings (total_matches=%s, filters=%s)",
            tool_name, result.get("total_matches", "?"), arguments,
        )
    return listings


# ── Public Sync API ───────────────────────────────────────────────────────────

def search_historical_sync(**filters) -> list[dict]:
    return _call_tool_sync("search_historical_listings", filters)


def search_active_sync(**filters) -> list[dict]:
    return _call_tool_sync("search_active_listings", filters)


def convert_currency_sync(from_currency: str, to_currency: str, amount: float) -> dict:
    try:
        text = _call_raw_sync("convert_currency", {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
        })
    except RuntimeError as e:
        return {"error": True, "message": str(e)}
    if text.startswith("Error:"):
        return {"error": True, "message": text}
    try:
        parts = text.split("=")
        rate = float(parts[1].strip().split()[0])
        return {"rate": rate, "text": text}
    except (IndexError, ValueError):
        return {"error": True, "message": f"Could not parse: {text}"}


# ── Public Async API ──────────────────────────────────────────────────────────

async def search_historical(**filters) -> list[dict]:
    _ensure_connected()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: search_historical_sync(**filters))

async def search_active(**filters) -> list[dict]:
    _ensure_connected()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: search_active_sync(**filters))

async def convert_currency(from_currency: str, to_currency: str, amount: float) -> dict:
    _ensure_connected()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: convert_currency_sync(from_currency, to_currency, amount))
