# Research: Buyer Intelligence Roadmap

## Decision: Reuse existing historical listings for market context

**Rationale**: Historical listing data already has area, price, date, and reported area fields. An aggregate is more honest and smaller than an external market-data integration.

**Alternatives considered**:

- Paid market data: rejected by project constraint.
- LLM-estimated market trend: rejected because it is not factual evidence.

## Decision: Keep research and feedback browser-local

**Rationale**: Existing saved searches are local and cross-device identity is explicitly gated. Local feedback provides immediate bounded signal without inventing a retention system.

**Alternatives considered**:

- Add accounts and notifications now: rejected; privacy, authentication, and delivery decisions are unresolved.
