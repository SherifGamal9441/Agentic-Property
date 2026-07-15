# Data provenance

## Frozen snapshot identity

| Dataset | Rows | DVC MD5 | SHA-256 | Frozen date |
|---|---:|---|---|---|
| `active_dld.csv` | 3,087 | `074fdb1bd7999b5925c2cb9d570aa756` | `d52c72dcc9fd971f93d1c98445b57068a331b3e52a43afc54477b44cb61a8467` | 2026-07-02 |
| `historical_dld.csv` | 28,809 | `352765cce81a0bc215b7c812d68e44ea` | `8f481b75245d1e0782931578059442036ee72fb30e974fe2997f1bf5ca112b32` | 2026-07-02 |

Schema version: **2**. DVC pointers are committed; full CSVs remain DVC outputs.

## Controlled enrichment result

One source API attempt was made for true unit area and dedicated unit parking. The source returned HTTP 429 and did not prove those unit fields. The evidence-safe fallback is active: unit area, price per square foot, dedicated parking, and price assessment are withheld. No building total is used as a unit substitute.

## Schema dictionary

Buyer-verifiable listing facts: property ID, reported price, type, bedrooms, bathrooms, address, furnishing, completion status, post date, building name, completion year, area name, coordinates, and source link.

Building-only facts: `building_total_parking_spaces`, `building_floors`, `building_total_area_sqft`, and `building_elevators`. These may describe a whole building and never participate in buyer fit.

## Validation

`scripts/migrate_snapshot_schema.py` performs the lossless header migration and checks record counts, duplicate active property IDs, non-negative prices, coordinate ranges, source URL shape, and SHA-256. `scripts/preflight.py` verifies DVC MD5 and file size before demo startup.

External links are captured references and may expire. Snapshot wording must never imply real-time inventory.
