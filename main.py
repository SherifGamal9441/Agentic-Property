"""
Agentic Property — entry point / smoke test.

Tests all three graph paths with fake data:
  Path A — query_routing → comparison (recommendation)
  Path B — web_search (general question)
  Path C — irrelevant query (rejection)

Usage:
    uv run python main.py
"""

import logging

from src.agents.graph import agent_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

_DIVIDER = "=" * 60


def run_test(label: str, query: str) -> None:
    print(f"\n{_DIVIDER}")
    print(f"TEST: {label}")
    print(f"QUERY: {query}")
    print(_DIVIDER)

    initial_state = {"query": query}
    final_state = agent_graph.invoke(initial_state)

    print(f"\n{_DIVIDER}")
    print("FINAL ANSWER")
    print(_DIVIDER)
    print(final_state.get("final_answer") or "(no answer)")
    print(f"\nRoute taken : {final_state.get('route', 'n/a (rejected before routing)')}")
    print(f"Data source : {final_state.get('data_source', 'n/a')}")
    print(f"Data intent : {final_state.get('data_intent', 'n/a')}")
    print(f"Relevant    : {final_state.get('is_relevant', True)}")
    # lets visualise the graph
    agent_graph.get_graph().draw_mermaid_png(output_file_path="current_full_graph.png")

def main() -> None:
    # Path A — recommendation query (query_routing path, stub tools → no-results response)
    run_test(
        label="Path A — Property recommendation (stub tools active)",
        query="I'm looking for a 2-bedroom apartment in Dubai Marina with a sea view, budget AED 1.8M.",
    )

    # Path B — general question (web_search path)
    run_test(
        label="Path B — General question (web_search path)",
        query="What are the current rental trends in Downtown Dubai?",
    )

    # Path C — irrelevant query (rejection path)
    run_test(
        label="Path C — Irrelevant query (rejection)",
        query="What's the best recipe for pasta carbonara?",
    )


if __name__ == "__main__":
    main()
