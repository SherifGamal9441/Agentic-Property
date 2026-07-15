# Tasks: Buyer Research Remaster

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts](contracts/), [quickstart.md](quickstart.md)  
**Prerequisites**: Existing buyer-workspace implementation and maintained test suites  
**Tests**: Required. Each behavior task begins with a focused failing test.

## Phase 1: Setup and shared contracts

- [X] T001 [P] Add failing conversation-history endpoint tests in `tests/agent_api/test_app.py`
- [X] T002 [P] Add failing filtered historical-context tests in `tests/data_service/test_app.py`
- [X] T003 [P] Add failing session-history, market-evidence, costs, buyer-decision, and accessibility tests in `frontend/src/App.test.tsx`
- [X] T004 Define browser-local session and buyer-decision types plus safe storage migration helpers in `frontend/src/App.tsx`

## Phase 2: Foundational evidence access

- [X] T005 [P] Add validated read-only conversation-history retrieval using the existing checkpointer in `src/agent_api/app.py`
- [X] T006 Add `GET /api/conversations/{thread_id}` safe response and unknown-session behavior in `src/agent_api/app.py`
- [X] T007 [P] Extend historical-context filtering and matching-basis output in `src/data_service/app.py`
- [X] T008 Forward optional type and bedroom context filters through `GET /api/market-context` in `src/agent_api/app.py`
- [X] T009 Verify API and data-service contracts in `tests/agent_api/test_app.py` and `tests/data_service/test_app.py`

**Checkpoint**: Existing memory and historical data are available to the browser through safe, factual contracts.

## Phase 3: User Story 1 - Continue visible property research (Priority: P1)

**Goal**: Make persisted conversation usable as a same-browser buyer research timeline.

**Independent Test**: Run, refresh, reopen, and continue a buyer session without history mixing.

- [X] T010 [US1] Implement session index persistence, transcript loading, current-session selection, and new-session behavior in `frontend/src/App.tsx`
- [X] T011 [US1] Render the ordered research timeline and session picker in `frontend/src/App.tsx`
- [X] T012 [US1] Style calm timeline, current-session, empty-history, and unavailable-history states in `frontend/src/styles.css`
- [X] T013 [US1] Verify same-browser history, continuation, and new-session isolation in `frontend/src/App.test.tsx`

## Phase 4: User Story 2 - Compare homes with real market evidence (Priority: P1)

**Goal**: Replace decision-sheet placeholder copy with factual historical evidence for each selected home.

**Independent Test**: Compare homes with matching and missing historical evidence and verify no active/valuation claim appears.

- [X] T014 [US2] Load historical context per selected property with explicit loading, unavailable, and matching-basis states in `frontend/src/App.tsx`
- [X] T015 [US2] Render historical record count, covered period, price range, and unit-price range in the decision sheet in `frontend/src/App.tsx`
- [X] T016 [US2] Style comparison evidence matrix and historical-status treatments in `frontend/src/styles.css`
- [X] T017 [US2] Verify factual historical decision-sheet output and insufficient-evidence handling in `frontend/src/App.test.tsx`

## Phase 5: User Story 3 - Understand real cost of each choice (Priority: P1)

**Goal**: Show buyer-entered costs transparently per selected property.

**Independent Test**: Enter one-off and annual amounts for two homes and verify totals, blanks, and labels.

- [X] T018 [US3] Replace combined entered-cost display with typed buyer cost assumptions and per-property purchase totals in `frontend/src/App.tsx`
- [X] T019 [US3] Render distinct annual-service and not-entered states in the decision sheet in `frontend/src/App.tsx`
- [X] T020 [US3] Style cost assumption inputs, totals, and print layout in `frontend/src/styles.css`
- [X] T021 [US3] Verify per-home purchase totals, separate annual service, and blank input disclosure in `frontend/src/App.test.tsx`

## Phase 6: User Story 4 - Make a composed buyer decision (Priority: P2)

**Goal**: Let buyers keep, defer, or rule out homes without mutating source evidence.

**Independent Test**: Change status and private note, refresh same browser state, and reverse the decision.

- [X] T022 [US4] Implement browser-local buyer decision state and private note persistence in `frontend/src/App.tsx`
- [X] T023 [US4] Render reversible saved/maybe/ruled-out actions across property card, detail, comparison, and decision sheet in `frontend/src/App.tsx`
- [X] T024 [US4] Style decision actions and status badges without using color as their only indicator in `frontend/src/styles.css`
- [X] T025 [US4] Verify persistence, reversibility, and evidence immutability in `frontend/src/App.test.tsx`

## Phase 7: User Story 5 - Trust an elegant, honest workspace (Priority: P2)

**Goal**: Deliver one disciplined luxury design and accessible interaction standard across the buyer journey.

**Independent Test**: Exercise empty, loading, timeline, detail, comparison, decision-sheet, mobile, keyboard, and print states.

- [X] T026 [US5] Consolidate existing visual values into editorial CSS tokens and apply clear action hierarchy in `frontend/src/styles.css`
- [X] T027 [US5] Add focus management, visible focus, modal semantics, and reduced-motion support in `frontend/src/App.tsx` and `frontend/src/styles.css`
- [X] T028 [US5] Refine responsive workspace, comparison, timeline, decision-sheet, and print composition in `frontend/src/styles.css`
- [X] T029 [US5] Verify keyboard, focus, reflow, and buyer-facing state copy in `frontend/src/App.test.tsx`

## Phase 8: Integration and release checks

- [X] T030 Run focused API/data tests from `tests/agent_api/test_app.py` and `tests/data_service/test_app.py`
- [X] T031 Run browser regression suite with `frontend/npm run test:gate`
- [X] T032 Build browser bundle with `frontend/npm run build`
- [ ] T033 Validate end-to-end flows in `specs/005-buyer-research-remaster/quickstart.md`

## Dependencies and execution order

`T001–T004 → T005–T009 → US1 → US2 → US3 → US4 → US5 → T030–T033`

- US1 depends on checkpoint transcript access.
- US2 depends on filtered historical-context access.
- US3 uses the existing decision-sheet shell and is independent of session persistence.
- US4 reuses local storage helpers from T004.
- US5 follows functional work to avoid visual churn masking behavior defects.

## MVP

Complete T001–T017: buyer-visible conversation history and factual decision-sheet market evidence. This fixes the two current trust gaps before expanding buyer decision state and visual polish.
