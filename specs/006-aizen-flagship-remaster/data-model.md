# Data model

## BuyerBrief

`version`, `mode`, `original_query`, `currency`, and ordered `criteria`.

## Criterion

`id`, buyer-readable `label`, `priority`, supported `field`, `operator`, scalar `value`, and `verifiable`.

Supported fields are `area`, `price`, `property_type`, `bedrooms`, `bathrooms`, `furnishing`, `completion_status`, `building_name`, and `completion_year`. Unsupported lifestyle wishes have null field/operator/value and remain visible with `verifiable=false`.

## Listing evidence

Each result carries identity, reported price and facts, exact coordinate status, captured source URL, observation date, snapshot identity, criterion evaluations, fit, evidence coverage, and suitability. Whole-building fields use the `building_*` prefix. No verified unit fields exist in schema version 2.

## PropertyGuidance

`version`, deterministic `outcome`, audited best/runner-up property IDs, coded reasons, criterion-linked caveats, and a constrained next action. References are validated against the audited result and confirmed brief. Unknown facts cannot become positive reasons. Property-search prose is rendered by React; web research remains cited buffered prose.

## Run statistics

`candidate_count` is active inventory retrieved before evaluation. `audited_count` is processed by deterministic comparison/reflection. `total_matches` is the suitable and conditional set released by audit. Excluded identities and withheld candidates remain internal.

## Browser-local state

Thread identity, recent validated briefs, shortlist IDs, comparison IDs, buyer status, private notes, affordability inputs, and the affordability target ID. Prior answers and result sets are never replayed. Blank financial inputs remain unknown.
