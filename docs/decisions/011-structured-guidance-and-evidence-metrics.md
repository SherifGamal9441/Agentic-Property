# ADR 011: Structured guidance and evidence metrics

**Status:** Accepted

## Context

Free-form agent prose arrived as an undifferentiated paragraph and could overstate completeness. Adding a generic model confidence percentage would look reassuring without measuring a defensible quantity.

## Decision

Property search returns a validated `PropertyGuidance` contract containing an outcome, deterministically ordered best/runner-up IDs, coded reasons, criterion-linked caveats, and one constrained next action. References must exist in the audited result, caveats must match deterministic evaluations, and unknown facts cannot become positive reasons. One malformed-JSON repair attempt is allowed; a second invalid response fails calmly. React owns the buyer-readable wording. Cited web research remains prose but is buffered until completion.

The completion reveal shows at most three primary numbers: released suitable/conditional homes, candidates audited, and top-match evidence coverage. Evidence coverage describes confirmed-criterion evaluation coverage, not model confidence or complete property knowledge. Fit and matched/unknown counts remain secondary details. Stable-order tie-breaks are disclosed.

## Consequences

Property output is easier to scan and safer to audit. SSE gains a `guidance` event plus candidate/audited counts. Backend tests enforce reference integrity and ordering; frontend tests enforce labels, caveat wording, and completion prominence.
