"""
Run LangSmith evaluations against the uploaded datasets.

Two evaluation modes:
  --type structural : Objective state assertions (is_relevant, route, parsed_query, etc.)
  --type quality    : LLM-as-judge quality scoring against rubric criteria

Usage:
    python scripts/run_langsmith_eval.py                           # run both
    python scripts/run_langsmith_eval.py --type structural          # structural only
    python scripts/run_langsmith_eval.py --type quality --tag currency  # filter by tag
    python scripts/run_langsmith_eval.py --max-concurrency 8        # parallelism

Prerequisites:
    1. Set LANGSMITH_API_KEY in .env
    2. Run: python scripts/upload_eval_datasets.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from langsmith import Client, traceable
from langsmith.schemas import Run, Example
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

DATASET_NAMES = {
    "structural": "agentic-property-structural",
    "quality": "agentic-property-quality",
}


# ---------------------------------------------------------------------------
# Target function — wraps the agent graph so LangSmith can trace every run
# ---------------------------------------------------------------------------

from src.agents.graph import build_graph
# Compile a stateless graph (no SQLite checkpointer) for evaluation to run queries in parallel cleanly
agent_graph_eval = build_graph(checkpointer=False)


@traceable(name="agentic-property-agent")
def agent_target(inputs: dict) -> dict:
    """Invoke the LangGraph agent and return the full final state."""
    result = agent_graph_eval.invoke({"query": inputs["query"]})
    return result


# ---------------------------------------------------------------------------
# Structural evaluators — each checks one field in the agent state
# ---------------------------------------------------------------------------

def _safe_get(outputs: dict, key: str, default: Any = None) -> Any:
    return outputs.get(key, default) if isinstance(outputs, dict) else default


def is_relevant_eval(outputs: dict, reference_outputs: dict) -> dict:
    expected = reference_outputs["expected"].get("is_relevant")
    if expected is None:
        return {"key": "is_relevant", "score": None, "comment": "No assertion for this field"}
    actual = _safe_get(outputs, "is_relevant")
    passed = actual == expected
    return {"key": "is_relevant", "score": float(passed), "comment": f"expected={expected}, got={actual}"}


def route_eval(outputs: dict, reference_outputs: dict) -> dict:
    expected = reference_outputs["expected"].get("route")
    if expected is None:
        return {"key": "route", "score": None, "comment": "No assertion for this field"}
    actual = _safe_get(outputs, "route")
    passed = actual == expected
    return {"key": "route", "score": float(passed), "comment": f"expected={expected}, got={actual}"}


def data_source_eval(outputs: dict, reference_outputs: dict) -> dict:
    expected = reference_outputs["expected"].get("data_source")
    if expected is None:
        return {"key": "data_source", "score": None, "comment": "No assertion for this field"}
    actual = _safe_get(outputs, "data_source")
    passed = actual == expected
    return {"key": "data_source", "score": float(passed), "comment": f"expected={expected}, got={actual}"}


def data_intent_eval(outputs: dict, reference_outputs: dict) -> dict:
    expected = reference_outputs["expected"].get("data_intent")
    if expected is None:
        return {"key": "data_intent", "score": None, "comment": "No assertion for this field"}
    actual = _safe_get(outputs, "data_intent")
    passed = actual == expected
    return {"key": "data_intent", "score": float(passed), "comment": f"expected={expected}, got={actual}"}


def parsed_query_eval(outputs: dict, reference_outputs: dict) -> dict:
    expected_pq = reference_outputs["expected"].get("parsed_query")
    if not expected_pq:
        return {"key": "parsed_query", "score": None, "comment": "No parsed_query assertion"}
    actual_pq = _safe_get(outputs, "parsed_query", {})
    if not isinstance(actual_pq, dict):
        return {"key": "parsed_query", "score": 0.0, "comment": f"parsed_query is not a dict: {type(actual_pq)}"}
    mismatches = []
    for key, expected_val in expected_pq.items():
        actual_val = actual_pq.get(key)
        if actual_val != expected_val:
            mismatches.append(f"{key}: expected={expected_val}, got={actual_val}")
    if not mismatches:
        return {"key": "parsed_query", "score": 1.0, "comment": "All fields match"}
    return {
        "key": "parsed_query",
        "score": 0.0,
        "comment": "; ".join(mismatches),
    }


def rejection_eval(outputs: dict, reference_outputs: dict) -> dict:
    expected_contains = reference_outputs["expected"].get("final_answer_contains")
    if not expected_contains:
        return {"key": "rejection", "score": None, "comment": "No rejection assertion"}
    final_answer = _safe_get(outputs, "final_answer", "") or ""
    final_answer_lower = final_answer.lower()
    missing = [s for s in expected_contains if s.lower() not in final_answer_lower]
    if not missing:
        return {"key": "rejection", "score": 1.0, "comment": "All expected phrases present"}
    return {
        "key": "rejection",
        "score": 0.0,
        "comment": f"Missing phrases: {missing}",
    }


STRUCTURAL_EVALUATORS = [
    is_relevant_eval,
    route_eval,
    data_source_eval,
    data_intent_eval,
    parsed_query_eval,
    rejection_eval,
]


# ---------------------------------------------------------------------------
# Quality evaluator — LLM as judge
# ---------------------------------------------------------------------------

class JudgeResult(BaseModel):
    score: float
    passes: list[str] = []
    fails: list[str] = []
    critique: str = ""


def _build_judge_prompt(query: str, answer: str, criteria: list[str]) -> str:
    criteria_text = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(criteria))
    return f"""You are evaluating the quality of an AI assistant's answer about Dubai real estate.

User Query: {query}

Assistant Answer: {answer}

Evaluation Criteria:
{criteria_text}

Score each criterion and return an overall score from 0.0 to 1.0.
Return a JSON object with:
  - "score": float (0.0 to 1.0, overall quality)
  - "passes": list of criteria that were met (as strings)
  - "fails": list of criteria that were not met (as strings)
  - "critique": brief explanation of your assessment

Respond ONLY with the JSON object, no other text."""


def llm_judge_eval(outputs: dict, reference_outputs: dict) -> dict:
    criteria = reference_outputs.get("criteria", [])
    min_score = reference_outputs.get("min_score", 0.5)
    answer = _safe_get(outputs, "final_answer", "") or ""

    if not answer.strip():
        return {
            "key": "llm_judge",
            "score": 0.0,
            "comment": "No final_answer produced by agent",
        }

    prompt = _build_judge_prompt(
        query=outputs.get("query", ""),
        answer=answer,
        criteria=criteria,
    )

    try:
        from src.llm.factory import get_llm
        judge_llm = get_llm(streaming=False)
        response = judge_llm.invoke(prompt)
        raw = response.content if hasattr(response, "content") else str(response)

        import re
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(raw)

        result = JudgeResult(**parsed)
        passed = result.score >= min_score
        return {
            "key": "llm_judge",
            "score": float(passed),
            "comment": f"score={result.score:.2f} (min={min_score}), fails={result.fails}, critique={result.critique}",
        }
    except Exception as exc:
        log.warning("Judge LLM error: %s", exc)
        return {
            "key": "llm_judge",
            "score": 0.0,
            "comment": f"Judge error: {exc}",
        }


QUALITY_EVALUATORS = [llm_judge_eval]


# ---------------------------------------------------------------------------
# Tag filter helper
# ---------------------------------------------------------------------------

def _make_tag_filter(tag: str | None):
    """Return a filter function that only runs examples matching the given tag."""
    if tag is None:
        return None

    def _filter(run: Run, example: Example) -> bool:
        example_tags = example.inputs.get("tags", [])
        return tag in example_tags

    return _filter


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_evaluation(
    client: Client,
    eval_type: str,
    tag: str | None = None,
    max_concurrency: int = 4,
) -> None:
    dataset_name = DATASET_NAMES[eval_type]

    if eval_type == "structural":
        evaluators = STRUCTURAL_EVALUATORS
        experiment_prefix = "structural"
    else:
        evaluators = QUALITY_EVALUATORS
        experiment_prefix = "quality"

    print(f"\n{'=' * 60}")
    print(f"Running {eval_type} evaluation on dataset '{dataset_name}'")
    if tag:
        print(f"  Filter: tag='{tag}'")
    print(f"  Concurrency: {max_concurrency}")
    print(f"  Evaluators: {[e.__name__ for e in evaluators]}")
    print(f"{'=' * 60}\n")

    eval_kwargs: dict[str, Any] = {
        "data": dataset_name,
        "evaluators": evaluators,
        "experiment_prefix": experiment_prefix,
        "max_concurrency": max_concurrency,
        "description": f"Agentic Property {eval_type} evaluation",
    }

    if tag:
        eval_kwargs["evaluator_kwarg_kwargs"] = {}
        eval_kwargs["filter"] = _make_tag_filter(tag)

    results = client.evaluate(
        agent_target,
        **eval_kwargs,
    )

    print(f"\nResults:")
    try:
        df = results.to_pandas()
        print(df.to_string(index=False))
    except Exception:
        print(f"  Experiment URL: {results.experiment_url() if hasattr(results, 'experiment_url') else 'see LangSmith dashboard'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run LangSmith evaluations for the Agentic Property agent.",
    )
    parser.add_argument(
        "--type",
        choices=["structural", "quality", "both"],
        default="both",
        help="Which evaluation to run (default: both)",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Filter examples by tag (e.g. 'currency', 'arabic', 'rejection')",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=4,
        help="Max concurrent agent invocations (default: 4)",
    )
    args = parser.parse_args()

    # Pre-flight: warn if data service is unreachable (structural evals need it)
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/health", timeout=3)
        if resp.status_code == 200:
            log.info("Data service reachable at http://localhost:8000")
        else:
            log.warning("Data service returned %d — active listing tests will fail", resp.status_code)
    except Exception:
        log.warning("Data service unreachable at http://localhost:8000 — "
                     "active listing tests will fail. Start it: uv run scripts/run_data_service.py")

    client = Client()

    types_to_run = (
        ["structural", "quality"]
        if args.type == "both"
        else [args.type]
    )

    for et in types_to_run:
        run_evaluation(client, et, tag=args.tag, max_concurrency=args.max_concurrency)

    print(f"\nDone! View results at https://smith.langchain.com")


if __name__ == "__main__":
    main()
