# UI State Contract

## Property actions

| Action | Preconditions | Result |
|---|---|---|
| Add/remove shortlist | Selected property exists | Shortlist membership changes and all visible surfaces reflect it |
| Add/remove comparison | Selected property exists; add has fewer than four selections | Comparison membership changes; fifth add keeps existing set and shows a limit notice |
| Reset research | Buyer activates explicit reset | Only the selected research state is cleared; confirmation is shown |

## Map scopes

| Scope | Visible emphasis |
|---|---|
| All results | All result-set locations |
| Shortlist | Locations of shortlisted results |
| Comparison | Locations of compared results |

If a scope has no exact coordinates, the map retains its context and states why no precise pin is available.

## Location confidence

| Source state | Buyer-facing meaning |
|---|---|
| Valid exact coordinate | Relative pin based on supplied coordinates |
| No valid coordinate with area | Area-only location evidence |
| No usable location data | Location unavailable |
