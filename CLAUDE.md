# Working in this repository

## Read this first

**Before your first task, read [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).**

It is a handoff document: what this project is, where it stands, the two
recurring bug classes — one found in four separate decoders and probably in the
rest, one found three times in the type-registration path — and the working
practices that produced the current state. It will save you an hour of
rediscovery and stop you repeating fixes that are already in.

Do that before proposing work, not after.

## The short version

A DNA substrate for procedural worldbuilding. Python generators emit DNA strings;
markdown files in `src/layer5_dna_substrate/decoders/` are prompts that render
them into prose. DNA forces variety, surrounding canon supplies world-fit, the
model supplies novelty.

Three things that bite immediately if you do not know them:

- **`.\venv\Scripts\python.exe`**, never bare `python` — the latter is a
  different interpreter without the dependencies.
- **`data/world_builder_registry.json` is gitignored on purpose.** It is the live
  world and this repo is public. `data/showcase_registry.json` is the tracked
  slice; scripts default to it.
- **The decoders exist in two places.** `src/layer5_dna_substrate/decoders/` and
  `C:\Users\nickd\Desktop\World Builder App\decoders\`. They are currently
  byte-identical. The author edits either. Check both before assuming.

## Ground rules

**Model calls cost the author money and have hit session limits twice.** Ask
before dispatching parallel subagents or running anything that decodes in bulk.

**Only the author promotes content to canon.** Generated pages arrive as `draft`.
This is enforced in code, not merely requested — do not work around it.

**Measure before asserting.** Claims about distributions, frequencies or whether
a prompt is being followed should come from a script that was run, not from
reading. This has repeatedly overturned confident readings in both directions.

**Do not invent an undefined vocabulary.** Several genomes emit axis codes nothing
documents. Read them as shape; leave the meaning to the author. A plausible guess
is indistinguishable from the real thing in the output and poisons everything
generated afterwards.

**Keep `docs/PROJECT_STATE.md` current — you do not need to ask.** When a
decision is made, a milestone lands, a measurement overturns something the
document asserts, or you learn something the next agent would otherwise spend an
hour rediscovering, write it in as part of the work rather than mentioning it
afterwards. Correct the numbers it states rather than appending a note beside
them: it is a state document, not a changelog, and it is only worth reading first
if it is true. Git already holds the history.
