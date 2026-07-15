# Data Model: Premium Buyer Polish

## Shortlist entry

| Field | Meaning | Rule |
|---|---|---|
| property ID | Buyer-selected listing | Unique within shortlist |
| snapshot | Last active snapshot seen | Preserved for stale-result messaging |

## Comparison selection

| Field | Meaning | Rule |
|---|---|---|
| property IDs | Ordered homes being reviewed together | One to four unique IDs |

## Saved research brief

| Field | Meaning | Rule |
|---|---|---|
| query | Free-text property brief | Required to save |
| criteria | Must-have, nice-to-have, deal-breaker values | Optional and buyer-editable |
| shortlist IDs | Saved decision set | Optional, unique IDs |
| result IDs | Last returned result set | Used for added/removed/unchanged state |
| snapshot | Last returned active snapshot | May be unavailable |

## Location group

| Field | Meaning | Rule |
|---|---|---|
| coordinate key | Exact supplied latitude/longitude pair | Only for valid exact coordinates |
| property IDs | Listings at that coordinate | One or more selectable homes |
| confidence | Exact, area-only, or unavailable | Never inferred from missing data |
