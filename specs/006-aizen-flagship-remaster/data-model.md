# Data model

## BuyerBrief

`version`, `mode`, `original_query`, `currency`, and ordered `criteria`.

## Criterion

`id`, buyer-readable `label`, `priority`, supported `field`, `operator`, scalar `value`, and `verifiable`.

Supported fields are `area`, `price`, `property_type`, `bedrooms`, `bathrooms`, `furnishing`, `completion_status`, `building_name`, and `completion_year`. Unsupported lifestyle wishes have null field/operator/value and remain visible with `verifiable=false`.

## Listing evidence

Each result carries identity, reported price and facts, exact coordinate status, captured source URL, observation date, snapshot identity, criterion evaluations, fit, evidence coverage, and suitability. Whole-building fields use the `building_*` prefix. No verified unit fields exist in schema version 2.

## Browser-local state

Thread identity, saved brief/session index, shortlist IDs, comparison IDs, buyer status, private notes, and affordability inputs. Blank financial inputs remain unknown.
