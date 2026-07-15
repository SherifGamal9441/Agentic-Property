# Quickstart Validation: Buyer Research Remaster

## Prerequisites

- Services configured as documented in the repository root.
- Historical data seeded and agent API reachable.

## Validation flows

1. Run a buyer brief, then a follow-up. Confirm the workspace timeline shows both prompts and answers.
2. Refresh the page, reopen the current research session, and verify prior messages return. Start a new conversation and verify it is distinct.
3. Select one to four active properties and open the decision sheet. Confirm each property shows historical evidence or an explicit unavailable message, matching basis, and historical label.
4. Enter transfer, finance, moving, and annual service values. Confirm purchase total is per property and annual service is separate; blank remains not entered.
5. Mark properties saved, maybe, and ruled out; add a note; refresh and verify state remains in the same browser.
6. At desktop, 320px width, keyboard-only navigation, and print preview, verify clear action hierarchy, focus visibility, no horizontal page overflow, and evidence labels.

## Automated checks

```powershell
pytest tests/agent_api/test_app.py tests/data_service/test_app.py
Push-Location frontend; npm run test:gate; npm run build; Pop-Location
```

Expected result: new transcript, market-context, buyer-state, and responsive decision-sheet tests pass with the maintained project suites.
