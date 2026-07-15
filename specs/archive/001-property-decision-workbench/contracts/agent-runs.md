# Contract: Agent Run Stream

## Request

`POST /api/runs`

| Field | Required | Rules |
|---|---|---|
| `query` | Yes | Non-empty buyer brief, maximum existing request limit. |
| `thread_id` | Yes after browser initialization | Stable for current browser conversation; server may create one only for legacy callers. |

Demo mode is removed from the buyer contract.

## Stream events

| Event | Required data | Consumer behavior |
|---|---|---|
| `run_started` | `thread_id`, `mode: "active_dataset"` | Store thread ID if browser does not already hold it; enter loading state. |
| `agent_step` | `node`, `label`, `status` | Update visible progress without exposing internal diagnostics. |
| `properties` | `properties: PropertyResult[]`, `applied_criteria` | Replace prior property results; clear stale selection IDs not present in new results. |
| `answer_token` | `token` | Append response text. |
| `run_completed` | `thread_id`, `route`, `data_status` | End loading state and retain stable conversation. |
| `run_failed` | `code`, `message`, `retryable` | End loading state, preserve safe retry action, never expose exception details. |

## Rules

- `properties` may contain zero through the service result cap.
- Every `PropertyResult` obeys nullable-field rules in [data-model.md](../data-model.md).
- Active-data result must have `data_status: "active_dataset_listing"` plus snapshot evidence where available; it must not claim real-time availability.
- Historical result must have `data_status: "historical_insight"`; UI must not use active-listing call to action.
- Events are additive except `properties`, which represents current result set.
