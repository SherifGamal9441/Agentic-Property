# Quickstart Validation: Premium Buyer Polish

## Prerequisites

- Run the existing Docker Compose stack, or use the frontend test fixture data.
- Use a browser with local storage enabled for saved-research checks.

## Validation scenarios

1. Open a property from a card and from its map pin. Add it to shortlist and comparison; verify labels update on the card, drawer, map, and tray.
2. Add four homes to comparison, attempt a fifth, and verify the original four remain selected with a clear notice.
3. Use all-results, shortlist, and comparison map scopes with overlapping and missing-coordinate listings. Verify exact groups are selectable and area-only language remains honest.
4. Save a brief with criteria and shortlist, refresh the page, and restore it. Simulate a newer snapshot and verify added, removed, and unchanged states are distinguishable.
5. Review empty, researching, results, drawer, and decision-sheet states at desktop and narrow mobile widths; verify no horizontal overflow and keyboard access to overlay controls.

## Commands

```powershell
Set-Location frontend
npm run test:gate
npm run build
Set-Location ..
uv run pytest -q
docker compose config --quiet
```
