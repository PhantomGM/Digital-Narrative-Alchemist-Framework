# Session 0 trial

A full end-to-end run of the campaign-genesis pipeline: four simulated players
interviewed, a contract derived from what they said, fifteen entities generated
for real through the DNA substrate, a campaign pitch assembled from them, and the
pitch put back to the table. All four accepted.

**This is committed including its flaws, deliberately.** The generated pages are
the actual unedited output. Where the design failed, `03_findings.md` says so and
names the mechanism. A trial that only recorded its successes would not be worth
keeping.

## Reading order

| File | What it is |
| :--- | :--- |
| `player_profiles.json` | The four players, structured. Lines and Veils held apart — see the note at the top, it is a finding in itself. |
| `01_round1_transcript.md` | What the players said, unedited, before anyone saw anyone else's answers. |
| `02_campaign_pitch.md` | The pitch, assembled from the generated entities. Every name in it came out of the pipeline. |
| `03_findings.md` | **Start here if you only read one.** What worked, what broke, and the measurement that changed the project's termination model. |
| `pages/` | The fifteen decoded entities, as generated. |
| `registry.json` | The trial world's registry. Not connected to the live world. |
| `generate_world.py` | The harness. Re-runnable; `--dry-run` makes no model calls. |

## The headline result

Stub fan-out on a **new** world is **3.67** implied entities per generated entity.
On the mature live world it is **0.97**. The project's existing conclusion — that
generation terminates on its own — turns out to hold only once a world is
populated enough for name-deduplication to bite. On a fresh world, nothing bounds
it but the contract. See `docs/PROJECT_STATE.md` §8.

## Running it again

```bash
.\venv\Scripts\python.exe testing/session_zero/generate_world.py --dry-run
```

Decoding needs `GOOGLE_API_KEY` in `.env`. A full run is 15 decodes and took
about seven minutes on the free tier. It writes only inside this folder.
