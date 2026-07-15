# Public API and SSE contract

- `POST /api/briefs/interpret` validates live model extraction and permits one repair attempt. The originating search submission authorizes a successful brief for immediate execution.
- `POST /api/runs` accepts `{brief, thread_id?}` only; raw prompt-only calls are invalid.
- `GET /api/conversations/{thread_id}` returns ordered messages, last brief, audited properties, and snapshot identity.
- `GET /api/market-context` returns robust transaction-price context.
- `POST /api/areas/compare` accepts two or three areas.

Property-search SSE order: `run_started`, zero or more paired `agent_step` events, `properties`, `sources`, `guidance`, optional `relaxation_options`, and `run_completed`. `properties` includes `candidate_count`, `audited_count`, `total_matches`, `shown_count`, and audited properties. Property search does not stream partial prose. Web research may stream `answer_token`, but the UI buffers it until completion. Any failure terminates with `run_failed`. Prompts, secrets, raw exceptions, and model reasoning are forbidden.

`guidance` contains validated `PropertyGuidance`: `outcome`, deterministic best and runner-up IDs, coded reasons, criterion-linked caveats, and one constrained next action. One malformed-JSON repair attempt is allowed; an invalid second response fails calmly.
