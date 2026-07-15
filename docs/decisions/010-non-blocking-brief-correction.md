# ADR 010: Non-blocking brief correction

**Status:** Accepted

## Context

The full-page “Confirm what Aizen understood” step made a correct interpretation feel like unfinished work and delayed the product's main value. Removing structured validation would weaken deterministic filtering and evidence audit.

## Decision

The initial **Find matching homes** submission authorizes a successfully validated `BuyerBrief` and starts `/api/runs` immediately. Raw prompts remain invalid at the run boundary. The active criteria stay visible as compact chips. **Edit brief** creates a disposable draft; closing discards it and **Apply & rerun** commits it through a fresh live run. No-result relaxation opens the same editor and never changes a criterion automatically.

Interpretation and runs share an abortable lifecycle. Failure retries only the failed stage, cancellation keeps the validated brief, and recent searches rerun stored briefs without replaying old output.

## Consequences

The happy path needs one action, while buyer authority and auditability remain explicit. Frontend tests must cover cancellation, draft discard/apply, focus restoration, retry, and the absence of the old confirmation page.
