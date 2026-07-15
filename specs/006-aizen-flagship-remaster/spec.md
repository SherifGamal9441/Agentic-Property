# Aizen Flagship Remaster

## Product statement

Aizen is a local-first Dubai home-buying decision product. One search action turns a natural-language request into a validated contract, runs a frozen-snapshot search, scores facts deterministically, audits the evidence, and reveals a private decision workspace.

## Non-negotiable behavior

- React is the only supported product UI; the Streamlit proof of concept is legacy.
- **Find matching homes** is submit-as-confirmation: interpretation must produce a valid `BuyerBrief`, which runs immediately. Raw prompt-only `/api/runs` calls remain invalid.
- All AI responses are live. Provider failure returns a calm error; cached answers are never replayed.
- The eight LangGraph nodes and MCP/data-service boundary remain recognizable.
- Active captured listings are inventory. Historical transactions are context only.
- LLMs interpret and explain; application code filters, scores, audits, and calculates.
- Brief corrections use a disposable **Edit brief** drawer and require **Apply & rerun**. Hard criteria are never relaxed automatically.
- The product fetches and scores 20 candidates, initially reveals six, and exposes the rest on demand.
- Unit size, price per square foot, and dedicated parking are absent until independently verified unit fields exist.
- Browser storage holds anonymous sessions, criteria, shortlist, comparison, statuses, private notes, and affordability assumptions. There are no accounts.
- Property guidance is a validated reference contract; React renders the buyer-readable language from audited property and criterion IDs.

## Experience direction

Editorial Dubai is the reading and decision layer. The dark cinematic research surface transforms in place from a cancellable trace into a prominent completion reveal. Every property receives a deterministic, code-native architectural preview seeded by stable property identity and area. Visuals never change fit, evidence, or ordering.

## Explicit exclusions

No public deployment, Arabic, investor mode, accounts, cross-device sync, paid map, listing photography, CRM, valuation model, financial advice, automatic relaxation, notifications, or scheduled refresh.
