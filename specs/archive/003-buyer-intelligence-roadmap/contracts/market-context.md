# Market Context Contract

`GET /api/market-context?area=<area>` returns historical area evidence only.

```json
{
  "area": "Dubai Marina",
  "record_count": 42,
  "period_start": "2024-01-01",
  "period_end": "2025-12-31",
  "price_min": 1000000,
  "price_max": 2500000,
  "price_per_sqft_min": 900,
  "price_per_sqft_max": 1600
}
```

All absent aggregates are `null`; the browser labels this as insufficient historical evidence.
