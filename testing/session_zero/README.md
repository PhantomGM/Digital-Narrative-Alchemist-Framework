# Session 0 trials

Six runs of the campaign-genesis pipeline: simulated players interviewed, a
contract derived from what they said, a world generated for real through the DNA
substrate, and — twice — a pitch put back to the table and accepted.

They exist to find defects that unit tests cannot, and they have. **Every trial
found something no test in this repo would have caught**, and most of the
machinery listed below was written because a trial demanded it.

**Committed including the flaws, deliberately.** The generated pages are the
actual unedited output. Where the design failed, the write-ups say so and name the
mechanism. A trial that only recorded its successes would not be worth keeping —
and the most useful single artifact here is a zero-byte page that the pipeline
reported as a success.

---

## Start here

[`index.md`](index.md) lists every file with a one-line description. If you want
one document, read [`03_findings.md`](03_findings.md) (trial 1) and then
[`11_trial6_naming.md`](11_trial6_naming.md) (the most recent).

## The six trials

| | What it varied | What it found |
| :--- | :--- | :--- |
| **1** | — (first run) | Seven defects. Branching factor **3.67** on a new world against 0.97 on the mature one, which corrected the project's whole termination model. |
| **2** | Same transcripts, *built* machinery instead of scaffolding | Five of five defects fixed. And the negative result that matters: **a contract bounds what is generated, not what is implied** — branching was unchanged at 3.81. |
| **3** | Fresh interview, same profiles | Safety findings reproduce; creative findings do not. **A safety register can be cached per group; a contract cannot.** |
| **4** | The same interview with three leading hints deleted | One finding reproduced unprompted, one **reversed**, one vanished. For safety, **the hint is the instrument, not the bias.** |
| **5** | Full pipeline — contract, safety, expansion policy, ghosts | A `culture` decode returned **nothing** while the pipeline reported `contract satisfied: True`. All four players accepted the pitch, then found three defects no probe could. |
| **6** | `naming` and `roster` finally wired | The first world whose names obey its own language. **Zero model-default names in seventeen pages.** |

## What these trials caused

Nearly all of this was written in response to a trial, not in anticipation of one.

| Code | Because |
| :--- | :--- |
| `src/layer5_dna_substrate/content_contract.py` | Trial 1: a count says how many, never which. Briefs, a dependency graph, tonal slots, and a stop condition. |
| `src/layer3_operations/safety_register.py`, plus `ContextPackage.safety` | Trial 1: one player's Line bound the *setting*, which an output filter structurally cannot catch. |
| `src/layer5_dna_substrate/expansion_policy.py` | Trial 2: the contract does not bound implication. EXPAND / COMPOSE / GHOST / DEFER. |
| `src/layer5_dna_substrate/ghost_registry.py` | Trial 5: on a fresh world nothing is canonized, so the compose tier answers nothing and everything defers. |
| Guards in `src/layer5_dna_substrate/decoder.py` | Trial 5: an empty decode, then a decode returning **1.8 MB of trailing whitespace** with half the profile missing. |
| The Lever section in `src/layer5_dna_substrate/decoders/npc.md` | Core Vulnerability was restating the alignment on 3 of 3 sampled characters. |
| Title fixes across five decoders | They opened their pages with a template label instead of a name. |
| `naming` + `roster` wiring in both harnesses | Trial 6: five trials generated a language and discarded it. |

## Headline results

**Branching.** A new world implies **3.67** entities per entity made; the mature
live world implies 0.97. Termination was never automatic — it depended on
name-deduplication, which needs a populated registry to bite. Later trials measured
3.81, 2.88 and 2.71, so three points now trend downward and three points is still
three points. See `docs/PROJECT_STATE.md` §8.

**Safety.** Asked directly rather than hinted, **all four players said they would
not raise a boundary out loud** — including the ten-year veteran who had
volunteered the opposite twice. The table-wide "just say it" norm is endorsed by
nobody and relied on by everybody's GM.

**Naming.** Trial 5's crew were Kaelen Vance, Sariel Finch and Bess Marrow. Trial
6's are **Brak-Tally, Vex-Seam and Tor-Vane**, its places carry sector numbers and
its factions take `Line` or `Guild` — because the language the world invented
finally reached the prompts that came after it.

## Running them

```bash
.\venv\Scripts\python.exe testing/session_zero/generate_trial5.py --dry-run --out testing/session_zero/pages_trial7
```

`generate_trial5.py` is the current harness — its own contract, and the only one
that advances the frontier through `ExpansionPolicy` and `GhostRegistry`.
`generate_world.py` is the trials 1–2 harness, kept because those pages are the
evidence for the defects trial 2 fixed. Both take `--out`; the registry and index
follow it, so a new run cannot overwrite an old one.

`--dry-run` makes **no model calls** and prints the contract, its resolved order
and the safety register. `compare_trials.py` re-runs the trial 1 versus trial 2
comparison defect by defect and also makes no model calls.

Decoding needs `GOOGLE_API_KEY` in `.env`. A full 17-entity run is about 20–25
minutes on the free tier now that `naming` and `roster` are in every prompt —
roughly double what it cost before. Everything writes inside this folder; nothing
touches `data/world_builder_registry.json`.

## Known and deliberate

- **One verbatim example-name reuse in sixteen** (trial 6's station is named after
  an illustrative example). Reduced from 1-in-1, not eliminated.
- **Trial 6's names are all hyphenated compounds.** That monotony came from the
  language rather than its application — `linguistic` gave one construction to all
  three name classes. **Since fixed**: the decoder now requires a different
  construction per class and carries a test for it, so a re-run should give people,
  places and institutions three distinguishable shapes. Trial 6's pages predate
  that and are left as they are.
- **Trial 1's pages are left exactly as generated**, template-label leaks and all.
  They are the evidence.
