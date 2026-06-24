"""
AgentState — the single source of truth flowing through every LangGraph node.

Ownership map:
  query                                       → entry point, set by the caller
  is_relevant, route                          → set by query_relevancy / query_understanding
  parsed_query                                → set by query_understanding
  data_source, data_intent                    → set by query_routing
  retrieved_properties                        → set by query_routing
  web_search_*                                → set by web_search sub-graph (teammate)
  comparison_result                           → set by comparison_engine
  reflection_output, needs_retry, retry_count → set by reflection
  final_answer                                → set by answer_generation (all paths)
                                                 also carries rejection messages when
                                                 is_relevant=False — the API layer
                                                 always reads this one field.
"""

from pydantic import BaseModel, ConfigDict


class AgentState(BaseModel):
    model_config = ConfigDict(extra="allow")

    # ── Entry ─────────────────────────────────────────────────────────────────
    query: str = ""
    """Raw user input exactly as received."""

    # ── Set by query_relevancy ────────────────────────────────────────────────
    is_relevant: bool = True
    """False when the query is out of scope (not Dubai, not property-related).
    When False the graph ends immediately; final_answer carries the explanation."""

    # ── Set by query_understanding ────────────────────────────────────────────
    route: str | None = None
    """Which path to take after query_understanding:
       "query_routing"  → user wants property recommendations / comparisons
       "web_search"     → user has a general question about Dubai real estate"""

    parsed_query: dict = {}
    """Structured intent extracted by query_understanding.
    Expected keys: location, budget, property_type, bedrooms, amenities, etc."""

    # ── Set by query_routing ──────────────────────────────────────────────────
    data_source: str | None = None
    """Which tool tier was used: "cached" | "historical" """

    data_intent: str | None = None
    """How downstream nodes must treat the data:
       "recommend"     → properties are current; comparison engine scores and recommends
       "insights_only" → historical data only; properties may be sold.
                         comparison engine derives market insights, does NOT recommend."""

    retrieved_properties: list[dict] = []
    """Properties returned by the active tool.
    Each dict should contain at minimum: id, title, price, area_sqm, location."""

    # ── Set by web_search sub-graph (teammate) ────────────────────────────────
    web_search_query: str = ""
    """Rewritten web search query."""

    web_search_results: list[dict] = []
    """Raw results from the web search tool."""

    web_search_summary: str = ""
    """LLM-generated summary of web search results."""

    # ── Set by comparison_engine ──────────────────────────────────────────────
    comparison_result: dict | None = None
    """LLM comparison output.
    Shape: {
        properties: [
            {
                id: str,
                title: str,
                fit_score: float,           # 0.0 – 1.0
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
        ok: bool,
        issues: list[str],
        confidence: float,
    }"""

    needs_retry: bool = False
    """True when reflection finds the comparison insufficient and retry is warranted."""

    retry_count: int = 0
    """Number of retries consumed. Caps at settings.max_retries."""

    # ── Set by answer_generation ──────────────────────────────────────────────
    final_answer: str | None = None
    """The response delivered to the user — populated by every terminal path:
       - Recommendation / insights (query_routing path)
       - General question answer  (web_search path)
       - Out-of-scope explanation (is_relevant=False path)
    The API layer always reads this one field."""
