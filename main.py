"""
Agentic Property — entry point.

Usage:
    uv run python main.py

Runs a smoke test with fake property data to verify the P2 pipeline:
    comparison_engine → reflection → answer_generation
"""

import logging

from src.agents.graph import agent_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    # ── Sample state (mimics what tool_router would inject) ───────────────────
    initial_state = {
        "query": "I'm looking for a 2-bedroom apartment in Dubai Marina, budget AED 1.8M, with sea view.",
        "parsed_query": {
            "location": "Dubai Marina",
            "property_type": "apartment",
            "bedrooms": 2,
            "budget_aed": 1_800_000,
            "amenities": ["sea view"],
        },
        "retrieved_properties": [
            {
                "id": "prop-001",
                "title": "Marina Crest — 2BR Sea View",
                "price": 1_750_000,
                "area_sqm": 110,
                "location": "Dubai Marina",
                "bedrooms": 2,
                "amenities": ["sea view", "gym", "pool"],
            },
            {
                "id": "prop-002",
                "title": "Marina Gate 2 — 2BR City View",
                "price": 1_850_000,
                "area_sqm": 105,
                "location": "Dubai Marina",
                "bedrooms": 2,
                "amenities": ["gym", "pool"],
            },
            {
                "id": "prop-003",
                "title": "Jumeirah Living — 2BR Canal View",
                "price": 1_650_000,
                "area_sqm": 98,
                "location": "JBR",
                "bedrooms": 2,
                "amenities": ["canal view", "concierge"],
            },
        ],
        "comparison_result": None,
        "reflection_output": None,
        "needs_retry": False,
        "retry_tool": None,
        "retry_count": 0,
        "final_answer": None,
    }

    print("\n" + "=" * 60)
    print("Running Agentic Property pipeline...")
    print("=" * 60 + "\n")

    final_state = agent_graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(final_state.get("final_answer", "No answer generated."))


if __name__ == "__main__":
    main()
