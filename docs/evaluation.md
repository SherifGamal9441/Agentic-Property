# Evaluation

## Automated release record

This table records the latest complete release-gate run.

| Gate | Verified result |
|---|---|
| Python | 75 passed |
| React/Vitest | 13 passed |
| Production build | Passed; 242.45 kB initial JS, MapLibre isolated in a lazy 1,055.12 kB chunk, no Vite size warning |
| Playwright journeys | 9 passed in Chromium |
| Compose configuration and health | Passed; PostgreSQL, data service, agent API, and frontend healthy |
| Data snapshot preflight | Passed; provider, checksums, Compose, services, and ports verified |
| Diff whitespace | Passed |

## Live provider rehearsal

Each preset was interpreted by the configured live model and executed through the real graph against snapshot `active-2026-07-02-v1`. No cached or replayed response was used.

| Preset | Candidates audited | Released matches | First ranked home | Evidence |
|---|---:|---:|---|---|
| Ready 2BR in Dubai Marina under AED 2M, no off-plan | 3 | 3 | MARINA DIAMOND 5 (A), `15642277` | Strong |
| Ready 3BR in Al Furjan under AED 3M | 5 | 5 | EQUITI HOME-A, `15646637` | Strong |
| Furnished 1BR in Business Bay under AED 1.5M | 17 | 9 | Reva Residences, `15687720` | Strong |

The 2026-07-15 release rehearsal verified the production property-search sequence `run_started → agent_step* → properties → sources → guidance → run_completed` for the structured completion contract. Deterministic retrieval, comparison, and evidence audit account for candidate/match counts; model-backed scope classification and structured guidance account for most latency. The final browser gate runs nine Chromium journeys with one worker for deterministic screenshot capture.

## Manual acceptance

- 1440 px desktop, 768 px tablet, and 320 px mobile without page-level horizontal scroll.
- Keyboard-only brief, cards, drawer, navigation, comparison, and dossier.
- Visible focus, Escape close, contained dialog navigation, 44 px touch targets.
- Reduced-motion setting removes animated travel.
- Print preview for one through four homes; links remain visible and clickable.
- Provider outage shows a calm live-run error and never a cached result.
- Three presets return genuine snapshot matches.

The product case study uses numbers from this release record or values derived from the static architecture contract.
