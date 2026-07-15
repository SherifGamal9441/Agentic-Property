# ADR 004: MCP data boundary

**Status:** Accepted

Property retrieval remains behind typed MCP tools and a separate data service. The graph does not query database tables directly. This keeps data access replaceable, observable, and independently testable.
