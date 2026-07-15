# Scoring and evidence

## Criterion result

Each criterion is `matched`, `conflict`, `unknown`, or `unsupported`. A missing field is unknown, never a conflict. An unsupported lifestyle wish stays visible but does not enter fit arithmetic.

## Suitability

- A known must-have or deal-breaker conflict produces `excluded`.
- An unknown must-have or deal-breaker produces `conditional`.
- Otherwise the property is `suitable`.

Excluded rows are not emitted as ranked matches.

## Fit and coverage

Must-have weight is 3; nice-to-have weight is 1; deal-breakers are hard gates and have no fit weight. Fit is matched weight divided by all verifiable weighted criteria. Evidence coverage is criteria with a known matched/conflict result divided by all criteria. Stable order is suitability, descending fit, descending coverage, ascending reported price, then property ID.

Evidence coverage is not model confidence and is never labelled “AI confidence.” A value of 100% means every confirmed criterion has a captured evaluation; it does not mean the property record is complete. When fit and coverage tie, the UI discloses the reported-price and property-ID tie-break.

## Audit

Reflection verifies retrieved identity, active-source safety, captured source URL, observation date, and recomputed arithmetic. Invalid candidates are withheld with a safe issue. The LLM receives only audited facts for explanation and cannot generate a new score, valuation, fee, or benchmark.

Property guidance is a validated reference layer. Best and runner-up IDs must match deterministic order; reason codes may reference only audited matches and caveats must match criterion evaluations. Unknown facts cannot become positive reasons. React translates these references into buyer-readable sections. “No known criterion gaps in the captured fields” replaces absolute claims such as “no caveats.”

The completion surface limits primary metrics to released suitable/conditional homes, candidates audited, and top-match evidence coverage. Fit and matched/unknown counts remain secondary property details.

## Historical context

Historical reported prices are filtered with the 1.5×IQR rule and summarized as median plus 25th–75th percentile. Evidence is strong at 20+ usable records, limited at 5–19, and insufficient below 5. Distribution claims are withheld when insufficient. Unit-price claims remain unavailable.
