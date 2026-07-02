"""Long-term SQLite checkpoint saver for LangGraph agent memory.

Provides both sync (SqliteSaver, for CLI/tests) and async (AsyncSqliteSaver,
for Streamlit astream_events) variants. AsyncSqliteSaver requires a running
event loop so it must be created inside an async context.
"""

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_MEMORY_DIR = _PROJECT_ROOT / "data" / "memory"
_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = str(_MEMORY_DIR / "chat_history.db")

# ── Sync checkpointer (CLI, tests, sync invoke) ──────────────────────────────

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    return _conn


def _create_sync_checkpointer() -> SqliteSaver:
    return SqliteSaver(_get_conn())


def _get_sync_checkpointer() -> SqliteSaver:
    if not hasattr(_get_sync_checkpointer, "_instance"):
        _get_sync_checkpointer._instance = _create_sync_checkpointer()
    return _get_sync_checkpointer._instance


# Module-level convenience accessor for sync use
checkpointer = _get_sync_checkpointer()


# ── Async checkpointer (Streamlit astream_events) ─────────────────────────────
# Must be called inside a running event loop (e.g. inside an async function).

async def create_async_checkpointer() -> AsyncSqliteSaver:
    """Create an AsyncSqliteSaver backed by the same SQLite DB.

    MUST be called inside a running asyncio event loop (e.g. from an async
    function). Uses aiosqlite for async-compatible connection.
    For use with agent_graph.astream_events() in Streamlit.
    """
    import aiosqlite
    conn = await aiosqlite.connect(_DB_PATH)
    return AsyncSqliteSaver(conn)
