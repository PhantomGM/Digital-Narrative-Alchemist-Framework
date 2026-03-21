---
tags: [template, item, artifact, relic]
entity_type: template
template_for: Item
dna_generator: item_generator.py
decoder_prompt: prompt_item.txt
output_directory: "07_History_Timeline_Legends"
---

# {{Item Name}}

> [!info] GM Notes
> **Parent Entity:** [[NPC_{{Name}}]] / [[Faction_{{Name}}]] / [[Quest_{{Name}}]]
> **Item Type:** {{weapon | armor | wand | staff | ring | amulet | potion | scroll | book | relic}}
> **DNA Version:** {{version}}
> **Generated:** {{date}}
> **Status:** {{complete | draft | thin}}

---

## 1. Brief Description

<!-- Concise summary: appearance, function, core identity. Note major contradictions like power vs. effect if present. -->

---

## 2. Physical Description

<!-- Detailed sensory description from PHY{} values: material, size, appearance, durability, craftsmanship, weight, form, texture. Address contradictions (e.g., Appearance vs. AP relationship). -->

---

## 3. Magical Properties

<!-- Effects from MAG{} values: effect, potency, duration, control, source, activation, requirement, transformation. Interpret Potency/Effect via Block values, reference Core Power scale if discrepancy exists. Explain CHAIN{USE} and CHAIN{MAG} implications. -->

---

## 4. History & Lore

<!-- Background from HIS{} and LOR{} values: origin, creator, age, reputation, legacy, former owners, destiny, stories. Explain contradictions (e.g., obscure history vs. notorious lore). -->

### Known History
<!-- What is widely known about this item -->

### Lost Knowledge
<!-- What has been forgotten or suppressed -->

### Legends & Rumors
<!-- What people whisper about this item -->

---

## 5. Attunement

<!-- Requirements and effects from ATTUNE{} values: user requirement, wielder effect, compatibility, mutation, synergy, vision, price, restriction. Explain CHAIN{ATT} implications. -->

### Requirements
<!-- Who can attune and how -->

### Effects on Wielder
<!-- Physical, psychological, or magical changes -->

### Cost of Use
<!-- The price paid for wielding this item -->

---

## 6. Game Mechanics

<!-- Suggested system-agnostic mechanics appropriate to interpreted power level. Incorporate curse, attunement effects, activation, control issues. -->

> [!warning] Balance Note
> {{Note on mechanical balance considerations}}

---

## 7. Evolution

<!-- How the item changes over time or with use, from EVO{} block. Describe whether power is STABLE, RISING, DECAYING, FLUCTUATING, etc. -->

### Current State
<!-- Where the item is on its evolutionary track -->

### Future Trajectory
<!-- How it will change with continued use or time -->

---

## Related Entities
- [[Conductor_Routing]]
- [[_99_Templates_and_Patterns_Index]]
- [[_07_History_Timeline_Legends_Index]]
- [[_00_Admin_and_Indexes_Index]]

- **Creator:** [[NPC_{{Name}}]]
- **Current Owner:** [[NPC_{{Name}}]]
- **Associated Faction:** [[Faction_{{Name}}]]
- **Found In:** [[Settlement_{{Name}}]] / [[Quest_{{Name}}]]
- **Lore Connection:** [[Region_{{Name}}]]
- **System Docs:** [[DNA_System_Rules]], [[Metadata_Priority_Logic]]
