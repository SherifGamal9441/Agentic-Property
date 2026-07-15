# Tasks: Property Decision Workbench

**Input**: Design documents in `specs/001-property-decision-workbench/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`  
**Tests**: Required. Each behavior task starts with a focused failing test.

## Phase 1: Baseline and foundations

- [X] T001 Verify current focused backend/frontend test commands and record baseline in `specs/001-property-decision-workbench/quickstart.md`
- [X] T002 Replace obsolete cached-tool integration expectation with active/historical routing in `tests/agents/test_pipeline_e2e.py`
- [X] T003 Add failing agent API payload/failure contract tests in `tests/agent_api/test_app.py`
- [X] T004 Add failing browser session, map, comparison, decision-sheet, and saved-search tests in `frontend/src/App.test.tsx`

## Phase 2: Evidence contract and persistence

- [X] T005 Add normalized nullable property evidence fields and safe run-failure codes in `src/agent_api/app.py`
- [ ] T006 Add active CSV snapshot metadata helper and data-service health exposure in `src/data_service/app.py`
- [X] T007 Add deterministic result score factors in `src/agent_api/app.py`
- [X] T008 Add named SQLite memory volume in `compose.yaml`
- [X] T009 Verify T003 agent API tests pass after T005-T008

## Phase 3: User Story 1 - Evaluate active property matches (Priority: P1)

**Goal**: Buyers receive active-snapshot evidence or honest source state.

- [X] T010 [US1] Add applied criteria and active/historical evidence to streamed property results in `src/agent_api/app.py`
- [X] T011 [US1] Add active dataset snapshot/source labels and no-result state in `frontend/src/App.tsx`
- [X] T012 [US1] Add result evidence presentation styles in `frontend/src/styles.css`
- [X] T013 [US1] Verify active, historical, no-result, and partial-data tests in `tests/agent_api/test_app.py` and `frontend/src/App.test.tsx`

## Phase 4: User Story 2 - Continue a property conversation (Priority: P1)

**Goal**: Follow-up briefs retain one browser conversation until reset.

- [X] T014 [US2] Persist browser thread ID and add new-conversation action in `frontend/src/App.tsx`
- [ ] T015 [US2] Verify stable thread identity and reset behavior in `frontend/src/App.test.tsx`

## Phase 5: User Story 3 - Inspect location evidence (Priority: P2)

**Goal**: Existing location view truthfully displays valid coordinates.

- [X] T016 [US3] Add failing one-pin, overlap, and missing-coordinate tests in `frontend/src/App.test.tsx`
- [X] T017 [US3] Validate coordinates, compute safe relative bounds, offset overlap pins, and remove invented landmarks in `frontend/src/App.tsx`
- [X] T018 [US3] Add relative-location and area-only styles in `frontend/src/styles.css`
- [X] T019 [US3] Verify location tests in `frontend/src/App.test.tsx`

## Phase 6: User Story 4 - Compare available matches (Priority: P2)

**Goal**: Buyers compare one through four returned homes.

- [X] T020 [US4] Add failing four-property and fifth-rejection tests in `frontend/src/App.test.tsx`
- [X] T021 [US4] Replace hard-coded three-item comparison limit/layout in `frontend/src/App.tsx`
- [X] T022 [US4] Add responsive one-to-four comparison styles in `frontend/src/styles.css`
- [X] T023 [US4] Verify comparison tests in `frontend/src/App.test.tsx`

## Phase 7: User Story 5 - Make a decision from evidence (Priority: P2)

**Goal**: Buyers make transparent, printable decision from shortlists.

- [X] T024 [US5] Add failing preference, decision-sheet, comparable, and cost-assumption tests in `frontend/src/App.test.tsx`
- [X] T025 [US5] Add must-have/nice-to-have controls and transparent score gaps in `frontend/src/App.tsx`
- [X] T026 [US5] Add browser-printable decision sheet with historical comparable summary and editable cost assumptions in `frontend/src/App.tsx`
- [X] T027 [US5] Add decision-sheet and print styles in `frontend/src/styles.css`
- [X] T028 [US5] Verify decision tests in `frontend/src/App.test.tsx`

## Phase 8: User Story 6 - Return to saved research (Priority: P3)

**Goal**: Buyers save browser-local searches and see newer-snapshot changes.

- [X] T029 [US6] Add failing browser-local saved-search and changed-snapshot tests in `frontend/src/App.test.tsx`
- [X] T030 [US6] Add local saved search storage and snapshot-change indicator in `frontend/src/App.tsx`
- [X] T031 [US6] Add saved-search styles in `frontend/src/styles.css`
- [X] T032 [US6] Verify saved-search tests in `frontend/src/App.test.tsx`

## Phase 9: User Story 7 - Use resilient active-data workspace (Priority: P3)

- [ ] T033 [US7] Render safe agent-failure state and retry action in `frontend/src/App.tsx`
- [ ] T034 [US7] Verify no raw exception exposure in `tests/agent_api/test_app.py` and `frontend/src/App.test.tsx`

## Phase 10: Integration and release checks

- [X] T035 Run Python focused test suite from `tests/`
- [X] T036 Run frontend `npm run test:gate` in `frontend/`
- [X] T037 Run frontend `npm run build` in `frontend/`
- [ ] T038 Build and validate `docker compose up --build` against `specs/001-property-decision-workbench/quickstart.md`

## Dependencies and execution order

`T001 → T002-T004 → T005-T009 → US1/US2 → US3/US4 → US5 → US6/US7 → T035-T038`

Frontend user stories share `frontend/src/App.tsx`; execute sequentially. Backend/API work completes before evidence UI. Each test task must fail before its corresponding implementation task.
