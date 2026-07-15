# Data Model: Buyer Research Remaster

## Research session

| Field | Meaning | Validation |
|-------|---------|------------|
| `thread_id` | Opaque conversation identity | UUID retained by this browser only |
| `title` | Buyer-readable session label | Derived from first non-empty brief; bounded text |
| `last_activity_at` | Most recent local activity | ISO timestamp |
| `conversation_history` | Ordered buyer/Aizen messages | Read from existing checkpoint; each entry has `role` and non-empty `content` |

Transitions: new → active → retained locally; selecting another retained session makes it active. Starting a new session creates a new identity and does not erase retained session metadata.

## Historical context

| Field | Meaning | Validation |
|-------|---------|------------|
| `area` | Selected property's reported area | Required query field |
| `property_type` | Selected property's reported type | Optional filter; normalized to existing source convention |
| `beds` | Selected property's reported bedrooms | Optional non-negative integer filter |
| `matching_basis` | Facts used to filter evidence | Area plus only available compatible facts |
| `record_count` | Matching historical rows | Integer, zero allowed |
| `period_start` / `period_end` | Earliest/latest reported transaction dates | Nullable ISO dates |
| `price_min` / `price_max` | Range of reported prices | Nullable positive AED values |
| `price_per_sqft_min` / `price_per_sqft_max` | Range derived only from rows with positive reported size | Nullable positive AED values |

Transitions: loading → available or unavailable. A zero count is unavailable evidence, not an error or estimate.

## Cost assumption

| Field | Meaning | Validation |
|-------|---------|------------|
| `transfer` | Buyer-confirmed one-off transfer cost | Empty or non-negative AED amount |
| `finance` | Buyer-confirmed one-off finance cost | Empty or non-negative AED amount |
| `moving` | Buyer-confirmed one-off moving cost | Empty or non-negative AED amount |
| `annual_service` | Buyer-confirmed recurring annual service cost | Empty or non-negative AED amount |

`purchase_total = reported property price + entered transfer + entered finance + entered moving` only when price is reported. `annual_service` is never added to purchase total.

## Buyer decision state

| Field | Meaning | Validation |
|-------|---------|------------|
| `property_id` | References returned property | Required opaque property ID |
| `status` | Buyer classification | `saved`, `maybe`, or `ruled_out` |
| `note` | Optional private buyer note | Bounded plain text |
| `updated_at` | Last browser-local update | ISO timestamp |

Only local buyer state changes; no transition changes listing facts, source, ranking evidence, or historical data.
