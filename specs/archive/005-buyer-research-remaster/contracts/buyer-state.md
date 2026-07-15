# Browser Buyer State Contract

## Local keys

- `aizen-research-sessions`: ordered session metadata (`thread_id`, `title`, `last_activity_at`)
- `aizen-buyer-decisions`: property decision states keyed by property ID
- Existing saved-search and shortlist keys remain compatible

## Rules

- Session metadata enables only a same-browser session picker. Transcript content remains in the existing checkpoint store.
- Buyer decision state is private to the browser and never sent as listing feedback or source data.
- Invalid, unreadable, or older local values fail safely to an empty state; they must not crash the workspace.
