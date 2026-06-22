"""
AgentState — the single source of truth flowing through every LangGraph node.

Ownership map:
  query, parsed_query, retrieved_properties  → set by upstream nodes (query_understanding, tool_router)
  comparison_result                           → set by comparison_engine node (this team)
  reflection_output                           → set by reflection node (this team)
  needs_retry, retry_tool, retry_count        → set by reflection; READ by tool_router (upstream team)
  final_answer                                → set by answer_generation node (this team)
"""

from pydantic import BaseModel, ConfigDict


class AgentState(BaseModel):
    model_config = ConfigDict(extra="allow")

    # ── Set by upstream nodes ─────────────────────────────────────────────────
    query: str = ""
    """Raw user input exactly as received."""

    parsed_query: dict = {}
    """Structured intent extracted by the query_understanding node.
    Expected keys: location, budget, property_type, bedrooms, amenities, etc."""

    retrieved_properties: list[dict] = []
    """List of property records returned by whichever tool the router chose.
    Each dict should contain at minimum: id, title, price, area_sqm, location."""

    # ── Set by comparison_engine ──────────────────────────────────────────────
    comparison_result: dict | None = None
    """LLM comparison output.
    Shape: {
        properties: [
            {
                id: str,
                title: str,
                fit_score: float,          # 0.0 – 1.0
                matched_criteria: list[str],
                unmatched_criteria: list[str],
                price_assessment: "below_market" | "fair" | "above_market",
            }
        ]
    }"""

    # ── Set by reflection ─────────────────────────────────────────────────────
    reflection_output: dict | None = None
    """Audit of the comparison engine's output.
    Shape: {
        ok: bool,               # True if comparison is complete and consistent
        issues: list[str],      # list of detected problems (empty when ok=True)
        confidence: float,      # 0.0 – 1.0 overall confidence in the comparison
    }"""

    needs_retry: bool = False
    """True when reflection finds the comparison insufficient and retry is warranted."""

    retry_tool: str | None = None
    """Which tool to try next: "vector" | "sql" | "bayut" | None."""

    retry_count: int = 0
    """Number of retries already consumed. Caps at settings.max_retries."""

    # ── Set by answer_generation ──────────────────────────────────────────────
    final_answer: str | None = None
    """Streamed final answer delivered to the user."""
