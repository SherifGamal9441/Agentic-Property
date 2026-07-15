# Implementation Plan: Restore Buyer Experience

**Branch**: none | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

## Summary

Restore the supplied editorial Aizen composition around the existing real-data buyer workspace. Keep all accepted decision-workbench behavior; remove only conflicting presentation rules and synthetic-demo affordances.

## Technical Context

**Language/Version**: TypeScript, React, CSS  
**Primary Dependencies**: Existing Vite frontend and testing library  
**Storage**: Existing browser-local conversation and saved-search storage  
**Testing**: Existing frontend component tests and production build  
**Target Platform**: Modern desktop and mobile browsers  
**Project Type**: Web application frontend  
**Performance Goals**: No additional network requests or client dependencies for restoration  
**Constraints**: Preserve active-data honesty, no paid map provider, accessible controls, no demo mode  
**Scale/Scope**: One landing/workspace surface and its existing result states

## Constitution Check

No project constitution file exists. Pass: reuse existing frontend and native browser behavior; no new dependency, service, or abstraction is required.

## Design Decisions

- Preserve the reference hierarchy: editorial hero, honest supporting panel, four-step journey, guided starts, and spacious workspace.
- Replace representative confidence with active-dataset messaging until evidence-backed results exist.
- Keep the existing result, map, comparison, saved-search, and decision-sheet state model; restoration changes their placement and presentation, not their contracts.
- Use CSS layout and existing semantic controls. Avoid image assets or a visual-library dependency.

## Project Structure

```text
frontend/
├── src/App.tsx           # Buyer journey and state placement
├── src/App.test.tsx      # Interaction and restoration regression checks
└── src/styles.css        # Reference-inspired responsive presentation
```

**Structure Decision**: Frontend-only restoration; no backend changes.

## Complexity Tracking

No exceptions. The existing application surface is sufficient.
