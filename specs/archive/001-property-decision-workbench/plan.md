# Implementation Plan: Property Decision Workbench

**Branch**: No branch created by request | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification for evidence-first live property research, persistent follow-ups, truthful map behavior, and one-to-four comparison.

## Summary

Replace buyer-facing demo flow with an active-dataset evidence-first workspace. Normalize result payloads, persist browser conversation, score listings deterministically before model explanation, render returned coordinates on a keyless public basemap, support flexible selection of up to four returned properties, and add buyer decision tools. Preserve active-versus-historical safety and existing service boundaries.

## Technical Context

**Language/Version**: Python 3.13 agent API; Python 3.11 data service; TypeScript frontend

**Primary Dependencies**: FastAPI, LangGraph, SQLAlchemy, PostgreSQL, React/Vite, MapLibre GL JS, OpenFreeMap

**Storage**: PostgreSQL listing data; existing SQLite checkpoint file mounted as named volume for single-agent persistence

**Testing**: pytest; Vitest and Testing Library; Docker Compose health checks

**Target Platform**: Linux Docker services; modern desktop/mobile browsers

**Project Type**: Containerized web application with agent API, data service, and single-page frontend

**Performance Goals**: Visible progress within two seconds for 95% of successful active-data runs; location and comparison interactions respond without browser reload

**Constraints**: No synthetic buyer results; active CSV snapshot cannot be presented as real-time scraping; historical data cannot be presented as active inventory; no raw internal exception in browser; keyless OpenFreeMap basemap only; comparison maximum four; no Arabic localization

**Scale/Scope**: Current single-agent Compose deployment, buyer research workflow, zero to four visible comparison selections, browser-local saved searches and in-app snapshot-change indicators; no accounts, external alerts, CRM, automatic scraping, or Arabic localization

## Constitution Check

No project constitution exists. Feature gates derived from current product safety and user request:

- Pass: reuse existing services; no new microservice or broad abstraction.
- Pass: active and historical source intent remains explicit through every UI path.
- Pass: MapLibre renders supplied coordinates with OpenFreeMap; no paid map API, map key, or backend location service is added.
- Pass: ranking evidence is data-backed; generative output explains rather than invents score inputs.
- Pass: persistence first uses existing SQLite checkpointer plus Docker volume; Postgres migration deferred until replica scaling.

Re-check after implementation design: no gate requires unjustified complexity.

## Project Structure

### Documentation (this feature)

```text
specs/001-property-decision-workbench/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
```text
src/
├── agent_api/          # SSE contract and normalized property payload
├── agents/             # LangGraph topology and state
├── nodes/              # retrieval, ranking, explanation, reflection
├── data_service/       # listing search, schema, bootstrap
└── memory/             # existing checkpoint persistence

frontend/src/
├── App.tsx             # workspace state and orchestration
├── styles.css          # responsive workspace/layout behavior
└── test/               # frontend test setup

tests/
├── agent_api/
├── agents/
├── data_service/
└── nodes/

compose.yaml            # service environment and persistent memory volume
```

**Structure Decision**: Preserve current project layout. Keep map and comparison as focused frontend modules only if `App.tsx` becomes materially clearer; do not create a component framework merely for this feature.

## Implementation Sequence

### 1. Establish truthful contracts and test baseline

1. Replace obsolete end-to-end test assumptions with active/historical routing behavior.
2. Define normalized `PropertyResult`, run status, freshness/source, nullable values, and `data_status` at agent API boundary.
3. Add contract tests for active-snapshot, historical, no-results, partial-data, and safe-failure streams.

**Verify**: Existing graph tests plus new contract tests pass without invoking a real external model.

### 2. Preserve conversation and harden live runs

1. Generate/store one browser thread ID; reuse it until explicit new conversation.
2. Persist existing checkpoint database through Compose volume.
3. Replace browser-visible raw exceptions with safe code/message/retryable events; clear stale results on each run.

**Verify**: Follow-up request retains context; restart confirms single-agent persistence; failure simulation leaves UI usable.

### 3. Make recommendation evidence auditable

1. Preserve parsed/applied criteria, must-have/nice-to-have levels, source dates, and active snapshot identity from data service to UI payload.
2. Add deterministic score factors from filters and available property attributes; retain LLM explanation as commentary.
3. Keep historical result behavior as insights-only in card, detail, comparison, decision sheet, and answer paths.
4. Bound data search and add indexes/precise money representation only where required by current query pattern.
5. Derive historical comparable summaries and transparent ownership-cost inputs from available evidence; never hard-code undisclosed fees or rates.

**Verify**: Same input/data produces stable ordering; each displayed recommendation has evidence; historical result cannot show active-listing call to action; decision sheet discloses every assumption.

### 4. Replace demo workspace with live buyer experience

1. Remove demo mode switch, demo cards, demo confidence, and fake progress from primary UI.
2. Render explicit loading, no-result, historical-insight, web-research, partial-data, and safe-failure states.
3. Add source/freshness/snapshot/applied-criteria and score-factor panels to property detail.
4. Add must-have/nice-to-have brief controls and printable decision sheet.

**Verify**: Browser has no synthetic result path; each stream state has targeted frontend test.

### 5. Build real location and flexible comparison

1. Enhance current location view: remove unevidenced hard-coded landmarks, show current-result area labels, and keep clear relative-location wording.
2. Validate coordinates, calculate bounds for one or more pins, cluster/offset overlapping pins, and synchronize pin/card/detail selection.
3. Replace hard-coded three-property comparison with dynamic zero-to-four selection and responsive one-to-four comparison surface.
4. Include data status, source/freshness/snapshot, unavailable values, and score factors in comparison.
5. Add browser-local saved searches and in-app change indicators based only on a newer active dataset snapshot.

**Verify**: Location/card selection works in both directions; invalid/missing coordinate does not create pin; result sets zero through four pass frontend tests; saved-search change indicator never appears without newer snapshot.

### 6. Release validation

1. Run focused tests, then full maintained suite.
2. Build and launch Compose stack.
3. Perform quickstart acceptance flows using live-configured environment.
4. Confirm active data is labeled as a snapshot and all saved-search change signals reference a newer snapshot.

**Verify**: All quality gates in [quickstart.md](quickstart.md) pass.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Current services and coordinate location view cover this scope. | N/A |
