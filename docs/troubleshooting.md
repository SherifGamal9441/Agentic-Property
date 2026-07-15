# Troubleshooting

## Preflight fails provider configuration

Set only the variables required by `LLM_PROVIDER`. Docker uses `host.docker.internal` for host-served Ollama, vLLM, or compatible endpoints. Preflight prints variable names, never values.

## DVC checksum mismatch

Do not seed the database. Run `uv run dvc pull`, then rerun preflight. A missing or mismatched snapshot is a hard setup failure.

## PostgreSQL unavailable

The data service reports `database_backend=sqlite` and `degraded=true`. This is supported fallback behavior, not an invisible success. Restore PostgreSQL before the flagship rehearsal when possible.

## Provider error in the UI

The run is live-only. Check the endpoint from the host and container, selected model name, and provider key. Aizen intentionally has no cached fallback.

## Empty preset

Do not relax automatically. Confirm DVC identity and database record counts, inspect the structured brief, and replace the preset before release if the frozen snapshot genuinely changed.

## Map unavailable

OpenFreeMap requires network access. Exact supplied coordinates remain in the fallback list and missing coordinates remain labelled unavailable.
