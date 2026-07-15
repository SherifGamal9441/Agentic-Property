# ADR 009: Live-only failure behavior

**Status:** Accepted

Every agent run calls the selected provider. If the provider fails, Aizen returns a calm retryable error. It never replays a cached or preset response; presets only populate the buyer brief.
