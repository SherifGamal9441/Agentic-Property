# Feature Specification: Restore Buyer Experience

**Feature Branch**: `[002-restore-buyer-experience]`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: Restore the first iteration's visual quality using the user-provided Aizen reference screenshot, without restoring demo mode or losing active-data buyer features.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recognize a premium buyer workspace (Priority: P1)

A buyer lands on Aizen and immediately understands its purpose, sees an editorial and calm property-research experience, and can begin a property brief without encountering a demo/live-mode choice.

**Why this priority**: The approved first iteration established the product's visual identity. Functional additions must not make the product feel less polished or less focused.

**Independent Test**: Compare desktop rendering against the supplied reference at a standard wide viewport and verify the required visual hierarchy, journey, and start action are present while synthetic data claims are absent.

**Acceptance Scenarios**:

1. **Given** a first-time buyer opens Aizen, **When** the landing view loads, **Then** they see the editorial hero, restrained warm palette, prominent buyer value proposition, and one clear property-brief action.
2. **Given** the buyer sees the former confidence-panel region, **When** no evidence-backed result exists yet, **Then** it communicates an honest product/data promise rather than synthetic confidence or a fake property result.
3. **Given** the buyer uses the header, **When** they scan available actions, **Then** no demo-mode control, representative scenario, or claim of real-time scraping appears.

---

### User Story 2 - Move from inspiration to research without visual disruption (Priority: P1)

A buyer begins a brief from the hero or guided-start area and enters the workspace without losing the visual rhythm, wayfinding, or confidence of the landing view.

**Why this priority**: The first iteration made the path from promise to research clear. The restored experience must preserve that journey while using real data.

**Independent Test**: Begin a brief from each available entry point and verify the buyer reaches the same research workspace, with the same active-data disclosure and usable controls.

**Acceptance Scenarios**:

1. **Given** a buyer selects the primary hero action, **When** they start a brief, **Then** focus moves to the property brief workspace without a broken layout or duplicate form.
2. **Given** a buyer scans guided starts, **When** they choose or edit one, **Then** it becomes an editable brief and does not submit synthetic listings.
3. **Given** a buyer receives zero, one, or multiple results, **When** the workspace updates, **Then** the transition preserves readable hierarchy and does not collapse the page into an unstructured utility view.

---

### User Story 3 - Use evidence features inside the restored visual system (Priority: P1)

A buyer can use active-data labels, map evidence, one-to-four comparison, saved searches, and decision sheets while the interface remains coherent with the approved first iteration.

**Why this priority**: Restoration is not a rollback of buyer capabilities; it is a visual and interaction-quality correction.

**Independent Test**: Exercise results, map selection, comparison, saved-search state, and decision sheet on the restored workspace; verify each remains usable and visually consistent.

**Acceptance Scenarios**:

1. **Given** active or historical evidence is displayed, **When** a buyer reads a result, **Then** freshness and provenance are visible but subordinate to the property decision flow.
2. **Given** a buyer selects one through four homes, **When** the comparison tray renders, **Then** it remains visually balanced at every supported selection count.
3. **Given** a result lacks coordinates or fields, **When** it appears in the map or card, **Then** the unavailable state is clear and does not create an empty-looking or broken visual region.

---

### User Story 4 - Retain quality across screen sizes and states (Priority: P2)

A buyer sees a composed experience on common desktop and mobile widths, including empty, loading, result, comparison, drawer, and failure states.

**Why this priority**: A polished landing view cannot be limited to the initial desktop screenshot.

**Independent Test**: Review representative visual states at wide desktop, tablet, and narrow mobile widths; verify no clipped controls, overlapping panels, unreadable text, or inaccessible controls.

**Acceptance Scenarios**:

1. **Given** a narrow viewport, **When** the buyer opens the workspace or decision sheet, **Then** controls remain reachable and content remains readable without horizontal scrolling.
2. **Given** a loading or failure state, **When** it replaces result content, **Then** it uses the same visual language and retains a clear recovery path.

### Edge Cases

- A buyer may open the page with no search history, no saved search, and no available dataset result.
- Long property titles, areas, and evidence explanations must not disrupt card, map, comparison, or decision-sheet layout.
- The supplied screenshot contains prior demo-mode and representative confidence content; those visual positions are reference only and must not restore those behaviors or claims.
- The reference is a desktop composition, not a requirement for pixel-identical rendering or unsupported screen sizes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use the supplied first-iteration screenshot as the visual reference for hierarchy, editorial tone, spacing, palette, typography contrast, and progression from hero to workspace.
- **FR-002**: System MUST restore a composed landing hierarchy containing brand navigation, buyer value proposition, primary brief action, evidence-honest supporting panel, step-based journey, and guided-start-to-workspace transition.
- **FR-003**: System MUST retain an honest active-dataset disclosure and MUST NOT display demo-mode controls, synthetic homes, synthetic confidence scores, or real-time-scraping claims.
- **FR-004**: System MUST preserve the buyer capabilities already accepted in the prior decision-workbench specification: active/historical labels, source and snapshot evidence, relative location evidence, one-to-four comparison, saved-search indicators, and buyer decision sheet.
- **FR-005**: System MUST make the property brief workspace the visual continuation of the landing experience, with guided starts supporting rather than competing with the primary brief entry.
- **FR-006**: System MUST make empty, loading, partial-data, historical-context, and failure states visually intentional and readable.
- **FR-007**: System MUST preserve accessible names, visible focus, keyboard access, and readable contrast for all restored controls and overlays.
- **FR-008**: System MUST keep desktop, tablet, and mobile layouts free of clipped interactive controls, overlapping content, and horizontal scrolling at supported widths.
- **FR-009**: System MUST remove obsolete or conflicting visual rules introduced by the prior redesign when they no longer support the restored experience.
- **FR-010**: System MUST validate restoration against the supplied reference and representative real-data states before the next feature specification is implemented.

### Key Entities

- **Visual baseline**: User-supplied first-iteration reference image defining product tone and hierarchy, but not demo behavior or fictional data.
- **Buyer journey**: Landing, guided start, property brief, evidence review, comparison, and decision flow.
- **Workspace state**: Empty, researching, active-data result, historical context, partial-data result, failure, and selected-comparison states.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In visual acceptance review, the restored desktop landing and workspace preserve all five baseline characteristics: editorial hero, evidence-honest supporting panel, four-step journey, guided-start area, and spacious location-aware workspace.
- **SC-002**: 100% of reviewed landing, empty, loading, result, comparison, decision-sheet, and failure states retain active-data honesty and show no demo-mode or synthetic-result language.
- **SC-003**: Buyers can start a brief from the primary landing action and reach an editable property brief in one action.
- **SC-004**: At standard desktop, tablet, and mobile acceptance widths, 100% of primary controls remain visible, keyboard reachable, and free of horizontal page overflow.
- **SC-005**: Existing acceptance checks for map selection, one-to-four comparison, saved-search change indication, and buyer-entered cost inputs continue to pass after restoration.

## Assumptions

- The supplied screenshot is the authoritative visual baseline for this restoration pass.
- Restoration prioritizes the visual hierarchy and experience quality, not a pixel-for-pixel copy of a prior implementation.
- The buyer-first product scope, active-data definition, no-paid-map constraint, and no-Arabic-localization decision remain unchanged.
- This feature completes before implementation begins on the next buyer-feature specification.
