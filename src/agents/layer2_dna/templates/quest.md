---
tags: [template, quest, adventure, action]
entity_type: template
template_for: Quest
dna_generator: generator_quest.py
decoder_prompt: prompt_decode_quest.txt
output_directory: "08_Adventure_Content"
---

# {{Quest Title}}

> [!info] GM Notes
> **Parent Entity:** [[Region_{{Name}}]] / [[Settlement_{{Name}}]]
> **DNA Version:** {{version}}
> **Generated:** {{date}}
> **Status:** {{complete | draft | thin}}

---

## 1. The Hook

<!-- Engaging introduction drawing players in. Set the initial scene and present core motivation. -->

---

## 2. Background & Context

<!-- Backstory and situation leading to this quest. Anchor in the campaign world — reference factions, settlements, ongoing events. -->

**Key NPCs:**

- [[NPC_{{Name}}]] — {{role in quest}}
- [[NPC_{{Name}}]] — {{role in quest}}

**Involved Factions:**

- [[Faction_{{Name}}]] — {{stake in quest}}

---

## 3. Core Objectives

### Primary Objective
<!-- Clear statement of the main goal -->

### Secondary Objectives
<!-- Potential hidden or discovered objectives -->

### Hidden Objective
<!-- Concealed truth that may surface during play -->

---

## 4. Obstacles & Challenges

<!-- Detailed description of primary obstacles. Crucially explain HOW these challenges are meant to be approached — this is where OBS vs ENGAGE reconciliation happens. -->

### Primary Obstacles
<!-- From OBS{} block — describe the dangers -->

### Approach Guidance
<!-- From ENGAGE{} reconciliation — if high combat obstacles but low combat engagement, describe bypass strategies -->

> [!TIP]
> **Core Gameplay Contradiction:** {{Describe the central tension, e.g., "Massive military presence that must be circumvented through exploration and puzzle-solving, not confronted directly."}}

---

## 5. Adventure Structure & Flow

<!-- Beginning → Middle → End progression shaped by EVO{} data. Describe how difficulty, complexity, and rewards change over the course of the quest. -->

### Act 1: {{Title}}
<!-- Opening — Difficulty level, initial complexity -->

### Act 2: {{Title}}
<!-- Escalation — Rising tension, complications -->

### Act 3: {{Title}}
<!-- Climax — Peak challenge, resolution point -->

---

## 6. Key Scenes & Encounters

### Scene 1: {{Title}}

- **Type:** {{Combat | Social | Environmental | Supernatural | Puzzle | Exploration}}
- **Description:**
- **Stakes:**

### Scene 2: {{Title}}

- **Type:**
- **Description:**
- **Stakes:**

### Scene 3: {{Title}}

- **Type:**
- **Description:**
- **Stakes:**

---

## 7. Rewards & Spoils

### Tangible Rewards

- {{Gold / monetary reward}}
- [[Item_{{Name}}]] — {{description}}
- {{Skill or power gain}}

### Intangible Rewards

- {{Knowledge or information gained}}
- {{Reputation changes}}
- [[Faction_{{Name}}]] — {{loyalty or access earned}}
- {{New connections or alliances}}

---

## 8. Narrative & Tone

<!-- Key themes, pacing, dramatic moments. Describe the story's emotional arc. -->

---

## 9. Potential Outcomes

### Success
<!-- Full completion — consequences and rewards -->

### Failure
<!-- What happens if the party fails — consequences and fallout -->

### Alternative Outcome
<!-- Clever or unexpected player solutions -->

### Secret Outcome
<!-- Hidden resolution tied to the quest's deepest layer -->

---

## Related Entities
- [[Conductor_Routing]]
- [[_99_Templates_and_Patterns_Index]]
- [[_08_Adventure_Content_Index]]
- [[_00_Admin_and_Indexes_Index]]

- **Location:** [[Settlement_{{Name}}]], [[Region_{{Name}}]]
- **NPCs:** [[NPC_{{Name}}]], [[NPC_{{Name}}]]
- **Factions:** [[Faction_{{Name}}]]
- **Reward Items:** [[Item_{{Name}}]]
- **Travel:** [[Travel_{{Name}}]]
- **System Docs:** [[DNA_System_Rules]], [[Metadata_Priority_Logic]]
