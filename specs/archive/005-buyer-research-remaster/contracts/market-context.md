# Historical Market Context Contract

## `GET /market-context`

Query fields:

- `area` — required reported area
- `property_type` — optional reported property type
- `beds` — optional reported bedroom count

The agent API exposes the same buyer-safe shape at `GET /api/market-context` and forwards only these fields.

### Response

```json
{
  "area": "Dubai Marina",
  "matching_basis": ["area", "property_type", "beds"],
  "record_count": 42,
  "period_start": "2024-01-05",
  "period_end": "2026-05-27",
  "price_min": 1200000,
  "price_max": 2150000,
  "price_per_sqft_min": 1295,
  "price_per_sqft_max": 1864
}
```

Values unavailable from matching reported rows are `null`. A zero `record_count` has null ranges and is rendered as unavailable historical evidence. The endpoint does not return a valuation, active listing, inferred fee, or transaction-level personal information.
