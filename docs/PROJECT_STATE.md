# Project state and handoff

Written 2026-08-06 at the end of a long working session, and kept current since
by whoever is working here. Read it before your first task. It exists so you do
not spend an hour rediscovering things that took a day to establish — especially
the two recurring bug classes in §4, which are the most reusable findings here,
and the measured branching factor in §8, which is what the whole termination
design rests on.

**Correct it as you go.** CLAUDE.md makes this standing permission: change the
numbers rather than annotating them. Git holds the history.

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

## 2. Where it was before the 2026-08-06 session

- 635 tests passing.
- Decoders were uneven and unaudited. Several were **corrupt** and nobody knew.
- The registry knew 112 of the 165 relationships its own vault implied.
- NPC alignment was mathematically broken (see §3).
- The world's language existed as a decoder but never reached a single prompt.

## 3. Where it is now

**1157 tests passing.** The 2026-08-06 session took it from 635 to 1011 across 27
commits (`fd08582`..`9b00e62`). The session after it fixed the stub-routing hole
(§4b, `72ccdde`) and settled the generation-budget model (§8).

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

## 4. Two recurring bug classes — read this section

### 4a. Null values nothing anticipates

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

### 4b. Types the registration path cannot name

**`_resolve_stub_type` falls back to `"npc"` for any label it does not
recognise.** A type missing from `VALID_STUB_TYPES` or `FUZZY_TYPE_MAP` is not
merely unroutable: every stub naming it is silently registered as a person and
filed under Characters. Nothing raises, nothing warns, and the page looks fine.

Found three times. Creatures became NPCs. Then traps became NPCs. Then, in
`72ccdde`, six types at once — `agency`, `establishment`, `realm`,
`regional_poi`, `travel` and `wonder`, each with a generator, a decoder and a
folder in `TYPE_FOLDER_MAP`, none of them nameable. Measured cost: **the live
world holds 112 records and not one entity of any of the six.** A type nobody can
name does not error, it just never exists.

The cause was upstream of the map both times. `TAIL_INSTRUCTION` offered decoders
ten legal types while `VALID_STUB_TYPES` had grown to fifteen, so decoders were
never told `creature`, `culture`, `lore`, `text` or `trap` existed and reached for
an unlisted word instead. **That list is now derived from the set**, sorted for
stability across processes, so the drift is no longer expressible.

Two properties of `FUZZY_TYPE_MAP` worth knowing before you touch it:

- **Matching is substring-in-insertion-order.** New keys appended at the end can
  only capture labels that previously fell through to the `npc` default, so
  appending is safe and interleaving is not. Three collisions were closed when the
  keys were written: `shop` is inside *bishop*, `port` inside *portal*, `nation`
  inside *abomination*. `cult` must stay below the culture block, or the substring
  test routes every people in the world to `faction`.
- **An earlier key silently kills a later one.** `logbook` sat in the map for
  months and could never fire, because `book` appears earlier and claims it for
  `item`. `test_fuzzy_keys_do_not_shadow_a_later_key_of_another_type` walks the map
  in its real order and found it on the first run.

`tests/test_stub_type_coverage.py` derives its expectations from
`ProceduralForge.generators` rather than listing types, so **a twenty-second type
fails it until it is wired into all four places** — generator, decoder,
`VALID_STUB_TYPES`, `TYPE_FOLDER_MAP`. That file exists to stop the fourth
instance, not to record the third.

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

**Eight types have never produced an entity.** `agency`, `establishment`,
`realm`, `regional_poi`, `travel`, `wonder`, `trap` and `quest` all have a
generator, a decoder and a folder, and the live world contains none of them. Six
of the eight were unreachable until `72ccdde` (§4b); they are reachable now but
still unexercised, so their decoders have never been run against real canon.
Expect the §4a null-value bugs to be sitting in all of them.

**`establishment` has no vocabularies at all** — twenty genes, integer ranges
only, most of its decoder table marked `INFERRED`. The author's "Generative
Capabilities" list maps closely onto those genes (atmospheres, tiered menus,
services, legality, shopkeeper profiles, backroom stock) and is a candidate
source, but it is a **proposal awaiting ratification**, not a defined vocabulary.
Do not read it as one.

**Lines and Veils have no home in `ContextPackage`.** See §8 — this is the piece
where getting the shape wrong later means regenerating content rather than adding
to it.

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

---

## 8. When generation stops

The question this answers: with an AI agent doing canonization instead of the
author, what stops a new world generating forever? Every decoder asks for 2–4
Unmade Connections, and `expand_stub` recursively parses the entity it just made,
so on paper this is an unbounded tree.

### What the live world actually does

Measured over all 112 records:

| | |
| :--- | :--- |
| Made entities / pending stubs | 70 / 42 |
| Of the 70 made, once a stub | 26 |
| Mentions per made entity | **3.81** (matches the "2–4" instruction) |
| New stubs per made entity | **0.97** ← the branching factor |
| Mentions that deduped onto an existing entity | **75%** |
| Near-duplicate names dedupe missed | **0** |
| Pending stubs needing no generation at all | **17 of 42 (40%)** |

**Mean offspring below 1 is a sub-critical branching process — it terminates with
probability 1.** The brake is `_register_stub`'s `find_by_name` dedupe: three
quarters of everything a page mentions turns out to already exist.

### That result holds only for a MATURE world

Measured 2026-08-06 on a new world generated from a Session 0 contract
(`testing/session_zero/`, 15 entities decoded for real):

| World | Stubs implied per made entity |
| :--- | :--- |
| Skarn — 112 records, mature | **0.97** — sub-critical, terminates |
| The Hollow Assay — 15 entities, new | **3.67** — super-critical |

The brake needs a populated registry to bite. **A new world has nothing to dedupe
against**, so it branches at very nearly the rate the decoders are asked for (2–4
Unmade Connections each). Fifteen entities implied fifty-five stubs.

So the reassuring reading of the 0.97 is wrong where it matters most. **The
runaway case is precisely the new-world case an AI canonizer is meant to handle**,
and on a fresh world the contract is not a refinement — it is the only thing
between Session 0 and unbounded generation.

Two facts that make laziness safe and cheap:

- **Registration is free; only expansion costs.** `parse_and_register_stubs`
  makes a registry row and no model call. The 42 pending stubs are the frontier
  working as designed.
- **Stubs cannot leak into a prompt.** `context_assembler.py:314` excludes them
  from the retrieval pool, so an unexpanded stub can never be described into
  existence by a decoder.
- **`CanonComposer` answers 40% of the frontier for nothing.** `triage_all()`
  runs with zero model calls and found 17 stubs that canon already describes
  richly enough to compose a page from. **Triage before spending an expansion
  budget.**

### The decided model: generate against a deliverable, not against a world

World completeness is unreachable and therefore useless as a stop condition. Each
phase instead terminates when its *consumer* is satisfied:

| Phase | Bounded by | Done when |
| :--- | :--- | :--- |
| Session 0 | the contract | the player profile has answers |
| Core entities | the pitch | no empty slots |
| Pitch | the players | accepted |
| Character backstories | the players | accepted |
| World fill | the backstories | every referent resolves |
| First session outline | session one | it has openings, not a script |

**Session 0 sets the quota, it does not merely tint the tone.** Genre changes
which types matter at all: political intrigue wants factions, NPCs, agencies and
texts and roughly zero creatures; a hexcrawl inverts that. A fixed count is the
worst case for every specific game. A rough generic contract is ~11 entities
(1 each world/region/settlement/culture/linguistic/lore/quest, 2 factions,
3 NPCs) — the live world holds 70 made, six times a pitch's worth, and 10 `item`
records where a pitch needs none.

**Confirmed in trial, with three corrections.** `testing/session_zero/` ran this
end to end — four player-agents, a real interview, 15 entities decoded, a pitch
accepted by all four. Full write-up in `03_findings.md`. What it changed:

- **A type-and-count quota is not a contract.** Per-slot briefs must reach the
  prompt. The one `regional_poi` briefed only as "the mine" generated a
  dimensional arch on a plateau; adding the brief fixed it with the same genome.
- **The contract is a graph, not a list.** `linguistic` was generated after the
  settlement, so **the town was named before the naming rules existed**, and the
  POI was generated before the factions so it invented its own rival groups.
- **A quota cannot express tone.** Warmth was requested in Session 0 and present
  in the agreements block; every entity still came out grim, and the player who
  asked for it said so. Faction, NPC, creature and lore genomes all trend to
  conflict, and no type-and-count contract can ask for a place to have a meal.

Two further findings worth carrying: the interview raised factions from the
generic 2 to 3 **and specified their kinds**, which is the quota-shaping
hypothesis confirmed; and some Session 0 output shapes *runtime GM behaviour*
rather than the world (give faction X equal stage time; recognise this player
socially rather than mechanically; this player's silence is not a distress
signal). The contract holds none of that and needs a sibling that does.

**World fill is the one phase with no natural edge**, since a backstory can imply
arbitrarily much. Bound it structurally: expand depth 1 from each backstory
referent and register everything below as stubs.

### Prep, and what happens to the parts play never touches

Session outlines are contingency plans, not scripts; players will not follow
them. The distinction that matters is **fact versus forecast**, not used versus
unused:

- **Entities are facts.** A generated NPC, monster or location was true the
  moment it was made. Players not showing up does not unmake it. These canonize
  on the normal `draft` path — no special status.
- **Forecasts are predictions.** "The party confronts her in the crypt" did not
  happen. But something else did: **an unwitnessed forecast resolves rather than
  being deleted.** At session end each one is *witnessed*, *unwitnessed and due*
  (resolves off-screen, becomes new canon), or *still pending* (clock advances,
  carries into the next outline).

This is what stops the quantum ogre. **Prep is entities with a location and a
clock, not scenes waiting for a trigger.** The troll is in the eastern pass; take
the north road and the troll is still in the eastern pass, and next week a caravan
does not arrive. A scene held in reserve floats and lands wherever the players go,
which makes choice decoration.

**The fallback outcome must be written when the forecast is**, not improvised at
session end — generated after the fact it will rationalise whatever the players
did, which is the same failure in a different hat.

Off-screen resolution is bounded by writing **a dated line, not a page**.
`TimelineComposer` already consumes an `events` list (`date_label`, `event`,
`era`, `sources`) off any registry record, is a deriver, and calls no model. So
"the Rite completed unopposed" is one event on that entity's record: canon, in the
chronology, constraining everything generated afterwards, free. It becomes a page
only when play demands the detail.

### Lines and Veils are not preferences

Genre *steers* generation; a Line *prohibits* content, and `ContextAssembler`
treats steering as droppable — `_LAYER_BUDGET` caps `world_frame` at 25%, and
that is precisely how the naming rules were truncated out of every prompt that
ever ran (§5). **A Line that gets truncated is a safety failure, not a quality
regression.**

Worse, `canon_slice()` calls `_sections(include_directives=False)`, so the
auditor never sees `directives`. A Line placed there would steer generation and
never be verified, and a prompt instruction is not a guarantee.

So Lines and Veils need **their own `ContextPackage` field**, exactly as `naming`
got: present in both `for_decoder()` and `canon_slice()`, emitted first, never
budget-dropped, and given the `_fit_language_block` treatment if it must ever
shrink — whole items dropped by priority, never one severed mid-sentence. Two
further constraints from how the tool is used at real tables: veils are often
**private**, which argues for enforcement at audit time rather than a prompt that
recites the constraint back where the table can read it; and they are **added
mid-campaign**, so the profile must be amendable at any session rather than frozen
at Session 0.

**The trial proved this twice, in both directions.** A player's bigotry Line
turned out to bind the *setting* — "even if no one's PC ever encounters it
directly" — which `SafetyGovernor` structurally cannot enforce, because a culture
page carrying it reads fine in isolation. Carried into the prompt instead, it
held. And a claustrophobia Veil **collided with the premise itself**: a mine
campaign cannot be filtered into compliance, it has to be generated differently.
Both were invisible to an output filter and both were cheap at generation time.

**`PlayerProfileManager` cannot currently represent any of this.** It stores one
flat `lines_and_veils` list of strings, so `aggregate_safety_boundaries` hands the
governor a Line and a Veil as indistinguishable text. It cannot express that a
Line forbids and a Veil defers, that one player's animal Line is about on-screen
death rather than the content existing, that another's binds worldbuilding rather
than scenes, or that a third needs a private channel. Every one of those came out
of a single interview. Fixing the structure is a precondition, not a follow-up.
