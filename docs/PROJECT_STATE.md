# Project state and handoff

Written 2026-08-06 at the end of a long working session. Read this before your
first task. It exists so you do not spend an hour rediscovering things that took
this session a day to establish — especially the recurring bug class in §4,
which is the single most reusable finding here.

---

## 1. What this is, and the three places it lives

**One substrate serving two ends.** Layer V (`src/layer5_dna_substrate/`) generates
world content from DNA strings. The plan is for it to back two products: a
user-facing co-author app for human GMs, and a subsystem of a larger multi-agent
AI GM. Only Layer V is exercised today.

**The core idea.** DNA is a *constraint scaffold* that forces variety; surrounding
canon supplies *world-fit*; the LLM supplies *novelty*. The same seed under
different context must produce a different, still-valid creation. Genotype
(the DNA string) and phenotype (the decoded page) are deliberately separate.

| Location | What it is | Notes |
| :--- | :--- | :--- |
| `D:\Digital-Narrative-Alchemist-Framework` | The framework. **Public** GitHub repo. | PolyForm Noncommercial 1.0.0. Licence terms are in the README. |
| `C:\Users\nickd\Desktop\World Builder` | The Obsidian vault — the world of **Skarn**. **Private** repo (`Test-World-Bible` remote). | Git plugin auto-commits every 10 minutes. |
| `C:\Users\nickd\Desktop\World Builder App` | A copy of `decoders/` and `generators/` that a separate app loads. | **All 21 decoders are byte-identical to the repo as of `9b00e62`. Keep them that way.** The author edits here sometimes; check both before assuming the repo is current. |

There is also `C:\Users\nickd\Desktop\Test-World-Bible`, a stale clone of the
vault used for an experiment. Ignore it; it is ~15 files behind.

### The registry split — do not undo this

- `data/world_builder_registry.json` — the **live world**, 112 records. **Gitignored.**
  It carried 304 KB of Skarn's prose into a public repo until `ca72784`.
- `data/showcase_registry.json` — a curated 15-entity slice, **tracked**, one per
  generated type. Regenerate with `scripts/export_showcase.py` after editing
  `data/showcase_names.txt`. Scripts default to the showcase so a fresh clone runs.

Untracking did not unpublish: the live registry is still in the history of earlier
commits. The author knows and has accepted this.

---

## 2. Where it was when this session started

- 635 tests passing.
- Decoders were uneven and unaudited. Several were **corrupt** and nobody knew.
- The registry knew 112 of the 165 relationships its own vault implied.
- NPC alignment was mathematically broken (see §3).
- The world's language existed as a decoder but never reached a single prompt.

## 3. Where it is now

**1011 tests passing. 27 commits this session (`fd08582`..`9b00e62`).**

Seven decoders have had a full refinement pass — `npc`, `faction`, `creature`,
`culture`, `lore`, `text`, `item` — each with its own test file. Fourteen have not.

Two rules are now universal across all 21 decoders:
- **No scaffolding below the output template** — no DNA, no field codes, no scores.
- **The axis names are scaffolding too** — "their cohesion is loose" discloses
  exactly what printing `COH:3` would. Labelled template fields are exempt, or
  it would break `creature`'s **Threat** field and `linguistic`'s whole template.

Seven of twenty generators take `seed` and `**pins`: `npc`, `faction`, `creature`,
`culture`, `lore`, `text`, `item`. The other thirteen do not, which blocks the
co-author pattern ("I know this much; invent the rest") for those types.

### The biggest single fix: NPC alignment distribution

The headline LNC/GNE scores were the **rounded mean of 39 trait scores**. Each
trait was a fair 1–9, but averaging twenty of them has a standard error near
0.58. Measured over 20,000 rolls: **35% of NPCs came out exactly (5/5)**, 98% sat
inside the 3×3 Neutral core, only 21–25 of the 81 points ever appeared, and a 1
or a 9 never appeared at all. The 81-point grid was functionally a 5-point one.

Now the band is drawn first and the score picked within it: every alignment
10.7–11.5%, all 81 points reachable. `tests/test_npc_decoder_scale.py` fails all
four of its distribution assertions against the old implementation — verified,
not assumed.

**Every NPC in Skarn predates this fix**, so the existing cast is clustered near
True Neutral regardless of what their pages say. Re-rolling would break canon.

---

## 4. The recurring bug class — read this one

**Every generator emits values meaning "there is no answer", and no decoder
anticipated them.** This was found independently in four decoders and is almost
certainly present in the fourteen unexamined ones.

| Decoder | Rate | Example |
| :--- | :--- | :--- |
| `culture` | **55% of rolls** carry at least one | `AGE:none` sat under *"make this concrete and memorable"* |
| `text` | ~1 in 5 | `FUNC:never-opened` beside a rite that requires opening |
| `creature` | ~1 in 3 | `WKN:none-known` sat under *"ALWAYS give the GM something to work with"* |
| `lore` | 4% carry a contradiction | `PROOF:none-remaining` + `RESOLVE:resolvable` — settleable, with nothing to settle it |

The instruction around the field demanded exactly the content the value denied,
so **inventing an answer was the compliant reading of the prompt.** The fix is
never "don't write it" alone — each absence needs a question that replaces it
(leaderless still means decisions get made, so say *how*).

**When you touch a decoder, audit its generator's vocabularies for null values
first.** It takes one script and finds real bugs every time.

### How to find these

```
scripts pattern used all session (see git history for full versions):
  1. enumerate the generator's module-level vocabularies
  2. flag values matching ^(none|unknown|no-|forgotten|lost|never|does-not)
  3. measure their frequency over 3000+ rolls
  4. grep the decoder for whether each is addressed
  5. check cross-field pairs that can contradict
```

---

## 5. The language pipe (recently built, easy to break)

Skarn's language is **The Sibilant Directive** (`Cultures/`, canon, audit
`consistent`). It is delivered into every decode by `ContextAssembler`:

- Held in its **own `ContextPackage.naming` field**, *not* in `world_frame`.
  It used to live in the frame and was **truncated out of every prompt that ever
  ran**, because the frame is capped to 25% of budget and the World Overview alone
  overflows that. The standing rulings had the identical bug earlier.
- `_fit_language_block()` drops **whole labelled bullets by priority** when over
  budget — taboos kept first, sayings dropped first. A character cap severed the
  last taboo twice; half a taboo is worse than none.
- A **draft** profile steers generation but is kept **out of `canon_slice()`**,
  so unapproved content never becomes the baseline canon pages are audited against.
- The worked example names are labelled illustrative. Without that, a decode
  promoted `Scribe Veris Thal` — an example — into a real historical figure.

**Measured effect:** one DNA string across five worlds produced `Vane`×3 and
`Lyra`×2 before; after the roster and the "vary the opening consonant" rule, the
three treated contexts produced Rulen Silt, Liryn Stitch, Saris Cole — zero
repeats, zero V-initials — while the two untreated controls both produced `Vane`.

---

## 6. What is outstanding

**Undefined vocabularies — only the author can supply these.** Three genomes
emit values nothing documents:
- `faction` — 14 axes (`T`, `G`, `M`, `P`, `S`, `O`, `N`, `L`, `F`, `D`, `A`, `SC`, `MZ`, `X`)
- `quest` — ~40 sub-axis letters inside `GOAL`, `OBS`, `REWARD`, `NARR`, `MOTIV`
- `establishment` — 20 genes with no vocabularies at all

Those decoders currently read their DNA as *shape* (which blocks run high, how
lopsided) rather than meaning. **Do not invent the vocabulary.** A confident guess
is indistinguishable from the real thing in the output and will contradict
whatever gets defined later. `docs/dna_specs/conductor_routing.md` names the tags
and points at decoder files that were never brought into this repo.

**Fourteen decoders have not had the pass:** `agency`, `chronicle`,
`establishment`, `linguistic`, `location`, `quest`, `realm`, `region`,
`regional_poi`, `settlement`, `trap`, `travel`, `wonder`, `world`.

**Thirteen generators lack `seed`/`**pins`.**

**Only 4 of 21 decoders carry the canon-safety rule** (*never resolve a question
the setting leaves open*) — `lore`, `regional_poi`, `text`, `wonder`, plus the
ones added this session. This is the rule protecting the standing ruling that the
First Architects' identity is unresolved. Worth propagating.

### Layer IV: what the three rules cartridges are actually for

They are a **test matrix for the rules abstraction**, not three rulesets the
project needs:

| Cartridge | Role |
| :--- | :--- |
| `coin_flip` | trivial pass/fail — the floor |
| `one_page_5e` | rules-light |
| `PF2EDNA` | detailed — the ceiling |

The requirement they exist to prove is that **the conflict-resolution system can
be changed — between sessions or during one — without destabilising anything
above it.** Layer IV decides outcomes; the narrative agents render them; which
resolver sits underneath is not supposed to be their business.

That requirement had no test coverage and was already broken in two ways, both
in PF2EDNA and both fixed in `d1f0f9c`: it did not define `system_name` (which
`Orchestrator.load_ruleset` reads on every swap, so loading it raised
AttributeError), and its `resolve_action` required a second argument the
orchestrator's call site does not pass (TypeError on the first action after a
successful load). The two lightweight cartridges swapped cleanly; the one that
most needed to demonstrate swappability was the one that broke it.

**A third difference is real and deliberately left alone.** `coin_flip` and
`one_page_5e` accept the player's raw words. PF2EDNA accepts only mapped terms
(`attack_melee`, `save`, `skill_check`) and raises `NotImplementedError`
otherwise, while `Orchestrator.process_player_input` passes raw input straight
through. **Swapping to the detailed ruleset therefore resolves nothing until
something classifies intent first.** `tests/test_cartridge_swap.py` records this
rather than hiding it — a fallback would return a rules result no rule produced.
Building that intent layer is real outstanding work.

**Mythic GME** is a different thing again, and not a rules system. The intent is
an extra random variable running in the background *when no mechanical result is
needed*, forcing the agents to keep inventing rather than settling into their own
defaults — an active "imagination" input to story and content. It is for testing
only until the author builds an equivalent of his own. Note the symmetry worth
preserving: this is the runtime counterpart of what DNA does at generation time.
Both inject constraint precisely to stop the model reaching for its favourite
answer, which is the failure mode this project keeps rediscovering.

**Third-party licensing, arising from the above.** `src/layer4_rules/PF2EDNA/`
ships Paizo rules content with **no ORC or OGL notice anywhere**. The README
disclaims ownership, which is not the same as complying. This is a
*redistribution* question — the cartridge being a test fixture rather than a
product dependency does not change that a public repo carries the content. Mythic
GME (Word Mill Games) raises the same question if it ever ships.

**Sixteen of twenty-one decoders have no worked example.** Deliberate — an
example roughly doubles a decoder's size and therefore every prompt built from it.

---

## 7. How to work here

**Measure before asserting.** Every significant finding this session came from
running a script, not from reading. Several confident readings turned out wrong
under measurement, in both directions.

**Keyword probes are unreliable for judging prose.** They are good for finding
leaks (exact tokens) and bad for deciding whether an instruction was followed. At
least three times this session a probe reported a failure that turned out to be
the model using a different word ("incinerated" where the probe wanted
"destroyed"). **Confirm by reading the passage.**

**Verify a regression test actually fails on the regression.** The alignment
distribution test was run against the old implementation to prove it catches the
bug. An unverified guard is not a guard.

**A decoder is a prompt: its text IS its implementation.** Tests assert its
documentation. Assert *properties*, not sentences — eleven tests broke when the
author reworded a section better than the original, because they pinned phrasing.

**Live-decode to verify.** Decoder changes were checked by running real decodes
against the vault. This found defects the tests could not: palette labels printed
as output headers, field names laundered into prose ("their reproduction score is
zero"), and example names promoted to characters.

### Canon model — enforced, not requested

Everything generated arrives as `draft`. **Only the author promotes to canon.**
`ObsidianSync.PROTECTED_STATUSES` refuses to overwrite a canon page; the gate
audits canon but never patches it; `retype_element` refuses canonized entities.
The vault's `CLAUDE.md` defines operations (`create`, `expand`, `canonize`,
`query`, `lint`) — **there is no defined operation for amending a canon page**,
which came up and was handled ad hoc.

### Cost and quota — the author has raised this repeatedly

Model calls come out of the author's budget. Two subagent batches died mid-run on
session limits this session. **Ask before dispatching parallel subagents or
running anything that decodes in bulk.** A `GOOGLE_API_KEY` in `.env` drives the
decode pipeline (Gemini 2.5 Flash, free tier) — that is the cheap path.
`scripts/canonize_gate.py` re-audits everything not marked `consistent`,
`patched` or `composed`; check the pending count before running it.

### Environment

Windows. Use `.\venv\Scripts\python.exe`, never bare `python` (which is a
different interpreter without the deps). Piped stdout is cp1252, so non-ASCII
crashes — `common/console.enable_safe_stdout()` exists for this and every script
entry point calls it.

The vault has a `.graphifyignore` excluding `.obsidian/`, `.claude/`,
`Templates/`, `Log.md` and `graphify-out/`. Three separate attempts at graphing
that vault independently concluded the machinery has to come out first; without
it, ~15% of the graph is Obsidian plugin manifests and three of them outrank most
of the world by degree.
