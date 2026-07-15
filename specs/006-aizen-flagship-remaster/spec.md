# Aizen Flagship Remaster

## Product statement

Aizen is a local-first Dubai home-buying decision product. It turns a natural-language request into an editable, buyer-confirmed contract, searches one frozen listing snapshot, scores facts deterministically, audits the evidence, and produces a private printable dossier.

## Non-negotiable behavior

- React is the only supported product UI; the Streamlit proof of concept is legacy.
- Property runs require a confirmed `BuyerBrief`. Raw prompt-only runs are invalid.
- All AI responses are live. Provider failure returns a calm error; cached answers are never replayed.
- The eight LangGraph nodes and MCP/data-service boundary remain recognizable.
- Active captured listings are inventory. Historical transactions are context only.
- LLMs interpret and explain; application code filters, scores, audits, and calculates.
- Hard criteria are never relaxed without buyer confirmation.
- The product fetches and scores 20 candidates, initially reveals six, and exposes the rest on demand.
- Unit size, price per square foot, and dedicated parking are absent until independently verified unit fields exist.
- Browser storage holds anonymous sessions, criteria, shortlist, comparison, statuses, private notes, and affordability assumptions. There are no accounts.

## Experience direction

Editorial Dubai is the reading and decision layer. Dark cinematic surfaces are reserved for confidence moments: hero emphasis, live trace, map evidence, and the comparison tray. Visuals are abstract architecture and maps; listing photography is never fabricated.

## Explicit exclusions

No public deployment, Arabic, investor mode, accounts, cross-device sync, paid map, thumbnails, CRM, valuation model, financial advice, automatic relaxation, notifications, or scheduled refresh.
