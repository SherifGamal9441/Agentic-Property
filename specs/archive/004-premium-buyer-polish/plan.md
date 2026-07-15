# Implementation Plan: Premium Buyer Polish

**Branch**: `004-premium-buyer-polish` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

## Summary

Improve Aizen's buyer decision flow in the existing React workspace: explicit shortlist and comparison actions, an evidence-led relative map, durable local research state, buyer-facing sorting, and a more composed luxury workspace. Reuse existing property fields, the current relative map, browser storage, and the agent/data APIs; add no provider, package, or backend endpoint.

## Technical Context

**Language/Version**: TypeScript 5.8, Python 3.13  
**Primary Dependencies**: React 19, Vite 7, FastAPI 0.139  
**Storage**: Browser local storage for buyer-local saved research; existing data services remain read-only for this feature  
**Testing**: Vitest + Testing Library; existing pytest regression suite  
**Target Platform**: Modern desktop and mobile browsers served by Docker Compose  
**Project Type**: React web application with FastAPI services  
**Performance Goals**: All client-side selection, scope, and sort changes feel immediate for the returned result set  
**Constraints**: Buyer-first, no paid map provider, no unsupported routing/amenity claims, accurate active/historical qualification, no Arabic localization  
**Scale/Scope**: Current result set and one-to-four comparison; local saved research remains device-scoped

## Constitution Check

No project constitution file is present. Plan passes the applicable product gates:

- Reuses supplied listing coordinates and existing historical context only.
- Does not add a map provider, account system, notification service, or backend persistence.
- Keeps factual listing evidence separate from UI state and buyer feedback.
- Adds explicit keyboard-accessible controls and tests for new state transitions.

Post-design check: pass. No new service, dependency, or trust boundary is introduced.

## Project Structure

```text
frontend/
├── src/
│   ├── App.tsx          # Buyer state, property actions, map, workspace rendering
│   ├── App.test.tsx     # Buyer-flow acceptance coverage
│   └── styles.css       # Editorial workspace, actions, map, responsive states
specs/004-premium-buyer-polish/
├── plan.md
├── research.md
├── data-model.md
├── contracts/ui-state.md
├── quickstart.md
└── tasks.md
```

**Structure Decision**: Keep the feature in the existing single workspace component. Its state is already local to the buyer session; extracting a component layer would add indirection without reducing risk for this scoped iteration.

## Implementation Approach

1. Extend client state with a distinct shortlist, durable saved-research shape, comparison helpers, and safe migration of older saved entries.
2. Add property-detail actions and reflect membership on cards, comparison tray, and map.
3. Upgrade the current relative map with scope controls, exact-coordinate groups, and location-confidence messaging based only on existing fields.
4. Add local sorting/reset interactions and refine empty/loading/result layouts with CSS and semantic controls.
5. Cover the buyer flows in frontend tests, then run frontend build/tests and project regression tests.

## Complexity Tracking

No constitution violations or unjustified complexity.
