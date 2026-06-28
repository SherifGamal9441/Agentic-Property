"""
LangGraph StateGraph — full pipeline with dual-path topology.

Graph topology:
                              ┌── END (is_relevant=False, final_answer set)
                              │
START ──► query_relevancy ──► query_understanding
                                       │
               ┌───────────────────────┴─────────────────────────┐
               │ route="query_routing"                            │ route="web_search"
               ▼                                                  ▼
         query_routing                                     web_search (sub-graph)
               │                                                  │
               ▼                                                  │
      comparison_engine                                           │
               │                                                  │
               ▼                                                  │
           reflection                                             │
               │                                                  │
               └──────────────────┬───────────────────────────────┘
                                  ▼
                         answer_generation
                                  │
                                 END

Retry loop (reflection → query_routing):
    If reflection sets needs_retry=True and retry_count < max_retries,
    the edge routes back to query_routing to try again with different tool tier.
"""

from langgraph.graph import END, START, StateGraph

from src.agents.state import AgentState
from src.nodes.answer_generation import answer_generation_node
from src.nodes.comparison_engine import comparison_engine_node
from src.nodes.query_relevancy import query_relevancy_node, route_after_relevancy
from src.nodes.query_routing import query_routing_node, route_after_routing
from src.nodes.query_understanding import query_understanding_node, route_after_understanding
from src.nodes.reflection import reflection_node, route_after_reflection
from src.nodes.web_search import create_web_search_agent
from src.memory.long_term_memory import checkpointer

def build_graph() -> StateGraph:
    """
    Build and compile the full agent pipeline.

    Returns:
        A compiled LangGraph application ready to invoke.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("query_relevancy", query_relevancy_node)
    graph.add_node("query_understanding", query_understanding_node)
    graph.add_node("query_routing", query_routing_node)
    graph.add_node("web_search", create_web_search_agent())
    graph.add_node("comparison_engine", comparison_engine_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("answer_generation", answer_generation_node)

    # ── Entry ─────────────────────────────────────────────────────────────────
    graph.add_edge(START, "query_relevancy")

    # ── After relevancy: proceed or end ───────────────────────────────────────
    graph.add_conditional_edges(
        "query_relevancy",
        route_after_relevancy,
        {
            "query_understanding": "query_understanding",
            "end": END,
        },
    )

    # ── After understanding: split into two paths ─────────────────────────────
    graph.add_conditional_edges(
        "query_understanding",
        route_after_understanding,
        {
            "query_routing": "query_routing",
            "web_search": "web_search",
        },
    )

    # ── query_routing path ────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "query_routing",
        route_after_routing,
        {
            "comparison_engine": "comparison_engine",
            "web_search": "web_search",
        },
    )
    graph.add_edge("comparison_engine", "reflection")

    graph.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {
            "answer_generation": "answer_generation",
            # Retry: route back to query_routing to try the next tool tier
            "tool_router": "query_routing",
        },
    )

    # ── web_search path ───────────────────────────────────────────────────────
    graph.add_edge("web_search", "answer_generation")

    # ── Both paths converge here ──────────────────────────────────────────────
    graph.add_edge("answer_generation", END)

    return graph.compile(checkpointer=checkpointer)


# Singleton — import `agent_graph` wherever you need to invoke the pipeline
agent_graph = build_graph()
