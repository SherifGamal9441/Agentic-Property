# Research: Buyer Research Remaster

## Decision: Reuse checkpoint state for visible conversation history

**Rationale**: The graph already persists ordered user/assistant message pairs under browser-supplied thread IDs and the deployment has a persistent memory volume. A read-only history endpoint can expose that state without a second conversation database.

**Alternatives considered**:

- Duplicate messages into a new browser-only transcript: rejected because it loses history after an otherwise supported service restart and duplicates source of truth.
- Add accounts and a server-side session catalogue: deferred because identity, consent, retention, and cross-device privacy are explicitly out of scope.

## Decision: Use filtered reported historical context, not valuation logic

**Rationale**: Historical listing data contains area, type, bedrooms, transaction date, price, and size. Matching on area plus available type/bedrooms produces an explainable context set. A zero result is useful evidence of insufficiency.

**Alternatives considered**:

- Area-only figures for every home: retained only when the selected home lacks type or bedrooms; otherwise too broad to call comparable.
- Modelled price adjustments or estimated valuations: rejected because the project has no supported adjustment inputs and must not invent financial conclusions.

## Decision: Keep buyer decisions browser-local

**Rationale**: Save/maybe/rule-out and private notes improve a buyer's workflow immediately, fit existing saved-search behavior, and add no consent boundary.

**Alternatives considered**:

- Persist decisions beside listings: rejected because buyer opinions must not alter factual source records.
- Cross-device decision state: deferred pending explicit authenticated identity and privacy design.

## Decision: Refine the existing editorial system

**Rationale**: Existing typefaces and warm palette already establish an appropriate Dubai editorial direction. Tokens and layout discipline can create a more premium result than new libraries, stock imagery, or animation-heavy effects.

**Alternatives considered**:

- Add an external design system: rejected because current components are limited and this would increase visual/maintenance surface.
- Generate decorative property images: rejected because the product is evidence-first and images would imply unverified listing facts.
