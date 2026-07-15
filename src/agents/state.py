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
  reflection_output                            → set by reflection
  final_answer                                → set by answer_generation (all paths)
                                                 also carries rejection messages when
                                                 is_relevant=False — the API layer
                                                 always reads this one field.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.buyer_brief import BuyerBrief
from src.buyer_guidance import PropertyGuidance


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

    parsed_query: dict = Field(default_factory=dict)
    """Structured intent extracted by query_understanding.
    Expected keys: location, budget, property_type, bedrooms, amenities, currency, etc."""

    # ── Currency conversion (set by query_routing) ─────────────────────────────
    currency: str = "AED"
    """Currency code the user mentioned (default AED). Used by query_routing
    to convert price filters to AED before searching, and by answer_generation
    to show dual-currency prices."""

    exchange_rate: float | None = None
    """Exchange rate from user currency to AED (1 user_currency = X AED).
    Set by query_routing when currency != AED. None when no conversion needed."""

    # ── Set by query_routing ──────────────────────────────────────────────────
    data_source: str | None = None
    """Which tool tier was used: "active" | "historical" """

    data_intent: str | None = None
    """How downstream nodes must treat the data:
       "recommend"     → properties are current; comparison engine scores and recommends
       "insights_only" → historical data only; properties may be sold.
                         comparison engine derives market insights, does NOT recommend."""

    retrieved_properties: list[dict] = Field(default_factory=list)
    """Properties returned by the active tool.
    Each dict should contain at minimum: id, title, price, area_sqm, location."""

    # ── Set by web_search sub-graph (teammate) ────────────────────────────────
    web_search_query: str = ""
    """Rewritten web search query."""

    web_search_results: list[dict] = Field(default_factory=list)
    """Raw results from the web search tool."""

    web_search_summary: str = ""
    """LLM-generated summary of web search results."""

    # ── Set by comparison_engine ──────────────────────────────────────────────
    comparison_result: dict | None = None
    """Deterministic comparison output.
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
    """Audit of comparison identities, source fields, and score arithmetic."""

    # ── Set by answer_generation ──────────────────────────────────────────────
    final_answer: str | None = None
    """The response delivered to the user — populated by every terminal path:
       - Recommendation / insights (query_routing path)
       - General question answer  (web_search path)
       - Out-of-scope explanation (is_relevant=False path)
    The API layer always reads this one field."""

    # ── Conversation memory ──────────────────────────────────────────────────
    conversation_history: list[dict] = Field(default_factory=list)
    """Accumulated user/assistant message pairs across turns.
    Shape: [{"role": "user"|"assistant", "content": str}, ...]"""

    conversation_context: str = ""
    """Pre-formatted string of recent conversation history, ready to inject
    into LLM prompts. Built by the memory node at the start of each turn."""
    buyer_brief: BuyerBrief | None = None
    """Buyer-confirmed structured contract. Property runs require this value."""

    buyer_guidance: PropertyGuidance | None = None
    """Validated property references used by the decision UI."""

    candidate_count: int = 0
    audited_count: int = 0
    withheld_count: int = 0
