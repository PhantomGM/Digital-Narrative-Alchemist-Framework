---
tags: [template, settlement, location, meso]
entity_type: template
template_for: Settlement
dna_generator: location_generator.py
decoder_prompt: prompt_location_finalized.txt
output_directory: "03_Polities_and_Cultures"
---

# {{Settlement Name}}

> [!info] GM Notes
> **Parent Entity:** [[Region_{{Name}}]]
> **Settlement Type:** {{village | town | city | outpost | port-city | fortress | capital | hamlet | metropolis}}
> **DNA Version:** {{version}}
> **Generated:** {{date}}
> **Status:** {{complete | draft | thin}}

---

## 1. Overview

<!-- Key features, core identity, and major contradictions. Note any discrepancy between official classification and current reality. -->

---

## 2. Physical Description

<!-- Architecture, state of defenses, feel of public spaces. Highlight striking contrasts (e.g., formidable walls protecting a decaying interior). Drawn from STRUCT{} block. -->

---

## 3. Population

<!-- People, attitude, culture, daily life, health, crime, morale. Describe cause-and-effect from CHAIN{POP} in story terms. Drawn from POP{} block. -->

---

## 4. Economy

<!-- Primary trades, resources, market quality, services, industries, guild power. Describe CHAIN{ECON} through real-world effects. Drawn from ECON{} block. -->

---

## 5. Politics & Law

<!-- Governance system, corruption, freedom, stability. Illustrate CHAIN{POL} with narrative examples. Drawn from POL{} block. -->

---

## 6. Notable Locations

<!-- Key establishments and points of interest. Link to dedicated profiles where they exist. From POI{} block. -->

- [[Establishment_{{Name}}]] — {{brief description}}
- [[Establishment_{{Name}}]] — {{brief description}}
- {{Landmark or site}} — {{brief description}}

---

## 7. Surroundings

<!-- Immediate vicinity and relationships implied by proximity. From PROXI{} values. -->

- **Wilderness proximity:** {{description}}
- **Nearest town:** [[Settlement_{{Name}}]] — {{distance/relationship}}
- **Nearest city:** [[Settlement_{{Name}}]] — {{distance/relationship}}
- **Nearby ruins:** [[Location_{{Name}}]] — {{description}}

---

## 8. Trajectory

<!-- Is the settlement growing, shrinking, or transforming? Describe trends through tangible effects, not labels. From EVO{} block. -->

### Size Trend
<!-- Physical expansion or contraction -->

### Population Trend
<!-- Demographic changes -->

### Importance Trend
<!-- Rising or falling significance -->

---

## 9. Hooks & Opportunities

### Hook 1: {{Title}}
<!-- Stems from the settlement's unique characteristics or contradictions -->

### Hook 2: {{Title}}

### Hook 3: {{Title}}

---

## Key NPCs

- [[NPC_{{Name}}]] — {{role in settlement}}
- [[NPC_{{Name}}]] — {{role in settlement}}

## Factions Present

- [[Faction_{{Name}}]] — {{influence in settlement}}
- [[Faction_{{Name}}]] — {{influence in settlement}}

---

## Related Entities
- [[Conductor_Routing]]
- [[_99_Templates_and_Patterns_Index]]
- [[_03_Polities_and_Cultures_Index]]
- [[_02_Geography_and_Environment_Index]]
- [[_00_Admin_and_Indexes_Index]]

- **Region:** [[Region_{{Name}}]]
- **NPCs:** [[NPC_{{Name}}]], [[NPC_{{Name}}]]
- **Factions:** [[Faction_{{Name}}]]
- **Quests:** [[Quest_{{Name}}]]
- **Travel Routes:** [[Travel_{{Name}}]]
- **System Docs:** [[DNA_System_Rules]], [[Metadata_Priority_Logic]]
