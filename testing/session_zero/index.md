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
| [03_findings.md](03_findings.md) | **The write-up.** Eight things the trial validated, seven defects it found, and the branching-factor measurement that corrected `docs/PROJECT_STATE.md` §8. |

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
had a refinement pass, and all three print a template field label as an output
header — the same class of defect `docs/PROJECT_STATE.md` §7 records for palette
labels. It is not one bad decoder; it is a pattern in the unrefined set.

This also breaks name extraction downstream: `ExpansionManager._extract_name`
would take "World Overview" as the world's name.

## Not markdown, but part of the trial

- `player_profiles.json` — the four players, structured. Lines and Veils held
  apart, which `PlayerProfileManager` does not do.
- `registry.json` — the trial world's registry. Unconnected to the live world.
- `generation_index.json` — per-entity generation timings and record IDs.
- `generate_world.py` — the harness. `--dry-run` makes no model calls.
