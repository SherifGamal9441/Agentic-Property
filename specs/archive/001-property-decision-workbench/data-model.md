# Data Model: Property Decision Workbench

## PropertyResult

Normalized presentation record sent by the agent API.

| Field | Rules |
|---|---|
| `id` | Stable string identifier; required. |
| `title`, `area`, `property_type` | Display strings; use explicit unavailable label when absent. |
| `price`, `beds`, `baths`, `size_sqft`, `parking_spaces`, `year_of_completion` | Nullable values; UI must not coerce null to zero. |
| `currency` | Required when price exists; normally AED. |
| `data_status` | `active_dataset_listing`, `historical_insight`, or `web_research`; required. |
| `source_url`, `source_name` | Nullable evidence fields. |
| `observed_at` | Nullable ISO date/time representing listing or dataset observation date. |
| `freshness_label` | Human-readable source age/status derived from `observed_at`. |
| `dataset_snapshot_id`, `dataset_snapshot_at` | Nullable active-data snapshot evidence; required for `active_dataset_listing` when source exposes it. |
| `latitude`, `longitude`, `location_status` | Coordinates nullable; status is `exact`, `approximate`, or `unavailable`. Only valid coordinates are map eligible. |
| `fit_score`, `score_factors` | Nullable evidence-backed rank value and ordered reasons. |
| `matched_criteria`, `unmatched_criteria` | Lists; empty list is valid. |

## SearchBrief

Normalized user intent used by retrieval and ranking.

| Field | Rules |
|---|---|
| `area_name`, `property_type`, `completion_status` | Optional normalized filters. |
| `budget_min_aed`, `budget_max_aed`, `beds_min`, `baths_min`, `size_min_sqft` | Optional numeric filters. |
| `currency`, `exchange_rate` | Preserve original buyer currency and conversion evidence when conversion occurs. |
| `applied_criteria` | Ordered display-safe criteria presented with results. |
| `preference_level` | Each user-visible criterion is `must_have` or `nice_to_have`; missing a must-have remains visible in rank evidence. |

## Conversation

| Field | Rules |
|---|---|
| `thread_id` | Browser-generated stable identifier reused until reset. |
| `messages` | Ordered user/assistant entries managed by existing checkpoint system. |
| `started_at`, `last_active_at` | Optional operational metadata; no personal profile is added in this scope. |

## ComparisonSet

| Field | Rules |
|---|---|
| `selected_ids` | Ordered, unique subset of current results; minimum zero, maximum four. |
| `available_ids` | Current search results eligible for selection. |
| `comparison_fields` | Stable presentation fields: price, status, beds, baths, size, completion, furnishing, parking, source/freshness, fit reasons. |

## DecisionSheet

| Field | Rules |
|---|---|
| `property_ids` | Ordered selection of one through four current results. |
| `comparables` | Historical market summaries with date range and evidence status. |
| `ownership_cost` | Explicit input values, derived totals, source notes, and assumptions. |
| `generated_at` | Browser generation time; printable/exportable without server-side sharing. |

## SavedSearch

| Field | Rules |
|---|---|
| `id`, `name`, `brief` | Browser-local stable identity, buyer label, and normalized criteria. |
| `saved_at`, `last_seen_at` | Local timestamps. |
| `last_seen_snapshot_id` | Snapshot identity used for last comparison. |
| `last_result_ids` | Result identity set used to calculate in-app changes. |
| `change_summary` | New, removed, and changed result counts from a newer snapshot; no alert when snapshot is unchanged. |

## DatasetSnapshot

| Field | Rules |
|---|---|
| `id`, `observed_at` | Active dataset identity/time available after database load. |
| `source_description` | Explains that snapshot originated from loaded CSV data. |
| `status` | `current`, `stale`, or `unknown`; never `real_time`. |

## RunStatus

| Field | Rules |
|---|---|
| `phase` | `started`, `progress`, `completed`, or `failed`. |
| `code` | Safe machine-readable code on failure. |
| `message` | Buyer-safe explanation; never raw exception text. |
| `retryable` | Indicates whether user can retry same brief. |
