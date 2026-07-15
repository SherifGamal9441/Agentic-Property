# Demo runbook

## Before starting

1. Pull the exact DVC snapshot and run preflight.
2. Start Compose and wait for all four services to report healthy.
3. Warm the selected live model with a non-demo request.
4. Run all three presets once; do not save or replay their answers.
5. Use “Reset showcase” to clear browser-local decisions.

## Demo flow

Start with the Dubai Marina preset and select **Find matching homes** once. The validated brief authorizes the run immediately, while **Edit brief** keeps corrections available without a separate confirmation screen. Let the run trace reach the completion view, then open **View agent trace** to inspect the eight-node flow. Open the best match, compare the top two homes, inspect an unknown value where present, enter an affordability scenario, copy the decision summary, and open print preview. The `#/case-study` route provides a compact view of the architecture.

## Failure recovery

If the provider fails, confirm preflight and retry the validated brief. **Run again** starts a new live request and never replays an earlier answer. If map tiles fail, use the coordinate evidence fallback. Do not replace a live result with saved model output.
