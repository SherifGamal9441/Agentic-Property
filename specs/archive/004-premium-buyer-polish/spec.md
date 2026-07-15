# Feature Specification: Premium Buyer Polish

**Feature Branch**: `[004-premium-buyer-polish]`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: Add premium buyer actions, evidence-led location map, saved research quality-of-life, and luxury workspace refinement without paid map services or unsupported location claims.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a deliberate shortlist (Priority: P1)

A buyer can open any property card and immediately save it to a shortlist or add it to the comparison tray, then understand exactly what is saved and what is being compared.

**Why this priority**: A property drawer without decision actions breaks the journey at the moment a buyer has enough evidence to act.

**Independent Test**: Open a result through its card and map pin; add and remove it from the shortlist and comparison tray; verify each state updates everywhere and comparison accepts one through four homes.

**Acceptance Scenarios**:

1. **Given** a buyer opens a property, **When** they inspect its details, **Then** clear actions let them add or remove it from their shortlist and comparison tray without returning to the result grid.
2. **Given** a buyer has selected homes, **When** they review cards, pins, the drawer, or the decision tray, **Then** each selected state is visible and consistent.
3. **Given** a buyer attempts to add a fifth home to comparison, **When** they choose the comparison action, **Then** the system preserves the existing four homes and explains the limit.

---

### User Story 2 - Use location as decision evidence (Priority: P1)

A buyer uses the location view to understand where results sit, distinguish precise from area-level placement, filter to their saved or compared homes, and inspect overlapping results without unsupported geographic claims.

**Why this priority**: Location is central to property choice, but the product must remain more trustworthy than a decorative map.

**Independent Test**: Load results with multiple areas, overlapping coordinates, missing coordinates, shortlisted homes, and comparison homes; verify every displayed location outcome can be traced to supplied evidence.

**Acceptance Scenarios**:

1. **Given** a buyer selects a card, pin, shortlist entry, or comparison entry, **When** the selection changes, **Then** the corresponding map state and property evidence remain synchronized.
2. **Given** several homes share an exact or effectively overlapping position, **When** a buyer selects that point, **Then** they can choose each home represented by the cluster.
3. **Given** a buyer switches map scope between all results, shortlist, and comparison homes, **When** the selected scope has locations, **Then** only that evidence is emphasized without discarding the broader search context.
4. **Given** a listing has missing or area-only location evidence, **When** it appears in the experience, **Then** the buyer sees its confidence level and a useful explanation rather than a misleading pin.

---

### User Story 3 - Return to an organized decision (Priority: P2)

A buyer can resume a saved search with its criteria and shortlist intact, recognize what changed in a newer active dataset snapshot, and quickly clear or refine the decision when their brief changes.

**Why this priority**: Buying a home spans multiple sessions; research should feel composed rather than disposable.

**Independent Test**: Save a brief with criteria and selected homes, reopen it, then evaluate a changed dataset snapshot; verify criteria, shortlist, added results, removed results, and reset controls are accurate.

**Acceptance Scenarios**:

1. **Given** a buyer saves a research brief, **When** they return on the same device, **Then** the brief, structured criteria, and shortlist can be restored before a new search.
2. **Given** a saved search is run against a newer active dataset snapshot, **When** results differ, **Then** the buyer can distinguish added, removed, and unchanged matches.
3. **Given** the buyer changes direction, **When** they reset the brief or shortlist, **Then** the affected state is cleared deliberately and the system confirms what changed.

---

### User Story 4 - Experience a composed premium workspace (Priority: P2)

A buyer sees a calm, editorial workspace that carries the luxury of the landing view into empty, loading, result, map, shortlist, and drawer states without oversized blank regions or data jargon.

**Why this priority**: The central research surface currently feels plainer than the surrounding page, weakening perceived quality despite the strong palette and typography.

**Independent Test**: Review empty, loading, one-result, multi-result, shortlist, comparison, and property-drawer states at desktop and mobile widths; verify hierarchy, rhythm, contrast, and primary actions remain clear.

**Acceptance Scenarios**:

1. **Given** no search has run, **When** a buyer reaches the workspace, **Then** it presents an intentional invitation and guided next step instead of a large unused white canvas.
2. **Given** research is loading or partial, **When** the workspace changes state, **Then** the composition retains visual warmth, meaningful hierarchy, and a clear recovery path.
3. **Given** a buyer reads product data status, **When** it is shown in the interface, **Then** it is accurate and useful without exposing CSV, database, scraping, or other ingestion implementation details.

---

### User Story 5 - Move through research without friction (Priority: P3)

A buyer can refine, sort, inspect, and exit research controls quickly using mouse, keyboard, or touch while evidence remains readable and decisions remain reversible.

**Why this priority**: Small interaction details distinguish a polished buyer tool from a prototype.

**Independent Test**: Use keyboard-only and touch-sized controls to open and close a property, change map scope, sort or filter visible results, add a home to the shortlist, and clear a selection.

**Acceptance Scenarios**:

1. **Given** a buyer has multiple results, **When** they use buyer-relevant filtering or sorting, **Then** the active choice is visible and does not alter property facts or evidence labels.
2. **Given** a buyer opens a property drawer or decision sheet, **When** they use keyboard or touch controls, **Then** they can reach all actions and close the overlay without losing their research state.
3. **Given** a result has incomplete fields, **When** the buyer filters, sorts, or compares it, **Then** unknown values remain visibly unknown and do not become invented values.

### Edge Cases

- A search may return zero or one result; shortlist, comparison, map, and decision states must remain useful without padded or broken panels.
- A property may be removed from a new snapshot while it remains in a saved shortlist; it must be identified as no longer active rather than silently deleted or presented as current.
- Several properties may share coordinates, while other properties in the same result set have no coordinates.
- A buyer may add the same home repeatedly, close a drawer mid-action, or attempt to compare more than four homes; all actions must be idempotent and preserve the valid state.
- Long titles, areas, criteria, source labels, and currency values must not clip essential actions on supported desktop and mobile widths.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide separate, clearly labelled shortlist and comparison actions inside the property detail view.
- **FR-002**: System MUST show shortlist and comparison membership consistently on property cards, map pins or clusters, property detail, and the comparison tray.
- **FR-003**: System MUST support comparing one through four homes and prevent a fifth home from replacing an existing choice without explicit buyer action.
- **FR-004**: System MUST let buyers remove a property from shortlist or comparison from the same context in which it was added.
- **FR-005**: System MUST keep selection synchronized between result cards, property detail, map locations, shortlist entries, and comparison entries.
- **FR-006**: System MUST enhance the existing no-cost relative location view with selectable overlap groups, all-results/shortlist/comparison scopes, and visible coordinate confidence.
- **FR-007**: System MUST identify the difference between precise supplied coordinates, area-level location evidence, and unavailable location evidence without implying unsupported precision.
- **FR-008**: System MUST show area-level evidence summaries only when source data supports the reported values and time period.
- **FR-009**: System MUST NOT add a paid map provider or claim routing, commute time, nearby amenities, street boundaries, or real-time location information without verified supporting data.
- **FR-010**: System MUST preserve a saved brief's query, structured criteria, shortlist, and last-seen dataset snapshot for return visits on the same device.
- **FR-011**: System MUST distinguish added, removed, and unchanged matches when saved research is evaluated against a newer active dataset snapshot.
- **FR-012**: System MUST provide deliberate reset controls for brief criteria, shortlist, and comparison choices and confirm the affected state after use.
- **FR-013**: System MUST offer buyer-relevant result filtering or sorting while preserving displayed property facts, source evidence, and unknown values.
- **FR-014**: System MUST make empty, loading, partial-data, and failure workspace states feel intentional, warm, and visually aligned with the established editorial buyer experience.
- **FR-015**: System MUST retain accurate user-facing active-data language while excluding CSV, database, scraping, and other ingestion implementation details from the buyer experience.
- **FR-016**: System MUST preserve readable contrast, keyboard operation, visible focus, logical overlay dismissal, touch-sized actions, and no horizontal overflow at supported desktop and mobile widths.
- **FR-017**: System MUST preserve existing active-data honesty, historical-data qualification, buyer-first scope, one-to-four comparison support, no-paid-map constraint, and no-Arabic-localization decision.

### Key Entities

- **Shortlist entry**: A buyer-selected property retained for later consideration, with its last-known active-data status and source snapshot.
- **Comparison selection**: Up to four shortlisted or directly selected homes presented together for a buyer decision.
- **Location evidence**: The reported coordinate, area-level placement, availability state, and confidence level associated with a property.
- **Location group**: A selectable set of properties that share an overlapping relative location.
- **Saved research brief**: Buyer query, structured criteria, selected properties, last-seen snapshot, and result-change state retained for a return visit.
- **Workspace state**: Empty, researching, partial-data, result, selected, shortlist, comparison, and failure presentation states.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of property detail views expose visible shortlist and comparison actions, and the resulting state is reflected in every related surface within one interaction.
- **SC-002**: Buyers can assemble a one-to-four-home comparison from result cards or the property detail view and identify the selected homes within two minutes.
- **SC-003**: 100% of map acceptance cases distinguish exact, area-only, unavailable, and overlapping location evidence without unsupported travel, amenity, or street-level claims.
- **SC-004**: In saved-research acceptance tests, 100% of restored briefs retain their criteria and shortlist, and every snapshot change is categorized as added, removed, or unchanged.
- **SC-005**: Across empty, loading, partial-data, result, shortlist, comparison, and drawer acceptance states, reviewers find a clear next action and no oversized unused central workspace region.
- **SC-006**: At supported desktop and mobile widths, 100% of primary research, map, shortlist, comparison, reset, and overlay controls are keyboard reachable, touch usable, and free of horizontal page overflow.

## Assumptions

- Aizen remains a buyer-first, evidence-led Dubai property research product.
- Shortlists and saved briefs remain local to the current device until a separate consent, privacy, authentication, and retention feature is approved.
- Existing active dataset and historical context are the only sources for buyer-facing factual location and market evidence.
- The existing schematic map remains the visual foundation; the feature improves its decision value rather than replacing it with a generic third-party map.
- Premium feel comes from disciplined hierarchy, warm material layers, editorial typography, and purposeful empty states—not decorative data, fake confidence, or fictional listings.
- Arabic localization, real-time scraping claims, routing, commute estimates, and commercial map services remain out of scope.
