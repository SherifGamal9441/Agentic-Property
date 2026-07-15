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

## Audit

Reflection verifies retrieved identity, active-source safety, captured source URL, observation date, and recomputed arithmetic. Invalid candidates are withheld with a safe issue. The LLM receives only audited facts for explanation and cannot generate a new score, valuation, fee, or benchmark.

## Historical context

Historical reported prices are filtered with the 1.5×IQR rule and summarized as median plus 25th–75th percentile. Evidence is strong at 20+ usable records, limited at 5–19, and insufficient below 5. Distribution claims are withheld when insufficient. Unit-price claims remain unavailable.
