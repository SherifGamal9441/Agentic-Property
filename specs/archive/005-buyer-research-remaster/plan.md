# Implementation Plan: Buyer Research Remaster

**Branch**: No branch requested | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

## Summary

Turn the existing evidence-first workspace into a durable buyer decision experience. Reuse LangGraph checkpoint state for visible same-browser conversation history, replace the decision sheet's historical placeholder with factual filtered transaction summaries, correct per-home ownership-cost presentation, persist lightweight buyer decisions locally, and apply one restrained editorial accessibility pass.

## Technical Context

**Language/Version**: Python 3.13; TypeScript 5.8  
**Primary Dependencies**: FastAPI, LangGraph SQLite checkpointer, React 19, Vite 7  
**Storage**: Existing checkpoint SQLite database for transcript; browser local storage for research-session index and buyer decisions; PostgreSQL/SQLite historical listing data remains read-only  
**Testing**: pytest; Vitest and Testing Library  
**Target Platform**: Docker Compose services and modern desktop/mobile browsers  
**Project Type**: FastAPI services with React single-page buyer workspace  
**Performance Goals**: Conversation history and up to four historical-context summaries appear without a full page reload; local decision actions respond immediately  
**Constraints**: Existing evidence only; no accounts, paid maps, external cost feeds, new packages, fake imagery, real-time scraping claims, or Arabic localization  
**Scale/Scope**: One browser's opaque session identities, visible transcript, one-to-four comparison, and factual historical context per selected home

## Constitution Check

Pass:

- Reuse current checkpointer, historical data service, agent API, browser storage, and fonts.
- Keep active listings distinct from historical context; retain no-cost relative map constraints.
- Calculate money only from reported price and buyer-entered amounts; no implied fees or valuation.
- Keep anonymous browser data local; no account, identity, CRM, or notification system.

## Project Structure

```text
src/
├── agent_api/app.py              # Run stream, transcript read endpoint, market-context proxy
├── data_service/app.py           # Filtered factual historical-context summary
├── memory/long_term_memory.py    # Existing checkpoint access remains shared
└── agents/                       # Existing graph and conversation state

frontend/src/
├── App.tsx                       # Session, buyer-decision, comparison, and modal orchestration
├── App.test.tsx                  # Browser acceptance flows
└── styles.css                    # Tokens, workspace hierarchy, responsive/accessibility states

tests/
├── agent_api/test_app.py         # Transcript endpoint contract
└── data_service/test_app.py      # Historical-context filtering and unknown-value safety

specs/005-buyer-research-remaster/
├── research.md
├── data-model.md
├── contracts/
│   ├── conversation-history.md
│   ├── market-context.md
│   └── buyer-state.md
├── quickstart.md
└── tasks.md
```

**Structure Decision**: Keep existing service boundaries. Add only focused browser components when they make the already-large `App.tsx` materially clearer; do not add a component framework or state library.

## Implementation Approach

1. Add read-only transcript retrieval keyed by a validated opaque thread ID. It loads saved graph state through the existing checkpointer, returns only ordered `conversation_history`, and exposes no session listing or cross-browser discovery.
2. Extend market-context summaries to filter historical records by required area plus optional matching property type and bedroom count. Return only count, period, price range, unit-price range, and matching basis; use no valuation or adjustment.
3. In browser state, retain a local session index (ID, title, last activity) and retrieve transcript on current/selected session. Persist buyer decision status and optional notes separately from listing evidence.
4. Load historical context for each selected property when the decision sheet opens. Render status per home and a real comparison matrix; treat unavailable values as unavailable.
5. Reframe cost inputs as buyer assumptions: acquisition total per home is reported price plus entered transfer, finance, and moving amounts; annual service remains separate. Blank remains not entered.
6. Consolidate visual language around existing Cormorant Garamond/Manrope, warm ivory, forest/charcoal contrast, and restrained champagne accent. Improve focus, dialog behavior, reduced motion, responsive reflow, and print without adding visual fiction.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Existing services and browser state cover the feature. | N/A |
