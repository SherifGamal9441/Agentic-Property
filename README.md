# Aizen

**Find what fits. See what matters.**<br />
*Search less. Decide better.*

Aizen is a Dubai home-buying decision workspace. Describe a home once, watch a live eight-node investigation, and move from a clear brief to an evidence-ranked shortlist, comparison matrix, affordability scenario, and printable buyer dossier.

![Aizen flagship buyer workspace](docs/assets/aizen-home.png)

## The 60-second demo

1. Choose a live preset or describe a home in your own words.
2. Select **Find matching homes**; Aizen interprets and immediately runs the validated brief.
3. Meet the completion takeover, review its evidence metrics, and open the leading home's profile.
4. Edit and rerun the compact brief, compare up to four homes, enter an affordability scenario, and print the buyer dossier.

## Why it is technically credible

- A validated `BuyerBrief` turns natural language into editable criteria before search execution; submit authorizes the first run and later edits require **Apply & rerun**.
- `PropertyGuidance` references audited properties and criteria instead of trusting free-form factual prose.
- MCP isolates listing retrieval behind typed filters and preserves provider flexibility.
- Deterministic code—not an LLM—evaluates criteria, weights fit, and audits invariants.
- Active listing evidence and historical transaction context never substitute for one another.
- PostgreSQL is primary; SQLite keeps the local demo resilient when PostgreSQL is unavailable.
- React loads the OpenFreeMap/MapLibre location surface only when requested.
- Every shown property exposes its source reference, observation date, data-snapshot identity, matched criteria, and evidence coverage.
- Warm editorial surfaces carry reading and decision work. Dark cinematic surfaces mark research and evidence moments. Abstract architectural geometry gives every home a distinct visual identity without implying listing photography.
- Property visuals are deterministic editorial architecture generated from each property's stable identity; no listing photography is implied.

```mermaid
flowchart TD
  START([START]) --> memory[memory<br/>Restore session]
  memory --> query_relevancy[query_relevancy<br/>Dubai property scope]
  query_relevancy -- property scope --> query_understanding[query_understanding<br/>Validate BuyerBrief]
  query_relevancy -- outside scope --> END1([END])
  query_understanding -- property_search --> query_routing[query_routing<br/>Choose listing path]
  query_understanding -- web_research --> web_search[web_search<br/>Cited research]
  query_routing -- candidates found --> comparison_engine[comparison_engine<br/>Deterministic fit]
  query_routing -- no candidates --> answer_generation[answer_generation<br/>Buyer guidance]
  comparison_engine --> reflection[reflection<br/>Evidence audit]
  reflection --> answer_generation
  web_search --> answer_generation
  answer_generation --> END2([END])
```

| Node | Responsibility |
| --- | --- |
| `memory` | Restores bounded, thread-isolated session context |
| `query_relevancy` | Validates Dubai property scope |
| `query_understanding` | Normalizes the confirmed `BuyerBrief` |
| `query_routing` | Maps supported hard criteria to MCP filters |
| `web_search` | Handles laws, areas, and general market questions with citations |
| `comparison_engine` | Evaluates, weights, and orders candidates locally |
| `reflection` | Checks IDs, hard rules, arithmetic, sources, and snapshot identity |
| `answer_generation` | Turns audited references into concise guidance |

## Browser-to-data architecture

```mermaid
flowchart LR
  browser[React buyer workspace] <-->|SSE + JSON| api[FastAPI agent API]
  api --> graph[LangGraph eight-node workflow]
  graph --> mcp[Persistent MCP client]
  mcp --> server[MCP listing server]
  server --> data[FastAPI data service]
  data --> pg[(PostgreSQL primary)]
  data -. service fallback .-> sqlite[(SQLite)]
  data --> snapshot[DVC data snapshot]
  browser --> local[(Browser-local briefs, shortlist, notes, scenarios)]
  graph -. historical context .-> data
```

The browser owns presentation and private workspace state. The agent API owns validation and SSE. The graph owns routing. MCP is the typed boundary for property retrieval. The data service owns database selection and snapshot identity.

## Data and evidence

The schema-v2 data snapshot contains **3,087 captured active listings** and **28,809 historical transaction rows**, collected through the existing project source pipeline on **2026-07-02**. DVC pointers, checksums, field definitions, and validation results are documented in [data provenance](docs/data-provenance.md).

The product keeps property-level and building-level fields distinct. Historical context uses robust reported-price distributions, sample size, period, and property mix; it is presented as an orientation lens for the buyer workspace.

## One-command local startup

Prerequisites: Docker Desktop, Git, DVC access to the configured remote, and one configured live LLM provider.

```powershell
Copy-Item .env.example .env
# Edit .env for exactly one provider.
uv sync
uv run dvc pull
uv run python scripts/preflight.py
docker compose up --build -d
```

Open [http://localhost:5173](http://localhost:5173) and walk through any preset with the configured live provider.

## Preset recruiter scenarios

- Ready 2BR in Dubai Marina under AED 2M, no off-plan.
- Ready 3BR in Al Furjan under AED 3M.
- Furnished 1BR in Business Bay under AED 1.5M.

Presets populate the query, then the same one-action path interprets and runs the complete live agent.

## Verification

```powershell
uv run pytest -q
Push-Location frontend
npm run test:gate
npm run build
npm run test:e2e
Pop-Location
docker compose config --quiet
git diff --check
```

The release record, accessibility checks, mobile checks, print checks, and current verified counts live in [evaluation](docs/evaluation.md). The in-product `#/case-study` route presents the same engineering story for a recruiter walkthrough.

## Documentation

- [Architecture](docs/architecture.md)
- [Data provenance](docs/data-provenance.md)
- [Scoring and evidence](docs/scoring-and-evidence.md)
- [Evaluation](docs/evaluation.md)
- [Demo runbook](docs/demo-runbook.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Design system](docs/design-system.md)
- [Active specification](specs/006-aizen-flagship-remaster/spec.md)
- [Architecture decisions](docs/decisions/)

## License

MIT — see [LICENSE](LICENSE).
