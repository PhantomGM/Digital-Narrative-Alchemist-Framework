---
tags: [system, dna, rules, core]
entity_type: system_doc
version: "1.0"
related_docs:
  - "[[Metadata_Priority_Logic]]"
  - "[[Conductor_Routing]]"
  - "[[_99_Templates_and_Patterns_Index]]"
---

# DNA System Rules

> The master reference for the **Digital Narrative Alchemist (DNA)** procedural content generation and decoding framework. This document governs how the AI generates, interprets, and stores TTRPG content within the [[_00_Admin_and_Indexes_Index|World Bible]].

---

## Multi-Agent Architecture

The DNA system operates through four sequential layers:

| Layer | Role | Description |
|:------|:-----|:------------|
| **Conductor** | Central Router | Parses user intent, manages conversational flow, routes to the correct generator. See [[Conductor_Routing]]. |
| **User Interface** | Structured Input | Presents creation menus specific to each entity type, ensuring well-formed input parameters. |
| **DNA Forge** | Procedural Engine | Uses Python generators and `random` to produce raw **DNA strings** — alphanumeric codes representing the entity's fundamental truth. |
| **Storyteller** | Narrative Decoder | Translates the raw DNA string into polished, system-agnostic narrative using the decoding prompts. All technical data is hidden from final output. |

---

## Supported Content Types

Each content type has a dedicated **Generator** (Python) and **Decoder** (prompt), producing output stored in the [[_00_Admin_and_Indexes_Index|World Bible]] directories.

| Scale | Content Type | Generator | Decoder | Output Directory |
|:------|:-------------|:----------|:--------|:-----------------|
| Macro | World / Realm | `world_generator.py` | `prompt_decode_world.txt` | [[_01_Foundation_and_Cosmology_Index]] / [[_02_Geography_and_Environment_Index]] |
| Meso | Region | `world_generator.py` (regional) | `prompt_decode_world.txt` | [[_02_Geography_and_Environment_Index]] |
| Meso | Settlement / Location | `location_generator.py` | `prompt_location_finalized.txt` | [[_03_Polities_and_Cultures_Index]] |
| Org | Faction / Agency | `generator_faction.py` | `prompt_decode_faction.txt` | [[_04_Factions_Organizations_Religions_Index]] |
| Micro | NPC | `npc_generator.py` | `prompt_npc.txt` | [[_08_Adventure_Content_Index]] |
| Action | Quest | `generator_quest.py` | `prompt_decode_quest.txt` | [[_08_Adventure_Content_Index]] |
| Artifact | Magic Item / Relic | `item_generator.py` | `prompt_item.txt` | [[_07_History_Timeline_Legends_Index]] |
| Environ | Travel Scenario | `travel_generator.py` | `Travel DNA Prompt GPT.txt` | [[_08_Adventure_Content_Index]] |

---

## DNA String Architecture

Every DNA string follows a common structural pattern:

```
ENTITY{v1.0[CoreScale1/CoreScale2/CoreScale3]}<Relationship1,Relationship2,Relationship3>#type
BLOCK1{Key1Value1,Key2Value2,...}
BLOCK2{Key1Value1,Key2Value2,...}
CHAIN{Connection1;Connection2;Connection3}
EVO{Track1:PATTERN[V1,V2,V3,V4];Track2:PATTERN[V1,V2,V3,V4]}
```

### Value Interpretation

| Range | Meaning |
|:------|:--------|
| 1–33 | **Low** — weak, minor, rare, easy |
| 34–66 | **Medium** — moderate, balanced |
| 67–99 | **High** — strong, major, dominant, extreme |
| Core 1–3 | Broad category: weak/simple/common |
| Core 4–6 | Broad category: moderate |
| Core 7–9 | Broad category: powerful/complex/rare |

### Relationship Values

- **Below 1.0** → Inverse relationship (e.g., high appearance but low power)
- **Above 1.0** → Direct relationship (e.g., high rarity correlates with high effect)

### CHAIN Connections

Format: `CHAIN{DOMAIN:A>B>C}` — means changes in A cascade to B, which cascades to C.

### EVO Patterns

Format: `EVO{TRACK:PATTERN[V1,V2,V3,V4]}` — tracks how an attribute evolves over four time periods.

| Pattern | Meaning |
|:--------|:--------|
| STABLE | Resistant to change; V-values = resistance strength |
| RISING | Increasing over time; V-values = rate of increase |
| DECLINING / DESCENDING | Decreasing over time; V-values = rate of decrease |
| ACCELERATING | Rapidly intensifying; V-values = acceleration rate |
| FLUCTUATING | Oscillating unpredictably |
| CLIMACTIC | Building toward a dramatic peak |
| UNSTABLE | Chaotically shifting |
| DORMANT | Currently inactive but potentially awakening |

---

## Five Narrative Synthesis Mandates

These are **non-negotiable** rules governing all decoded output:

### 1. Embodiment of Data
>
> Numbers must never appear as raw stats. A magic prevalence of 9 becomes *"arcane storms routinely shatter the laws of physics"* — not *"Magic: 9"*.

### 2. Organic Emergence
>
> Traits reveal themselves through tone, behavior, and sensory detail. "Militaristic" becomes *rigid patrols, marching boots, fortified architecture* — never a label.

### 3. Accuracy Overrides Creativity
>
> The AI is **forbidden** from inventing content that contradicts DNA values. If technology is low, no clockwork mechanisms — pivot the aesthetic to match.

### 4. Inter-Block Causality
>
> The AI must demonstrate how one value shapes another. High magic + high conflict → *"warring factions battle for control over the last stable ley lines."*

### 5. Output Privacy
>
> Raw DNA codes and numeric interpretations are **strictly internal**. The final output must never reference mechanics, tags, or numbers.

---

## Resolution Engine

When DNA generation produces contradictory data points, the system treats them as **narrative opportunities**, not errors:

| Contradiction | Resolution Strategy |
|:--------------|:-------------------|
| High Lethality + Mundane Occupants | Suicidal swarm tactics, deadly environmental hazards, localized curses |
| Pristine Condition + Ancient History | Magical stasis fields, spectral caretakers, automated repair |
| High Reward + Easy Access | It's bait — devastating trap, social conundrum, or cursed hoard |
| High Combat Obstacle + Low Combat Engagement | Players are expected to **bypass** combat via exploration, stealth, or puzzles |
| Cursed + Revered | A death cult reveres it *because* of its lethal curse |

> [!TIP]
> The Resolution Engine is the primary mechanism by which random generation tables are elevated into compelling, specific TTRPG content.

---

## AI Personalities (History Generation)

For deep history and cultural evolution, the system deploys four distinct AI personalities:

| Personality | Focus | Tone | Tendency |
|:------------|:------|:-----|:---------|
| Idealist Visionary | Progress, unity | Light | Breakthroughs, alliances, advancements |
| Pragmatic Realist | Economics, power | Mixed | Logistics, scarcity, consequences |
| Cultural Anthropologist | Societies, beliefs | Mixed | Cultural patterns, faith movements |
| Conflict Theorist | Struggles, tension | Dark | War, instability, institutional collapse |

These interact through the **Oracle System** (Yes/No probability decisions) and the **Tone System** (Light/Dark epoch determination).

---

## Entity File Structure

Each generated entity in the World Bible consists of up to three files:

| File | Purpose | Example |
|:-----|:--------|:--------|
| `Entity_Name.md` | Human-readable narrative profile | `The_Shattered_Coast.md` |
| `Entity_Name.dna.json` | Raw algorithmic DNA string | `The_Shattered_Coast.dna.json` |
| `Entity_Name.meta.json` | Metadata tracking (inheritance, locks, incomplete fields) | `The_Shattered_Coast.meta.json` |

See [[Metadata_Priority_Logic]] for the rules governing these files.

---

## Related Documents

- [[Metadata_Priority_Logic]] — Data hierarchy, Thin Parent architecture, field locking
- [[Conductor_Routing]] — User intent routing, directory mapping, generation scales
- [[Entity_Master_Index]] — Auto-generated dashboard of all vault entities
- [[_99_Templates_and_Patterns_Index]] — All profile templates

## Related Entities
- [[Template_World]]
- [[Template_Travel]]
- [[Template_Settlement]]
- [[Template_Region]]
- [[Template_Quest]]
- [[Template_NPC]]
- [[Template_Meta_JSON]]
- [[Template_Item]]
- [[Template_Faction]]

- [[Template_DNA_JSON]]
