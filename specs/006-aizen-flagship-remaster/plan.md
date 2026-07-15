# Implementation plan

## Architecture spine

Keep `memory → query_relevancy → query_understanding → query_routing → comparison_engine → reflection → answer_generation` for property search and the separate `web_search` branch for cited informational questions. The search submission authorizes the interpreted brief; later edits are committed only by **Apply & rerun**. Routing translates supported hard criteria to MCP filters. Comparison and reflection are deterministic. Answer generation returns validated property/criterion references for property search and cited prose for web research.

## Delivery order

1. Lock public contracts and remove false unit-level claims.
2. Replace LLM scoring and opinion-based reflection with deterministic evaluation and audit.
3. Complete APIs for brief interpretation, runs, conversations, context, and area comparison.
4. Recompose React around one-action interpretation/run, compact correction, completion takeover, ranked homes, comparison, map, affordability, area evidence, and dossier.
5. Add recruiter case study, documentation, preflight, browser E2E, cancellation, recent live reruns, and clean-clone runbook.
6. Run every release gate and publish only verified counts.
7. Final presentation pass: use **Find what fits. See what matters.** as primary motto, **Search less. Decide better.** as supporting line, keep warm editorial surfaces and selective dark cinematic moments, and keep visible copy consistent across cards, drawers, trace, evidence, and dossier.
8. Final recruiter pass: keep README diagrams aligned with the graph source, link to the deep documentation set, and publish only release-gate facts.

## Constraints for Luna

- Do not add a router, state library, component framework, PDF dependency, or paid service.
- Do not reintroduce `total_building_area_sqft` as unit size or `total_parking_spaces` as dedicated parking.
- Do not use historical rows when active results are empty.
- Do not add a graph retry edge from reflection to routing.
- Do not calculate fit, valuation, fees, or market benchmarks in prompts.
- Do not show a criterion as verified if its field is missing.
- Do not call fit or evidence coverage AI confidence.
- Do not replay saved answers when rerunning a recent search.
- Keep PostgreSQL primary and SQLite fallback behavior intact.
