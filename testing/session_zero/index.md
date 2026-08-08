# Index — Session 0 trial

Every markdown file in this folder. Start with [03_findings.md](03_findings.md)
if you only read one; [README.md](README.md) explains what the trial was.

---

## The trial itself

| File | What it holds |
| :--- | :--- |
| [README.md](README.md) | What this folder is, why it is committed with its flaws, and how to re-run it. |
| [00_TTRPG Player Profiles.md](00_TTRPG%20Player%20Profiles.md) | **The input.** The four simulated players as originally written — experience, play style, genres, Lines and Veils. Everything downstream derives from this file. `player_profiles.json` is a structured reading of it, not a replacement. |
| [01_round1_transcript.md](01_round1_transcript.md) | The four players' unedited answers to the Session 0 questionnaire, given privately before any of them saw another's. |
| [02_campaign_pitch.md](02_campaign_pitch.md) | The campaign pitch, assembled from the generated entities. Every proper noun in it came out of the pipeline. All four players accepted it. |
| [03_findings.md](03_findings.md) | **The write-up.** Eight things trial 1 validated, seven defects it found, and the branching-factor measurement that corrected `docs/PROJECT_STATE.md` §8. |
| [04_trial2_findings.md](04_trial2_findings.md) | **Trial 2.** The same players and the same transcripts, through the *built* machinery instead of scaffolding. Five of five retested defects fixed, no regressions, and one new negative result: the contract bounds what is generated, not what is implied. |
| [05_trial3_interview.md](05_trial3_interview.md) | **Trial 3.** A fresh interview from the same four profiles, inverting trial 2. Safety findings reproduce; creative findings do not — so a safety register can be cached per group and a contract cannot. Includes the methodological caveat about hinted prompts. |
| [06_trial4_hints_stripped.md](06_trial4_hints_stripped.md) | **Trial 4.** The same interview with the three leading hints deleted and one player held as an unchanged control. One finding reproduced unprompted, one **reversed**, one vanished. For safety, the hint turns out to be the instrument rather than the bias. |

## The generated world

Fifteen entities, decoded in this order. Each was generated with every prior page
as context, which is why the later ones cross-reference the earlier ones by name.

| # | File | Entity | Type | Size |
| ---: | :--- | :--- | :--- | ---: |
| 1 | [01_world.md](pages/01_world.md) | *(unnamed — see note)* | `world` | 10.2k |
| 2 | [02_region.md](pages/02_region.md) | The Saltspire Marches | `region` | 12.6k |
| 3 | [03_settlement.md](pages/03_settlement.md) | Deepstone Bastion | `settlement` | 13.1k |
| 4 | [04_regional_poi.md](pages/04_regional_poi.md) | The Deepstone Bastion Mine — "The Maw" | `regional_poi` | 8.6k |
| 5 | [05_culture.md](pages/05_culture.md) | The Shifting Communes | `culture` | 11.3k |
| 6 | [06_linguistic.md](pages/06_linguistic.md) | The Serpent's Cadence | `linguistic` | 5.1k |
| 7 | [07_faction_1.md](pages/07_faction_1.md) | The Obsidian Vigil — *wants the shaft sealed* | `faction` | 7.8k |
| 8 | [08_faction_2.md](pages/08_faction_2.md) | The Loom Syndicate — *wants the town, indifferent to the mine* | `faction` | 8.9k |
| 9 | [09_faction_3.md](pages/09_faction_3.md) | The Whispering Descent — *wants what is down there* | `faction` | 10.0k |
| 10 | [10_npc_1.md](pages/10_npc_1.md) | Kaelen, Archivist of Echoes | `npc` | 10.7k |
| 11 | [11_npc_2.md](pages/11_npc_2.md) | Morwen of the Sunken Paths | `npc` | 10.7k |
| 12 | [12_npc_3.md](pages/12_npc_3.md) | Seraphina Volkov | `npc` | 10.9k |
| 13 | [13_creature.md](pages/13_creature.md) | Aether-Mote | `creature` | 8.3k |
| 14 | [14_lore.md](pages/14_lore.md) | The Question | `lore` | 6.9k |
| 15 | [15_quest.md](pages/15_quest.md) | The Scholar's Descent | `quest` | 12.2k |

The three factions are asymmetric **in kind**, not merely in motive — one seeking,
one sealing, one indifferent to the mine entirely. That was a player's explicit
requirement in the interview, and it raised the faction count from the generic
contract's two to three. It is the clearest evidence in the trial that Session 0
shapes the quota rather than only the tone.

## Note: three decoders leak their template labels

Building this index surfaced a defect the findings under-reported. The first
heading of a page should be the entity's name. Three are not:

| File | First heading | Should be |
| :--- | :--- | :--- |
| `01_world.md` | `World Overview` | the world's name |
| `02_region.md` | `Region Name: The Saltspire Marches` | `The Saltspire Marches` |
| `15_quest.md` | `1. Quest Title` | `The Scholar's Descent` |

`world`, `region` and `quest` are all among the fourteen decoders that have never
had a refinement pass, and all three printed a template field label as an output
header — the same class of defect `docs/PROJECT_STATE.md` §7 records for palette
labels. It was not one bad decoder; it was a pattern in the unrefined set, and
checking the fix found it in `settlement` and `travel` as well.

It also broke name extraction downstream: `ExpansionManager._extract_name` would
have taken "World Overview" as the world's name.

**Fixed in `e1b9b57`**, and confirmed in a real run: none of trial 2's sixteen
pages opens with a template label.

## Trial 2's world

`pages_trial2/` holds the 16 entities generated from the same transcripts
through `ContentContract` and `ContextPackage.safety`. Read it beside `pages/`
to see what the fixes changed, or run `compare_trials.py`, which checks each
defect rather than leaving it to the eye. **Trial 2's pages open with entity
names, not template labels** — the table above is trial 1 only.

The clearest single difference is `pages_trial2/trial2_07_haven.md`, **The Cog &
Kettle**. Trial 1's contract had no way to ask for a warm room at all.

## Not markdown, but part of the trial

- `player_profiles.json` — the four players, structured. Lines and Veils held
  apart, which the old `PlayerProfileManager` could not do; it now can, via
  `layer3_operations/safety_register.py`.
- `registry.json` / `registry_trial2.json` — each trial's registry. Neither is
  connected to the live world.
- `generation_index.json` / `generation_index_trial2.json` — per-entity timings
  and record IDs.
- `generate_world.py` — the harness, rewired after trial 1 to use the real
  contract and safety machinery. `--dry-run` makes no model calls; `--out`
  chooses the pages directory and the registry follows it.
- `compare_trials.py` — the trial 1 vs trial 2 comparison. Reads only.
