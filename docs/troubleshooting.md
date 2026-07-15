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

Do not relax automatically. Confirm DVC identity and database record counts, open **Edit brief**, and inspect the highlighted blocked criterion. **Apply & rerun** is the only way to commit a relaxation. Replace the preset before release if the frozen snapshot genuinely changed.

## A run was cancelled

The validated brief remains available. Select **Run again** to start a fresh live request or **Edit brief** to correct it. Cancelled, failed, and recent-search runs never replay a prior answer or result set.

## Clipboard is unavailable

The browser Clipboard API may require a secure context or explicit permission. The decision workspace remains usable; no toast or hidden fallback stores the summary.

## Map unavailable

OpenFreeMap requires network access. Exact supplied coordinates remain in the fallback list and missing coordinates remain labelled unavailable.
