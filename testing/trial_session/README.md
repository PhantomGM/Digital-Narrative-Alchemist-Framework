# DNA Trial Session Harness

This folder is a tiny, manual-first testing harness for the Digital-Narrative-Alchemist-Framework.

## What it is for
Use this to run a small fixed set of prompts through the current DNA pipeline and save the outputs for comparison.

## Files
- `sample_world_state.json` — fixed world state for the trial
- `sample_player_state.json` — fixed player state for the trial
- `test_prompts.json` — 5 starter prompts
- `score_sheet.md` — manual pass/fail rubric
- `manual_trial_workflow.md` — the testing ritual
- `runner_template.py` — now wired to the repo's real SessionDirector pipeline
- `output_logs/` — where each run writes markdown logs

## How to run it
From the repo root:

```bash
python testing/trial_session/runner_template.py --dry-run
python testing/trial_session/runner_template.py --test-id T1
python testing/trial_session/runner_template.py
```

## Recommended order
1. Run `--dry-run` once to confirm logs are being written where you expect.
2. Run one real test, like `--test-id T1`.
3. Review the generated markdown log in `output_logs/`.
4. Score the result in `score_sheet.md`.
5. Run all 5 prompts only after the first test behaves roughly as expected.

## Important note
This is intentionally small and imperfect.
You are not trying to prove the full framework works yet.
You are only trying to create a repeatable loop:
- run fixed prompts
- save outputs
- score them
- fix the biggest recurring failures
