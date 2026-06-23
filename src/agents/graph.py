"""
LangGraph StateGraph — wires the three P2 nodes owned by this team.

Graph topology (your nodes only):

    comparison_engine
          │
          ▼
       reflection ──── needs_retry=True ──► [tool_router — upstream team]
          │
     needs_retry=False
          │
          ▼
    answer_generation
          │
          ▼
         END

Entry point: "comparison_engine"
(The upstream query_understanding + tool_router nodes invoke this sub-graph
 by seeding the state with `parsed_query` and `retrieved_properties`.)

Compile once at module level so the graph is reused across calls.
"""

from langgraph.graph import END, StateGraph, START

from src.agents.state import AgentState
from src.nodes.answer_generation import answer_generation_node
from src.nodes.comparison_engine import comparison_engine_node
from src.nodes.reflection import reflection_node, route_after_reflection
from src.nodes.web_search import create_web_search_agent


def build_graph() -> StateGraph:
    """
    Build and compile the P2 agent core graph.

    Returns:
        A compiled LangGraph application ready to invoke.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("comparison_engine", comparison_engine_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("answer_generation", answer_generation_node)
    graph.add_node("web_search", create_web_search_agent())

    # ── Define edges ──────────────────────────────────────────────────────────
    graph.add_edge(START, "comparison_engine")
    graph.add_edge("comparison_engine", "reflection")

    # Conditional: reflection decides whether to pass or signal a retry
    graph.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {
            # Comparison passed — proceed to final answer
            "answer_generation": "answer_generation",
            # Comparison failed — signal upstream; we end our sub-graph here
            # The upstream team's tool_router picks up `needs_retry` from state
            "tool_router": END,
        },
    )
    graph.add_edge("answer_generation", END)

    return graph.compile()


# Singleton — import `agent_graph` wherever you need to invoke the pipeline
agent_graph = build_graph()
