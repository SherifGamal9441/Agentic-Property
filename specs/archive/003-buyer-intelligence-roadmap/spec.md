# Feature Specification: Buyer Intelligence Roadmap

**Feature Branch**: `[003-buyer-intelligence-roadmap]`  
**Created**: 2026-07-14  
**Status**: Draft — begins only after `002-restore-buyer-experience` meets acceptance criteria  
**Input**: Add the agreed next-level buyer capabilities: guided briefs, stronger comparisons, transparent decision support, historical market context, map evidence, research continuity, data operations, feedback, and quality measurement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a decision-ready buyer brief (Priority: P1)

A buyer can provide a natural-language brief and refine it with optional budget, timing, area, property, financing, must-have, nice-to-have, and deal-breaker inputs. They can verify how the system understood those inputs before trusting the results.

**Why this priority**: Better inputs produce better ranking and make trade-offs explainable without making the buyer repeat information.

**Independent Test**: Create a brief with both required and preferred criteria, change one criterion, and verify returned results and explanations reflect the updated brief.

**Acceptance Scenarios**:

1. **Given** a buyer begins with free text, **When** they add optional structured preferences, **Then** the workspace displays one coherent brief rather than conflicting filters.
2. **Given** a buyer marks a requirement as a deal-breaker, **When** a result misses it, **Then** the result is clearly identified as unsuitable or excluded according to the buyer's chosen behavior.
3. **Given** the system interprets a brief, **When** the buyer reviews it, **Then** they can see and correct the criteria before making a decision.

---

### User Story 2 - Compare and challenge choices (Priority: P1)

A buyer compares one through four homes in a decision matrix, sees the best reported value for relevant attributes, and can understand both why a home fits and why it may not be suitable.

**Why this priority**: A trustworthy buying tool should surface objections and evidence gaps, not only favorable rank scores.

**Independent Test**: Compare homes with different prices, sizes, source ages, criteria gaps, and missing values; verify every comparison row remains interpretable.

**Acceptance Scenarios**:

1. **Given** a shortlist of one through four homes, **When** the buyer opens comparison, **Then** the matrix shows normalized property facts, source/freshness, criteria matches, and criteria gaps side by side.
2. **Given** a field is unavailable for one home, **When** the matrix highlights a reported best value, **Then** the unavailable field is not treated as a losing value.
3. **Given** a home has a material trade-off, **When** the buyer reviews it, **Then** its “why not” reasons are factual, specific, and visible alongside its strengths.

---

### User Story 3 - Evaluate cost and market context transparently (Priority: P1)

A buyer can evaluate selected homes using only their own entered cost assumptions and can compare them with clearly labelled historical area context.

**Why this priority**: Buyers need a decision frame that separates current inventory from past market evidence and avoids hidden financial assumptions.

**Independent Test**: Enter different buyer cost scenarios and inspect historical context for a selected area; verify every number identifies its source, period, or buyer input.

**Acceptance Scenarios**:

1. **Given** a buyer enters cash or financing assumptions, **When** the decision sheet updates, **Then** it recalculates using only entered values and labels omitted inputs as unknown.
2. **Given** historical area data exists, **When** a buyer reviews a selected home, **Then** they can see an area-level transaction range, price-per-area range, activity volume, and time period labelled as historical context.
3. **Given** historical data is unavailable or too thin, **When** the buyer opens market context, **Then** the workspace states that limitation and does not imply a trend.

---

### User Story 4 - Explore evidence-backed location (Priority: P2)

A buyer uses the existing no-cost map experience to understand relative positions, property clusters, pin overlap, area grouping, and coordinate confidence without being shown unsupported travel-time or amenity claims.

**Why this priority**: Map value comes from honest spatial evidence, not decorative or unverified features.

**Independent Test**: Load sparse, overlapping, and multi-area coordinate sets; select a property from the map and from results; verify grouped and missing-coordinate states are clear.

**Acceptance Scenarios**:

1. **Given** several properties occupy the same or nearby locations, **When** the buyer views the map, **Then** the experience shows an understandable cluster or overlap indicator and allows selection of each property.
2. **Given** properties span multiple areas, **When** the buyer views the map, **Then** they can recognize area grouping without the map claiming a street-level boundary or commute time.
3. **Given** a coordinate is missing or approximate, **When** the buyer inspects the property, **Then** its location confidence is visible and it remains usable elsewhere.

---

### User Story 5 - Return to research and understand changes (Priority: P2)

A buyer can return to saved research, see what changed between dataset snapshots, and keep a durable shortlist when an authenticated research identity is available.

**Why this priority**: Property decisions take time; a one-session search experience loses valuable research context.

**Independent Test**: Save a brief and shortlist, load a newer snapshot with changed matches, and verify the buyer sees the changed items, unchanged items, and snapshot date without a false real-time claim.

**Acceptance Scenarios**:

1. **Given** a buyer saves research in a browser, **When** they return to it, **Then** the criteria, shortlist, and last-seen snapshot remain available.
2. **Given** a newer active dataset snapshot exists, **When** a saved search is reevaluated, **Then** the buyer can distinguish newly matching, no-longer-matching, and unchanged results.
3. **Given** the product offers authenticated research identity, **When** an authenticated buyer returns on another device, **Then** their consented shortlists and saved searches are available without exposing them to another buyer.

---

### User Story 6 - Improve research quality through operations and feedback (Priority: P3)

An operator can assess data freshness and ingestion quality, while buyers can give concise feedback on whether results were useful or had an incorrect area, weak comparison, or missing information.

**Why this priority**: Reliable product iteration needs both data-quality visibility and real buyer feedback.

**Independent Test**: Process a dataset refresh containing valid, duplicate, and rejected records; submit buyer feedback; verify operators can identify snapshot status, data issues, and aggregate feedback signals.

**Acceptance Scenarios**:

1. **Given** an operator reviews data operations, **When** a refresh completes or fails, **Then** they can see last successful refresh, record counts, rejected rows, duplicate handling, and active snapshot identity.
2. **Given** a buyer marks a result as useful or identifies an issue, **When** feedback is submitted, **Then** it is recorded without changing the factual property record.
3. **Given** product quality is reviewed, **When** operators inspect performance, **Then** they can assess request completion, empty-result rate, fallback-to-historical rate, safe failure rate, and evidence coverage.

### Edge Cases

- Buyers may leave optional criteria, cost inputs, or feedback blank; blanks must remain unknown rather than becoming assumed values.
- A saved search may produce zero matches after a newer snapshot; that is a change state, not an error.
- Historical context may be present for an area but not comparable to a specific property type or time period; it must be qualified or withheld.
- Multiple properties may have the same reported best value, incomplete values, or overlapping coordinates.
- Persistent research identity and notifications require explicit buyer consent and must not expose saved research across users.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let buyers combine free-text briefs with optional structured criteria, including must-haves, nice-to-haves, deal-breakers, budget, timing, area, property needs, and financing preference.
- **FR-002**: System MUST show buyers the interpreted decision criteria and allow correction before results are treated as decision evidence.
- **FR-003**: System MUST use buyer criteria consistently in retrieval, ranking, comparison, and explanation, while keeping factual calculation separate from generated narrative.
- **FR-004**: System MUST provide a one-to-four-home decision matrix with property facts, normalized unit values where data permits, data source, snapshot evidence, criterion matches, and known gaps.
- **FR-005**: System MUST expose factual “why not” reasons for each relevant result, including criterion conflicts, missing evidence, historical-only status, and material data limitations.
- **FR-006**: System MUST calculate decision-sheet scenarios only from values explicitly supplied by the buyer or an identified data source, and MUST label all assumptions and unknown inputs.
- **FR-007**: System MUST provide historical area context only when available evidence supports it, including labelled time period, sample size/activity count, transaction range, and unit-price range.
- **FR-008**: System MUST enhance the existing relative map with area grouping, overlap handling, selection synchronization, and coordinate-confidence indicators without a paid map provider or unsupported travel/amenity claims.
- **FR-009**: System MUST retain browser-local saved research and accurately identify differences between a saved result set and a newer active dataset snapshot.
- **FR-010**: System MUST support durable, consented buyer research identity before offering cross-device saved research or outbound change notifications.
- **FR-011**: System MUST provide operators with data-refresh status, snapshot identity, valid/rejected/duplicate record counts, and a clear last-successful-refresh state.
- **FR-012**: System MUST allow buyers to submit bounded usefulness and data-quality feedback without changing source property facts.
- **FR-013**: System MUST maintain a repeatable quality set of representative buyer briefs and report completion, empty-result, historical-fallback, safe-failure, response-time, and evidence-coverage measures.
- **FR-014**: System MUST preserve all active-data honesty, no-paid-map, buyer-first, and no-Arabic-localization constraints from prior specifications.
- **FR-015**: System MUST complete visual restoration acceptance before implementing any requirement in this specification.

### Key Entities

- **Decision profile**: Buyer-controlled brief containing interpreted requirements, weights, deal-breakers, and editable assumptions.
- **Comparison insight**: A factual match, gap, unit value, provenance item, or data-quality limitation attached to a selected property.
- **Market context summary**: Historical area-level evidence with period, coverage, and qualified ranges; never current inventory.
- **Location confidence**: Whether a property's supplied coordinate supports exact relative placement, approximate area placement, or area-only display.
- **Research record**: Saved buyer brief, shortlist, last-seen snapshot, result-change set, and consented ownership identity when available.
- **Refresh audit**: Operational record of a dataset load, including outcome, snapshot identity, counts, and data-quality exceptions.
- **Buyer feedback**: Bounded research-quality signal associated with a result or run, separate from the underlying property fact.
- **Quality measure**: Aggregated outcome metric for buyer research reliability and evidence coverage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 90% of buyers can state their must-haves, trade-offs, and one reason a shortlisted home may not fit without help.
- **SC-002**: 100% of decision-sheet monetary figures identify whether they are buyer-entered, source-backed, or unknown.
- **SC-003**: 100% of historical context panels identify their period and evidence coverage, and none are labelled as current inventory.
- **SC-004**: Buyers can compare any set of one through four homes and identify source, snapshot, key match, and key gap for each within two minutes.
- **SC-005**: 100% of saved-search change notices correspond to a newer active snapshot and identify changed versus unchanged result states.
- **SC-006**: Operators can identify the current active snapshot and the latest refresh outcome, including accepted, rejected, and duplicate counts, in one review.
- **SC-007**: Before release, the representative buyer-brief quality set validates every supported decision profile, no-result, historical-context, partial-data, map-overlap, and safe-failure path.

## Assumptions

- This is a staged feature set. Decision profile, comparison insight, cost transparency, market context, and map evidence are delivered before cross-device research identity, outbound notifications, and broader operations tooling.
- Existing browser-local saves remain the default until a consented buyer identity is explicitly introduced.
- Cross-device research and outbound notifications require a separate privacy, authentication, retention, and delivery plan before implementation; they are not silently enabled.
- Historical data is market context only and must not be presented as an active listing recommendation.
- The map remains evidence-led and no-cost; street navigation, traffic, commute estimates, and commercial map services are excluded.
- Arabic localization remains excluded.
