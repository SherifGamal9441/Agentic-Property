# Research: Property Decision Workbench

## Decision 1: Remove demo mode; keep explicit active-data result states

**Decision**: Remove synthetic demo properties, synthetic agent confidence, and demo/live mode switching from buyer-facing UI. Render only run states returned by the service: `loading`, `active_dataset_listing`, `historical_insight`, `web_research`, `no_results`, and `failed`.

**Rationale**: The product promise is an inspectable property decision. Active CSV data becomes a dated database snapshot, not a false claim of live/on-demand scraping.

**Alternatives considered**:

- Keep demo mode behind a toggle: rejected because normal product flow remains ambiguous.
- Keep a hidden URL demo route: deferred. Developer demos can use API fixtures and test harnesses instead.

## Decision 2: Render location evidence with a keyless basemap

**Decision**: Use MapLibre GL JS with OpenFreeMap's public keyless style. Fit returned coordinates to the visible map, group identical coordinates, synchronize marker/card/detail selection, retain native keyboard markers, and show an accessible area-only fallback when coordinates or the basemap are unavailable.

**Rationale**: Supplied listing coordinates are already available, so a real street map improves buyer location judgement without changing the agent or data service. OpenFreeMap requires no account or API key, while MapLibre preserves direct control over marker behavior and attribution.

**Alternatives considered**:

- Paid map API: rejected; a keyless public provider meets current scope.
- Hard-code `tile.openstreetmap.org`: rejected; its best-effort usage policy is unsuitable as the product's direct tile dependency.

## Decision 3: Share one property presentation contract

**Decision**: Agent API owns a normalized property-result payload for frontend use. It carries nullable display fields, explicit data status, source/freshness evidence, ranking explanation, and coordinate validity. Frontend never converts absent values to zero.

**Rationale**: Current database output may omit values while UI types and map calculations assume numbers. A single contract prevents broken cards, `AED 0`, and invalid map markers.

**Alternatives considered**:

- Patch each UI component: rejected; duplicated null behavior drifts quickly.
- Send database rows directly: rejected; leaks storage naming and leaves status/freshness ambiguous.

## Decision 4: Deterministic rank before generative explanation

**Decision**: Filter listings by parsed criteria, calculate transparent score components from available fields, sort deterministically, then ask the model to explain evidence and trade-offs. Historical rows retain `insights_only` status.

**Rationale**: Price assessment and fit must be traceable to actual input data; generative text remains useful for explanation, not factual scoring.

**Alternatives considered**:

- Keep LLM-only ranking: rejected; cannot audit why a property ranked first.
- Build market-price prediction model: deferred; insufficient validated comparables and no request for ML work.

## Decision 5: Persist current SQLite checkpoint volume before adding a service

**Decision**: Mount the existing SQLite checkpoint directory as a named Docker volume for single-agent deployment. Keep checkpointer interface unchanged. Plan a Postgres-backed checkpoint migration only before running multiple agent replicas.

**Rationale**: Existing system already works with SQLite; volume fixes restart loss without new infrastructure. SQLite remains unsuitable for horizontal agent scaling.

**Alternatives considered**:

- Add a second memory service now: rejected; existing Postgres/SQLite setup handles current need.
- Move immediately to Postgres checkpointing: deferred until multi-replica requirement appears.

## Decision 6: Dynamic comparison range is one through four

**Decision**: Keep a selection list capped at four properties. Render selected columns only, with empty slots as optional add targets; one selected property uses same comparison surface rather than special mode.

**Rationale**: Four is readable while covering full agent result set. One-to-four behavior removes hard-coded assumptions around exactly three homes.

**Alternatives considered**:

- Exactly four mandatory columns: rejected; wastes space for smaller result sets.
- Unlimited selection: rejected; comparison readability collapses and data density grows.

## Decision 7: Add buyer decision tools before account features

**Decision**: Add must-have/nice-to-have criteria, printable decision sheet, historical comparable summary, transparent ownership-cost calculator, active-snapshot monitor, browser-local saved searches, and in-app snapshot-change indicators. Exclude Arabic localization, accounts, external notifications, and paid integrations.

**Rationale**: These features directly improve buyer decision quality using existing data and browser storage. They avoid fake “real-time” claims and avoid adding identity, billing, or notification infrastructure prematurely.

**Alternatives considered**:

- Email/push alerts: rejected; no accounts, contacts, or automatic feed refresh exist.
- Arabic localization: explicitly deferred by user.
- Custom valuation/ML model: rejected; transparent historical comparables are safer and cheaper at this stage.
