# Implementation Plan: Buyer Intelligence Roadmap

**Branch**: none | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

## Summary

Implement the non-gated buyer-decision slice: structured brief context, factual comparison and trade-offs, buyer-entered scenarios, historical area context, map grouping, saved-search diffs, local feedback, and data-health visibility. Cross-device identity and outbound alerts remain deferred by the specification.

## Technical Context

**Language/Version**: TypeScript frontend; Python service/API  
**Primary Dependencies**: Existing React, FastAPI, SQLAlchemy, browser storage  
**Storage**: Existing listing database and browser-local research/feedback  
**Testing**: Existing frontend tests and pytest  
**Target Platform**: Browser plus existing containerized services  
**Project Type**: Web application  
**Constraints**: No paid map, no fictional market data, no silent fees, no new identity system  
**Scope**: Extend existing contracts and UI only; no new external provider

## Constitution Check

No project constitution file exists. Pass: calculations and market summaries are deterministic; generated agent text remains explanation, not factual source of truth.

## Design Decisions

- Submit structured buyer preferences as explicit brief context alongside free text, avoiding a new graph topology.
- Derive comparison unit values, cost totals, criteria gaps, map grouping, and saved-search changes in deterministic application code.
- Aggregate historical context in the existing data service and expose it through the agent API, keeping the browser on its existing API boundary.
- Keep feedback local in this iteration; it is bounded and visible to the buyer. Operator-facing persistence needs a separate retention decision.

## Project Structure

```text
src/data_service/app.py      # Historical aggregate and health metadata
src/agent_api/app.py         # Browser-facing market-context proxy
frontend/src/App.tsx         # Buyer profile, evidence, decisions, saved research
frontend/src/App.test.tsx    # Buyer behavior regressions
tests/data_service/test_app.py # Aggregate and health contract tests
```

## Complexity Tracking

No new service or provider. Cross-device identity and outbound notifications remain intentionally unimplemented.
