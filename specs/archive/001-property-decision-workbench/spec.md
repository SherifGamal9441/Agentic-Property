# Feature Specification: Property Decision Workbench

**Feature Branch**: `[001-property-decision-workbench]`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Plan all audit changes; remove demo mode from UI/UX; improve location map; support comparison of one to four returned listings."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate active property matches (Priority: P1)

A buyer submits a property brief and receives active-dataset, source-backed results or an honest no-results outcome. They can see why each result fits, when its data snapshot was observed, and whether it is a current listing record or historical market signal.

**Why this priority**: Trust is prerequisite for every decision and prevents demo data or historical data being mistaken for a live recommendation.

**Independent Test**: Run a supported brief against seeded/live data and verify each returned result shows source, observed date, data status, applied criteria, and result-specific fit reasons.

**Acceptance Scenarios**:

1. **Given** an active-dataset property brief with matches, **When** the buyer runs it, **Then** the workspace shows returned listings, source links, snapshot dates, applied criteria, and clearly stated ranking reasons.
2. **Given** a brief whose only evidence is historical, **When** the buyer runs it, **Then** the workspace labels it as market insight and does not present a historical transaction as available inventory.
3. **Given** no current result is available, **When** the buyer runs it, **Then** the workspace explains the result state and offers a safe next query instead of fabricated homes.

---

### User Story 2 - Continue a property conversation (Priority: P1)

A buyer can ask a follow-up such as “what about three bedrooms?” and receive an answer that retains their earlier brief during the same browser session.

**Why this priority**: Follow-up refinement is core agent behavior; the current browser experience loses its thread between requests.

**Independent Test**: Submit a brief, submit a follow-up without restating requirements, and verify the second request carries the same conversation identity and receives prior context.

**Acceptance Scenarios**:

1. **Given** a buyer has completed a brief, **When** they submit a follow-up in the same browser, **Then** the earlier brief remains available to the agent.
2. **Given** a buyer starts a new conversation, **When** they reset the workspace, **Then** it receives a new identity and does not include the prior conversation.

---

### User Story 3 - Inspect location evidence (Priority: P2)

A buyer can explore returned homes on an interactive OpenFreeMap basemap, select a pin or card, focus the matching result, and understand when coordinates or the basemap are unavailable. Exact source coordinates remain explicitly labelled as listing evidence.

**Why this priority**: Location is a primary property criterion; a decorative map cannot support a buying decision.

**Independent Test**: Load 1, 2, and 4 geo-coded results; select pins and cards in either order; verify selection synchronization, fit summary, and accessible location text. Repeat with missing coordinates.

**Acceptance Scenarios**:

1. **Given** returned properties with coordinates, **When** the buyer views the location panel, **Then** each eligible property appears in an interactive location view and selecting its pin opens or focuses the same property detail.
2. **Given** one or more properties have no usable coordinate, **When** the map loads, **Then** the workspace remains usable and states that the property is shown by area only.
3. **Given** multiple nearby properties, **When** the buyer opens the map, **Then** markers remain distinguishable and map bounds include all mappable results.

---

### User Story 4 - Compare available matches (Priority: P2)

A buyer can compare any subset of the returned results from one through four homes; the interface adapts to result count and does not require exactly three selections.

**Why this priority**: Search result sets vary. A fixed three-home tray hides value for small sets and blocks useful four-home comparisons.

**Independent Test**: Test result sets of zero, one, two, three, four, and more than four listings; select and remove homes; verify comparison details and selection cap.

**Acceptance Scenarios**:

1. **Given** two returned listings, **When** the buyer selects both for comparison, **Then** the comparison shows two populated columns and two empty optional slots.
2. **Given** four returned listings, **When** the buyer selects all four, **Then** all four are compared without an error.
3. **Given** more than four returned listings, **When** the buyer tries to add a fifth, **Then** the workspace retains the first four selections and explains the limit.
4. **Given** one returned listing, **When** the buyer opens comparison, **Then** its details remain useful and empty comparison slots are not presented as errors.

---

### User Story 5 - Make a decision from evidence (Priority: P2)

A buyer marks requirements as must-have or nice-to-have, then reviews a decision sheet containing comparables, total ownership-cost assumptions, source/freshness evidence, and trade-offs for their shortlisted homes.

**Why this priority**: Buyers need a defensible decision, not only a ranked card list.

**Independent Test**: Create a brief with must-haves and preferences, select one through four properties, and generate a printable decision sheet. Verify unavailable data and assumptions are disclosed.

**Acceptance Scenarios**:

1. **Given** a buyer marks a criterion as must-have, **When** a property misses it, **Then** the property clearly shows that gap and cannot be described as a complete match.
2. **Given** a buyer selects properties, **When** they open the decision sheet, **Then** it shows side-by-side attributes, historical comparable summaries, total-cost assumptions, evidence links, and known gaps.
3. **Given** required financial inputs are absent, **When** total ownership cost is shown, **Then** the missing value and assumption are explicit rather than estimated silently.

---

### User Story 6 - Return to saved research (Priority: P3)

A buyer can save a search locally and see an in-app alert when the active dataset snapshot has changed or its current matches differ from the last time they viewed that saved search.

**Why this priority**: This adds useful repeat research without introducing accounts, email delivery, or on-demand scraping.

**Independent Test**: Save a search, simulate a new active dataset snapshot, revisit it, and verify the alert accurately describes changed matching results.

**Acceptance Scenarios**:

1. **Given** a buyer saves a search, **When** they return in the same browser, **Then** they can reopen its criteria and prior result context.
2. **Given** the active dataset snapshot changes, **When** a saved search is revisited, **Then** the buyer sees an in-app change indicator with its snapshot date.
3. **Given** no snapshot change occurred, **When** a buyer revisits a saved search, **Then** no false alert appears.

---

### User Story 7 - Use resilient active-data workspace (Priority: P3)

A buyer sees accurate progress, understandable failures, and complete cards even when an agent run is slow, unavailable, or returns partial listing data.

**Why this priority**: A polished research tool must fail honestly rather than show zero-valued or broken results.

**Independent Test**: Simulate delayed, failed, and partial result runs; verify no raw internal errors appear and all controls recover without browser reload.

**Acceptance Scenarios**:

1. **Given** an active-data run fails, **When** the workspace receives the failure, **Then** it shows an actionable user-facing message without exposing internal exception text.
2. **Given** a listing omits price, size, beds, or coordinates, **When** the result renders, **Then** unavailable values are clearly marked and the card/map continue working.

### Edge Cases

- Zero results, historical-only results, and web-research answers do not render stale cards from a previous search.
- Coordinates at the same point, invalid coordinates, and a single mappable result produce stable map bounds.
- A listing may omit any non-identity field; unavailable data is not represented as zero or a made-up value.
- A request may end before property events arrive, may stream only answer text, or may fail after partial progress.
- Refreshing the page retains a conversation only when the buyer has not explicitly started a new one.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present an active-data workspace as the primary buyer experience and remove synthetic property results and synthetic confidence from normal UI flows.
- **FR-002**: System MUST keep a stable conversation identity for follow-up requests within one browser session and provide an explicit new-conversation control.
- **FR-003**: System MUST distinguish active dataset listings, historical market signals, web research, no-result states, and unavailable runs in both text and visual treatment.
- **FR-004**: System MUST show source link when supplied, observed/listing date when supplied, active dataset snapshot date, data freshness state, applied search criteria, and result-specific fit reasons for each property recommendation.
- **FR-005**: System MUST calculate and present ranking inputs from available property data; generative text may explain a ranking but must not be its only factual basis.
- **FR-006**: System MUST render valid property coordinates through MapLibre and OpenFreeMap; selecting a marker and selecting a result card MUST keep one shared selection state without introducing a paid map API, key, or backend location request.
- **FR-007**: System MUST identify properties lacking usable coordinates and retain them in the results and comparison flows without placing invalid markers.
- **FR-008**: System MUST allow comparison selection of one through four returned properties and prevent selection beyond four with a clear explanation.
- **FR-009**: System MUST show comparison fields consistently for the selected properties, including unavailable values and each property’s data status.
- **FR-010**: System MUST replace raw live-run exceptions with safe, actionable user messages and permit another request without a browser refresh.
- **FR-011**: System MUST return UI-ready property data with explicit nullable fields rather than relying on browser-side coercion of missing values.
- **FR-012**: System MUST support bounded result retrieval and sorting suitable for growing listing data, while preserving existing active-versus-historical behavior.
- **FR-013**: System MUST retain agent conversation state across agent-service restarts according to deployment’s configured persistent storage.
- **FR-014**: System MUST validate current routing and end-to-end behavior with maintained automated tests that reflect active/historical data paths.
- **FR-015**: System MUST let buyers classify brief criteria as must-have or nice-to-have and make rank trade-offs visible.
- **FR-016**: System MUST provide a printable buyer decision sheet for selected properties, including source/freshness evidence, comparison fields, comparable-market summaries, total-cost assumptions, and known gaps.
- **FR-017**: System MUST derive comparable summaries from available historical data and label them as historical market evidence, not current inventory.
- **FR-018**: System MUST calculate a transparent total ownership-cost estimate only from explicit inputs and documented assumptions; it MUST not silently invent fees, rates, or recurring costs.
- **FR-019**: System MUST expose the active dataset snapshot identity/date and indicate when it is stale or unavailable; it MUST not claim on-demand scraping or real-time market coverage.
- **FR-020**: System MUST let a buyer save searches locally in the same browser without requiring accounts or collecting contact information.
- **FR-021**: System MUST provide in-app saved-search change indicators only after comparing a saved search against a newer active dataset snapshot; email, push, and SMS delivery are out of scope.

### Key Entities

- **Property result**: A returned property or market signal, with identity, attributes, source/freshness evidence, location status, and ranking explanation.
- **Search brief**: Buyer’s criteria and normalized filters used to retrieve and rank properties.
- **Conversation**: A buyer’s ordered requests and answers within a persistent browser session.
- **Comparison set**: Up to four selected property results and their normalized side-by-side fields.
- **Location record**: A property’s coordinate validity, area label, map eligibility, and map selection state.
- **Saved search**: Browser-local buyer criteria, saved time, last-seen snapshot, and result identifiers for in-app change detection.
- **Decision sheet**: Printable buyer summary of selected properties, transparent calculations, market evidence, source/freshness, and gaps.
- **Dataset snapshot**: Identity and observation time of active data loaded into the database; not a claim of real-time scraping.
- **Run status**: A buyer-visible state for request progress, completion, partial completion, or failure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In user acceptance testing, 90% of participants can identify whether a displayed result is an active dataset record, historical signal, or unavailable without help.
- **SC-002**: 100% of displayed property recommendations with available evidence show their source, observed date, and applied criteria.
- **SC-003**: 100% of browser follow-up requests within a session reuse the same conversation identity until the buyer starts a new conversation.
- **SC-004**: Buyers can select, inspect, and compare any returned set of one to four listings without a broken layout or blocked action.
- **SC-005**: 100% of listing cards with missing optional values render an explicit unavailable state instead of a zero, invalid map marker, or runtime error.
- **SC-006**: At least 95% of successful active-data requests provide first visible progress feedback within two seconds; failed requests provide a recovery action within two seconds of failure detection.
- **SC-007**: Automated coverage verifies each active, historical, no-results, partial-data, and one-to-four comparison path before release.
- **SC-008**: Buyers can generate a decision sheet for any one-to-four comparison set with no undisclosed cost assumption or market-evidence status.
- **SC-009**: 100% of saved-search alerts correspond to a newer active dataset snapshot; no alert claims a real-time or on-demand data refresh.

## Assumptions

- Primary user is a buyer researching Dubai residential property; broker workflow, accounts, external notifications, and billing are out of scope.
- Active data means CSV data loaded into the database. It is a dated dataset snapshot, not on-demand scraping or real-time inventory. Existing active and historical datasets remain sources; new paid data providers and automatic ingestion are deferred.
- Existing location view remains map v1. It uses supplied property coordinates, shows only evidence-backed area labels, and clearly identifies approximate or missing location evidence; it does not claim street-level navigation or exact location where source data cannot support it.
- Existing service boundaries remain: agent API, data service, database, and browser frontend. Persistent storage should reuse deployed database infrastructure where practical.
- Comparison is limited to four homes to preserve readable desktop and mobile layouts.
- Saved searches and change indicators are local to a browser. They become useful when a newer active dataset snapshot is loaded; they do not send email, push, or SMS.
- Arabic localization is deliberately excluded from this feature.
