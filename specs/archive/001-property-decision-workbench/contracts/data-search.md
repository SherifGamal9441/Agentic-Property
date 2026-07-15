# Contract: Data Search Boundaries

## Search input

Active and historical search requests accept existing normalized filters plus bounded result controls.

| Field | Rules |
|---|---|
| `limit` | Positive bounded integer; service-enforced maximum protects database and model context. |
| `offset` or cursor | Optional pagination mechanism; one mechanism selected during implementation and used consistently. |
| sort | Stable sort with documented default. |

## Search output

| Field | Rules |
|---|---|
| `total_matches` | Count before pagination, when practical. |
| `returned_count` | Exact returned row count. |
| `listings` | Rows with nullable source fields preserved. |
| `data_observed_at` | Dataset/listing observation timestamp where available. |
| `dataset_snapshot_id`, `dataset_snapshot_at` | Active CSV-load snapshot evidence exposed to buyer-facing result contract. |

## Rules

- Active and historical endpoints retain separate behavior.
- Historical rows cannot be elevated to current-listing recommendations.
- Money values use exact storage/transport semantics chosen during implementation; browser formatting must not fabricate a value.
- Active endpoint describes loaded CSV snapshot data, never on-demand scraping or real-time coverage.
