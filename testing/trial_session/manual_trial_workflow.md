# Manual Trial Workflow

This is your first real testing ritual for the DNA repo.

## Goal
Run the same 5 prompts through one fixed process and compare outputs over time.

## Minimal pipeline
1. Load `sample_world_state.json`
2. Load `sample_player_state.json`
3. Pick one test from `test_prompts.json`
4. Run it through the current SessionDirector-based pipeline
5. Save the raw output in `output_logs/`
6. Score it in `score_sheet.md`

## Commands
From the repo root:

```bash
python testing/trial_session/runner_template.py --dry-run
python testing/trial_session/runner_template.py --test-id T1
python testing/trial_session/runner_template.py
```

## Suggested fixed process
For each prompt:
- classify the request as IC / OOC / Mixed
- pass it through the current orchestrator / session-director stack
- save:
  - input
  - expectations
  - trial notes / world facts
  - final response
  - quick score placeholders

## Logging convention
Each run creates a file like:
- `output_logs/T1_20260410T000000Z.md`

## What counts as success
You are successful if:
- you can run all 5 prompts through the same rough pipeline
- you can save the outputs
- you can compare results after changes

That is enough to count as a real test harness.

## What to do after the first run
1. Review the generated logs.
2. Fill out `score_sheet.md`.
3. Identify the top 3 recurring failures.
4. Fix only those first.
5. Re-run the same prompts and compare.
