# ADR 012: Editorial brief ledger and anchored navigation

**Status:** Accepted

The active buyer brief stays visible as a compact ledger rather than a second confirmation screen. Its original request is the headline; grouped criteria and counts make the contract legible at a glance. Editing creates a disposable draft and only **Apply & rerun** commits it, preserving the one-action search journey.

Top navigation and workspace tabs are view controls, not separate routes. Selecting one mounts its workspace and scrolls the heading below the sticky header. The initial page remains at the hero, same-view clicks still scroll, and reduced-motion preferences use an instant movement. This keeps the long decision workspace discoverable without adding a router or state library.
