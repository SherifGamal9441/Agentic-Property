# Validation Quickstart: Property Decision Workbench

## Prerequisites

- Required live-provider environment values configured.
- Docker available for full-stack validation.

## Focused checks

1. Run frontend component tests for no-results, partial-property, map selection, and one-to-four comparison states.
2. Run agent API stream tests for stable thread identity, safe failure events, and normalized property payloads.
3. Run data-service tests for bounded retrieval, active/historical status, and missing values.
4. Run maintained graph routing tests; replace obsolete cached-tool expectation with current active/historical path.

## Recorded baseline (2026-07-14)

- `uv run pytest -q`: 65 passed (three third-party deprecation warnings).
- `npm run test:gate` and `npm run build` from `frontend/`: passed.
- `docker compose config --quiet`: passed. The full stack was already confirmed by the project operator; this iteration does not restart it.

## Full-stack acceptance

1. Start project with `docker compose up --build`.
2. Open frontend and submit a supported buyer brief. Confirm progress begins, active dataset snapshot status appears, and no demo-mode switch is visible.
3. Submit a follow-up brief. Confirm same conversation context is retained. Start a new conversation and confirm context resets.
4. Test result sets of zero, one, two, three, and four. Confirm cards, map, and comparison remain correct.
5. Select each mappable result from card and location view. Confirm bidirectional focus, evidence-backed area labels, and source/freshness evidence.
6. Test partial values and forced agent failure. Confirm no `0` substitution, broken pin, or raw exception appears.
7. Restart agent container and confirm conversation persistence for configured single-agent deployment.
8. Mark must-have/nice-to-have criteria; generate a decision sheet and verify every ownership-cost assumption and historical comparable label.
9. Save a search locally, load a newer active dataset snapshot, and verify only then that an in-app change indicator appears.

## Release gate

- All focused tests pass.
- Docker stack health checks pass.
- Acceptance scenarios in [spec.md](spec.md) complete.
- Location view displays only coordinate and area evidence supplied by results; no external map provider is required.
