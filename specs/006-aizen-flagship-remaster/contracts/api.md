# Public API and SSE contract

- `POST /api/briefs/interpret` validates live model extraction and permits one repair attempt.
- `POST /api/runs` accepts `{brief, thread_id?}` only.
- `GET /api/conversations/{thread_id}` returns ordered messages, last brief, audited properties, and snapshot identity.
- `GET /api/market-context` returns robust transaction-price context.
- `POST /api/areas/compare` accepts two or three areas.

SSE order: `run_started`, zero or more paired `agent_step` events, `properties`, `sources`, optional `relaxation_options`, and `run_completed`. `answer_token` may occur during answer generation. Any failure terminates with `run_failed`. Prompts, secrets, raw exceptions, and model reasoning are forbidden.
