"""
LangGraph StateGraph — full pipeline with dual-path topology.

Graph topology:
                              ┌── END (is_relevant=False, final_answer set)
                              │
START ──► memory ──► query_relevancy ──► query_understanding
                                                 │
                                                 ▼
                                     ┌───────────┴───────────┐
                                     │ route="query_routing"  │ route="web_search"
                                     ▼                         ▼
                               query_routing            web_search (sub-graph)
                                     │                         │
                                     ▼                         │
                            comparison_engine                  │
                                     │                         │
                                     ▼                         │
                                 reflection                    │
                                     │                         │
                                     └─────────┬───────────────┘
                                               ▼
                                        answer_generation
                                               │
                                              END

Reflection is a deterministic terminal audit. Transient transport retries belong
inside the MCP client and never repeat the graph retrieval loop.
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
from src.nodes.memory import memory_node
from src.memory.long_term_memory import checkpointer as _default_checkpointer

def build_graph(checkpointer=None):
    """
    Build and compile the full agent pipeline.

    Args:
        checkpointer: Optional checkpointer override.
                      If None, defaults to the module-level sync SqliteSaver.
                      If False, compiles without any checkpointer (stateless).
                      Pass an AsyncSqliteSaver for async SSE streaming.

    Returns:
        A compiled LangGraph application ready to invoke.
    """
    if checkpointer is False:
        cp = None
    elif checkpointer is None:
        cp = _default_checkpointer
    else:
        cp = checkpointer

    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("memory", memory_node)
    graph.add_node("query_relevancy", query_relevancy_node)
    graph.add_node("query_understanding", query_understanding_node)
    graph.add_node("query_routing", query_routing_node)
    graph.add_node("web_search", create_web_search_agent())
    graph.add_node("comparison_engine", comparison_engine_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("answer_generation", answer_generation_node)

    # ── Entry → bounded memory restoration → scope classification ─────────────
    graph.add_edge(START, "memory")
    graph.add_edge("memory", "query_relevancy")

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
            "answer_generation": "answer_generation",
        },
    )
    graph.add_edge("comparison_engine", "reflection")

    graph.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {
            "answer_generation": "answer_generation",
        },
    )

    # ── web_search path ───────────────────────────────────────────────────────
    graph.add_edge("web_search", "answer_generation")

    # ── Both paths converge here ──────────────────────────────────────────────
    graph.add_edge("answer_generation", END)

    return graph.compile(checkpointer=cp)


# Singleton — import `agent_graph` wherever you need to invoke the pipeline
agent_graph = build_graph()
