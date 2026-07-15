# Feature Specification: Buyer Research Remaster

**Feature Branch**: `[005-buyer-research-remaster]`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: Make Aizen an elegant buyer-first property decision product: expose the existing persistent agent conversation, show factual historical evidence in the decision sheet, make costs transparent, add buyer decision actions, and unify the experience in a calm luxury editorial interface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continue visible property research (Priority: P1)

A buyer can see the conversation that informed their search, return to an earlier research session on the same browser, and continue a follow-up without restating their brief.

**Why this priority**: Agent memory has buyer value only when the buyer can see, trust, and resume it.

**Independent Test**: Complete two requests in one session, refresh the workspace, reopen the session, and submit a follow-up. Verify messages are in order and the follow-up uses the same research context.

**Acceptance Scenarios**:

1. **Given** a buyer completes a request, **When** the answer arrives, **Then** the research timeline shows the buyer request and Aizen answer in order.
2. **Given** a buyer returns in the same browser, **When** they open a retained research session, **Then** its prior conversation is displayed and can be continued.
3. **Given** a buyer starts a new conversation, **When** they submit a new brief, **Then** it does not include another session's context and the earlier session remains separately available.

---

### User Story 2 - Compare homes with real market evidence (Priority: P1)

A buyer opening a one-to-four-home decision sheet sees reported historical context for each selected home's available area, type, and bedroom facts, rather than a placeholder warning.

**Why this priority**: This is the decision surface where unsupported copy is most damaging to trust.

**Independent Test**: Select homes across one or more areas, open the decision sheet, and verify each home shows its matching historical record count, period, price range, unit-price range, or an explicit no-evidence state.

**Acceptance Scenarios**:

1. **Given** reported matching transactions exist, **When** a buyer opens the decision sheet, **Then** each selected home shows historical sample size, date coverage, price range, and price-per-square-foot range.
2. **Given** a selected home has incomplete comparable facts or no reported matching transactions, **When** the sheet opens, **Then** it says what is unavailable without estimating a value.
3. **Given** historical figures are shown, **When** a buyer reads them, **Then** every figure is labelled as historical market context and never as active inventory or a valuation.

---

### User Story 3 - Understand the real cost of each choice (Priority: P1)

A buyer can enter only confirmed costs and compare each home's purchase price, one-off costs, recurring annual charge, and disclosed unknowns.

**Why this priority**: The current combined entered-cost total cannot answer what each home would cost to acquire.

**Independent Test**: Enter one-off and annual assumptions for a two-home comparison. Verify each column shows its own purchase total, annual charge separately, and no unexplained fee or rate.

**Acceptance Scenarios**:

1. **Given** a buyer enters confirmed one-off assumptions, **When** they review selected homes, **Then** each home's purchase total combines its reported price with those entered one-off costs.
2. **Given** a buyer enters an annual service charge, **When** the sheet updates, **Then** it is displayed separately from purchase total.
3. **Given** a cost is empty, **When** the sheet renders, **Then** it remains marked as not entered rather than assumed to be zero.

---

### User Story 4 - Make a composed buyer decision (Priority: P2)

A buyer can mark homes as saved, maybe, or ruled out, add a private note, and move through a restrained, elegant evidence-led workspace on desktop or mobile.

**Why this priority**: Buyers need a calm way to narrow choices over several visits, not a collection of disconnected cards.

**Independent Test**: Mark homes with each decision state, add a note, change selection, and return in the same browser. Verify state is retained, reversible, and never changes source facts.

**Acceptance Scenarios**:

1. **Given** a buyer reviews a property, **When** they save, defer, or rule it out, **Then** the status is visible across the property card, detail, and decision controls.
2. **Given** a buyer writes a note, **When** they reopen the same browser research, **Then** the note is visible only in their saved buyer state and does not alter listing data.
3. **Given** any workspace state, **When** a buyer uses keyboard, touch, or screen magnification, **Then** primary actions remain reachable, visible, and understandable.

---

### User Story 5 - Trust an elegant, honest workspace (Priority: P2)

A buyer experiences a polished Dubai editorial interface with clear hierarchy, intentional empty/loading/error states, and evidence labels that make uncertainty useful rather than alarming.

**Why this priority**: Luxury comes from restraint, precision, and trustworthy information—not decorative claims.

**Independent Test**: Review empty, researching, results, history, detail, comparison, decision sheet, and print states at desktop and mobile widths. Verify each has a clear next action and preserves source-state meaning.

**Acceptance Scenarios**:

1. **Given** a buyer enters the workspace, **When** no research exists yet, **Then** guided next steps and the value of the service are clear without excess copy.
2. **Given** a request is loading, partial, or unavailable, **When** state changes, **Then** the buyer sees a calm explanation and recovery action without internal technical terms.
3. **Given** source, freshness, location confidence, or missing data is displayed, **When** the buyer scans the interface, **Then** its wording is consistent across cards, detail, comparison, and print.

### Edge Cases

- A checkpoint may exist but have no completed conversation; it must open as an empty research session.
- A browser may retain session metadata while the checkpoint is unavailable; the buyer sees an honest unavailable state and can start a new request.
- Selected homes may share an area, have incomplete type or bedroom facts, or have no matching historical records.
- Empty price or cost assumptions must remain unknown; entered negative values are rejected.
- Long titles, conversation answers, notes, and areas must wrap without hiding actions at supported mobile widths.
- A buyer can remove an existing decision state or note without deleting source listing evidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retain and display ordered buyer and Aizen messages for each browser-local research session that has a valid conversation identity.
- **FR-002**: System MUST let buyers reopen a locally listed prior session, continue it, and start a distinct new session without mixing their histories.
- **FR-003**: System MUST limit session discovery to identities retained by that browser; it MUST NOT provide a browsable catalogue of other sessions.
- **FR-004**: System MUST show historical market context for each selected home using only reported transactions matching the available area and, when available, property type and bedroom count.
- **FR-005**: System MUST show historical record count, covered period, price range, and price-per-square-foot range only when reported values support each field.
- **FR-006**: System MUST label historical context as market evidence, identify its matching basis, and state when it is unavailable or insufficient; it MUST NOT present it as a current listing, price estimate, or valuation.
- **FR-007**: System MUST calculate each selected home's purchase total from its reported price plus buyer-entered transfer, finance, and moving costs only.
- **FR-008**: System MUST show buyer-entered annual service charge separately from purchase total and identify all blank inputs as not entered.
- **FR-009**: System MUST let buyers save, defer, or rule out a home and attach an optional private note, retaining that buyer state only in the same browser until an identity/consent feature is separately approved.
- **FR-010**: System MUST make decision state reversible and visually consistent across property cards, property detail, comparison, and decision sheet.
- **FR-011**: System MUST use a restrained editorial design system: calm hierarchy, warm neutral material layers, dark contrast surfaces, limited accent use, real typography, and no fabricated property imagery or data.
- **FR-012**: System MUST preserve evidence-first language for active data, historical context, source snapshot, location confidence, and unreported fields throughout buyer and print views.
- **FR-013**: System MUST support keyboard operation, visible focus, logical overlay focus/dismissal, touch-usable controls, reduced-motion preference, readable contrast, and reflow without horizontal page scrolling at 320 CSS pixels.
- **FR-014**: System MUST keep existing active-versus-historical safety, one-to-four comparison limit, no-paid-map constraint, no-real-time-scraping claim, no accounts, and no Arabic localization.

### Key Entities

- **Research session**: Browser-retained title, conversation identity, last activity, and ordered buyer/Aizen transcript.
- **Historical context**: Reported transaction summary associated with one selected home's available area, type, and bedroom facts.
- **Cost assumption**: Buyer-entered transfer, finance, moving, or annual service amount, with explicit category and entered/not-entered state.
- **Buyer decision state**: Reversible saved, maybe, or ruled-out classification plus optional private note for a property.
- **Decision sheet**: Printable one-to-four-home evidence view combining property facts, historical context, buyer assumptions, and known gaps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of buyers can reopen a same-browser session, identify its prior brief, and continue it without restating the brief.
- **SC-002**: 100% of decision-sheet historical panels show either factual reported context with matching basis or an explicit unavailable state; no panel uses placeholder-only evidence.
- **SC-003**: 100% of monetary outputs identify whether they are reported property data, buyer-entered one-off cost, buyer-entered annual cost, or not entered.
- **SC-004**: In buyer acceptance testing, participants can identify their saved, maybe, and ruled-out homes and reverse a status within one minute.
- **SC-005**: At desktop and mobile acceptance widths, all primary research, session, comparison, decision, and overlay actions are keyboard reachable, touch usable, and free of horizontal page overflow.
- **SC-006**: At least 90% of evaluated buyers identify the difference between active listing evidence and historical market context without assistance.

## Assumptions

- Aizen remains an anonymous, buyer-first Dubai property research product; sessions, notes, and decisions stay browser-local until a consented identity feature is separately specified.
- Existing persistent conversation checkpoints are reused rather than duplicated in a second memory store.
- Historical context is factual transaction context only. The matching rule is area plus available type and bedroom facts; no adjustment model, estimate, or appraisal is introduced.
- Existing typography may be refined but no new UI package, paid map service, external cost feed, property image feed, or new listing source is needed.
- The Dubai editorial direction uses warm ivory, deep forest/charcoal, restrained champagne accents, and high-information layout. Decorative motion remains subtle and honours reduced-motion preferences.
