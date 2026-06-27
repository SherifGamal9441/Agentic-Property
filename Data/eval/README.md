# Evaluation Data

Two test suites for the Agentic Property LangGraph agent.

## Files

| File | Type | What it tests |
|------|------|---------------|
| `structural_tests.json` | 50 test cases | Objective state assertions: route, data_source, data_intent, parsed_query, rejection |
| `quality_tests.json` | 50 test cases | LLM-as-judge quality evaluation: answer correctness, structure, language, helpfulness |

## How structural tests work

Each case invokes `agent_graph.invoke({"query": query})` and asserts the final state matches `expected`:

```python
result = agent_graph.invoke({"query": test["query"]})
for key, value in test["expected"].items():
    assert result[key] == value, f"{test['id']}: {key} expected {value}, got {result[key]}"
```

## How quality tests work

Each case invokes the agent, then sends the `query` + `final_answer` to a **judge LLM** with the rubric criteria:

```python
result = agent_graph.invoke({"query": test["query"]})
judge_prompt = f"""
Evaluate this answer on the given criteria.
Query: {query}
Answer: {final_answer}
Criteria: {criteria}
Return: {{"score": 0.0-1.0, "passes": [...], "fails": [...], "critique": "..."}}
"""
judge_response = judge_llm.invoke(judge_prompt)
pass if judge_response.score >= min_score
```

## Adding new tests

1. Add to `structural_tests.json` for objective behavior tests
2. Add to `quality_tests.json` for answer quality tests
3. Include appropriate `tags` for filtering (arabic, currency, rejection, etc.)

## Running

```bash
# Run all tests
python scripts/run_eval.py

# Run specific tag
python scripts/run_eval.py --tag currency

# Run quality tests only
python scripts/run_eval.py --type quality
```

## Tag reference

- `basic` — Standard property search
- `general` / `web_search` — General knowledge questions
- `comparison` — Compare two areas or properties
- `rejection` — Out-of-scope queries
- `currency` — Currency conversion tests
- `arabic` / `chinese` / `french` / `spanish` / `german` / `russian` — Language tests
- `off-plan` / `ready` — Completion status
- `furnished` / `unfurnished` — Furnishing status
- `budget` — Budget-focused queries
- `luxury` — High-end property queries
- `investment` — Investment-related queries
- `edge_case` — Boundary or unusual queries
- `villa` / `apartment` / `townhouse` / `studio` / `penthouse` — Property type
