"""Long-term SQLite checkpoint saver for LangGraph agent memory."""

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

_MEMORY_DIR = Path(__file__).resolve().parent
_DB_PATH = str(_MEMORY_DIR / "chat_history.db")


def _create_checkpointer() -> SqliteSaver:
    """Create a new SqliteSaver backed by a project-local SQLite DB."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)


# Singleton — call _get_checkpointer() to retrieve the shared instance
def _get_checkpointer() -> SqliteSaver:
    if not hasattr(_get_checkpointer, "_instance"):
        _get_checkpointer._instance = _create_checkpointer()
    return _get_checkpointer._instance


# Module-level convenience accessor
checkpointer = _get_checkpointer()
