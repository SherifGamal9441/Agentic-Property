# Lazy imports — the MCP client has heavy dependencies (yaml, mcp SDK)
# that aren't available in all contexts (e.g. data-service container).
# Only import when the client functions are actually accessed.


def __getattr__(name):
    _exports = {
        "search_historical",
        "search_active",
        "convert_currency",
        "search_historical_sync",
        "search_active_sync",
        "convert_currency_sync",
    }
    if name in _exports:
        from src.mcp.client import (
            search_historical,
            search_active,
            convert_currency,
            search_historical_sync,
            search_active_sync,
            convert_currency_sync,
        )
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
