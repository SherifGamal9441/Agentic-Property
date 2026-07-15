# Tasks: Premium Buyer Polish

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [ui-state contract](contracts/ui-state.md), [quickstart.md](quickstart.md)

## Phase 1: Setup

- [X] T001 Confirm current frontend test baseline and existing workspace state in `frontend/src/App.test.tsx` and `frontend/src/App.tsx`

## Phase 2: Foundational buyer state

- [X] T002 Add regression tests for explicit property actions, saved research, map scope, and sorting in `frontend/src/App.test.tsx`
- [X] T003 Add shortlist, comparison, saved-research migration, reset, and buyer-sort state helpers in `frontend/src/App.tsx`

## Phase 3: User Story 1 - Build a deliberate shortlist (Priority: P1)

**Goal**: Buyers can add or remove shortlist and comparison entries from property detail, with membership visible throughout the decision flow.

**Independent Test**: Open a property and add/remove both memberships; compare four homes and reject a fifth without changing the first four.

- [X] T004 [US1] Render distinct shortlist and comparison actions plus membership indicators in `frontend/src/App.tsx`
- [X] T005 [US1] Style buyer actions, selection indicators, and comparison-tray state in `frontend/src/styles.css`
- [X] T006 [US1] Verify drawer, cards, and comparison limit behavior in `frontend/src/App.test.tsx`

## Phase 4: User Story 2 - Use location as decision evidence (Priority: P1)

**Goal**: Buyers can scope the evidence-led map and inspect overlapping locations without false precision.

**Independent Test**: Switch all/shortlist/comparison scopes, inspect an overlap group, and verify exact versus area-only messaging.

- [X] T007 [US2] Add map scopes, exact-coordinate groups, selection sync, and confidence messaging in `frontend/src/App.tsx`
- [X] T008 [US2] Style map scopes, grouped pins, and confidence states in `frontend/src/styles.css`
- [X] T009 [US2] Verify scoped map and overlap selection flows in `frontend/src/App.test.tsx`

## Phase 5: User Story 3 - Return to an organized decision (Priority: P2)

**Goal**: Same-device saved research retains buyer criteria and shortlist and accurately explains snapshot changes.

**Independent Test**: Save, reload, restore, reset, and compare prior/new result sets.

- [X] T010 [US3] Persist and restore structured criteria and shortlist, categorize saved-search changes, and add reset actions in `frontend/src/App.tsx`
- [X] T011 [US3] Verify saved-research restoration, change categories, and reset confirmation in `frontend/src/App.test.tsx`

## Phase 6: User Story 4 - Experience a composed premium workspace (Priority: P2)

**Goal**: Empty, loading, partial, and result states keep editorial warmth and purposeful hierarchy.

**Independent Test**: Review workspace states on desktop and mobile without a large unused center region or ingestion jargon.

- [X] T012 [US4] Render intentional empty and status states while retaining buyer-facing active-data language in `frontend/src/App.tsx`
- [X] T013 [US4] Refine central workspace layers, empty state, loading state, and responsive composition in `frontend/src/styles.css`
- [X] T014 [US4] Verify empty workspace hierarchy and no internal ingestion copy in `frontend/src/App.test.tsx`

## Phase 7: User Story 5 - Move through research without friction (Priority: P3)

**Goal**: Buyers can sort and navigate controls without losing evidence or accessibility.

**Independent Test**: Change sort and use keyboard-accessible drawer actions; unknown values remain visibly unknown.

- [X] T015 [US5] Add buyer-relevant sorting and accessible control labels in `frontend/src/App.tsx`
- [X] T016 [US5] Verify sorting and primary control accessibility in `frontend/src/App.test.tsx`

## Phase 8: Validation

- [X] T017 Run frontend tests/build, full pytest suite, Docker Compose configuration validation, and diff check from repository root

## Dependencies & Implementation Strategy

- T001–T003 establish shared local state before UI stories.
- US1 and US2 follow shared state; US3 depends on persisted shortlist shape from T003.
- US4 and US5 follow functional state work without changing services.
- Finish with T017 only after all UI and test tasks pass.

**MVP**: T001–T009 delivers direct property actions and an honest decision map. Remaining tasks complete continuity and quality-of-life polish.
