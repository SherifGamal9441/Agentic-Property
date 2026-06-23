"""
End-to-End Pipeline Test with Fake Data.

This test patches the two tool stubs in `query_routing.py` to return fake properties.
It does NOT mock the LLMs. This allows testing the full graph logic (query understanding,
routing, comparison, reflection, answer generation) with realistic data exactly as it 
would run in production.

Usage:
    uv run pytest tests/agents/test_pipeline_e2e.py -s
    (The -s flag ensures you can see the streaming text and print statements)
"""

import pytest
from unittest.mock import patch

from src.agents.graph import agent_graph

FAKE_CACHED_PROPERTIES = [
    {
        "id": "prop-001",
        "title": "Marina Crest 2BR Apartment",
        "price": 1_750_000,
        "area_sqm": 110.5,
        "location": "Dubai Marina",
        "bedrooms": 2,
        "amenities": ["sea view", "gym", "pool"],
    },
    {
        "id": "prop-002",
        "title": "Jumeirah Living 2BR",
        "price": 2_100_000,
        "area_sqm": 130.0,
        "location": "Jumeirah",
        "bedrooms": 2,
        "amenities": ["canal view", "maid room"],
    }
]

# We mark this so you know it's a slow test that requires the LLM
@pytest.mark.slow
@patch("src.nodes.query_routing._call_historical_tool", return_value=[])
@patch("src.nodes.query_routing._call_cached_tool", return_value=FAKE_CACHED_PROPERTIES)
def test_full_pipeline_with_real_llm_and_fake_data(mock_cached, mock_historical):
    """
    Test the pipeline with fake data and the REAL LLM.
    """
    query = "I'm looking for a 2-bedroom apartment in Dubai Marina with a sea view, budget AED 1.8M."
    initial_state = {"query": query}
    
    print(f"\n[Test] Sending query: '{query}'")
    print("[Test] Injecting 2 fake properties into the cached tool...")
    
    # 1. Invoke the graph
    final_state = agent_graph.invoke(initial_state)
    
    # 2. Assertions
    # We assert on the deterministic parts of the graph flow
    assert final_state["is_relevant"] is True
    assert final_state["route"] == "query_routing"
    assert final_state["data_source"] == "cached"
    assert final_state["data_intent"] == "recommend"
    assert final_state["comparison_result"] is not None
    
    props = final_state["comparison_result"].get("properties", [])
    assert len(props) > 0, "The LLM failed to return any properties in the comparison"
    
    assert final_state["final_answer"] is not None
    assert len(final_state["final_answer"]) > 50

    print("\n[Test] --- FINAL ANSWER ---")
    print(final_state["final_answer"])
    print("[Test] --------------------")
