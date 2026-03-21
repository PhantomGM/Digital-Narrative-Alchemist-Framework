# Ruleset Ingestion Blueprint

**Architectural specification for converting Obsidian Vault TTRPG rulesets into modular Layer IV cartridges for the DNA Framework's AI Game Master.**

> [!IMPORTANT]
> This document is a **blueprint for a Builder Agent** — a secondary AI that will execute the actual parsing and construction. It is NOT a human tutorial. Every section is designed for deterministic consumption by an autonomous agent.

---

## §1 — Core Architectural Principle

An AI Game Master operating on an LLM architecture cannot treat all data uniformly. Ruleset data must be classified into exactly **three storage modalities** based on how the runtime consumes it:

| Modality | Format | Runtime Access Pattern | When To Use |
|:---|:---|:---|:---|
| **Semantic** | Markdown (`.md`) | Injected into LLM context window | Content the LLM must *interpret, synthesize, or generate narrative around*. No math. No lookups. |
| **Tabular** | SQLite (`.db`) or JSON (`.json`) | Queried by Python resolvers via key/index | Structured data with many entries requiring rapid exact-match retrieval. Stats, tables, lists. |
| **Executable** | Python (`.py`) | Called deterministically by the Arbiter | Logic that **must not be left to LLM inference**: dice rolls, damage math, AC calculation, condition timers, state mutations. |

### Decision Threshold

```
Is the data used to GENERATE NARRATIVE?
  └─ YES → Semantic (.md)

Is the data a TABLE of 5+ entries that requires exact LOOKUP?
  └─ YES → Tabular (.db / .json)

Does the data involve MATH, RANDOMIZATION, or STATE MUTATION?
  └─ YES → Executable (.py)
```

---

## §2 — Data Structure Matrix

This matrix maps every standard TTRPG ruleset category to its required storage modality, file location within a cartridge, and the integration point with the DNA Framework runtime.

### 2.1 — Semantic Tier (Markdown)

Injected into LLM context window via the Orchestrator or Narrative Weaver.

| Category | Source Example (Obsidian) | Target File | Consumer Agent | Notes |
|:---|:---|:---|:---|:---|
| World Lore & Cosmology | `Lore/*.md`, `Deities/*.md` | `knowledge/lore.md` | Narrative Weaver | Flavor. Never queried programmatically. |
| Tone & Genre Guide | `Campaign/tone.md` | `knowledge/tone_guide.md` | Safety Governor, Weaver | Defines the "voice" of the system. |
| Roleplay Instructions | `Rules/roleplay.md` | `knowledge/roleplay_rules.md` | Narrative Weaver | How NPCs should behave narratively. |
| Alignment / Morality System | `Rules/alignment.md` | `knowledge/alignment.md` | NPC Engines, Weaver | Interpretive, not mechanical. |
| Adventure Hooks / Plot Seeds | `Adventures/*.md` | `knowledge/adventure_seeds.md` | Session Director | Scene framing context. |
| Downtime Activities (Narrative) | `Rules/downtime.md` | `knowledge/downtime.md` | Session Director | Non-mechanical downtime rules. |

### 2.2 — Tabular Tier (SQLite / JSON)

Queried by Python resolver scripts or exposed to the LLM as structured context blocks.

| Category | Source Example (Obsidian) | Target File | Schema | Consumer |
|:---|:---|:---|:---|:---|
| Races / Species | `Races/*.md` | `data/races.json` | `{id, name, ability_bonuses:{}, traits:[], size, speed, languages:[]}` | Character Model Adapter |
| Classes | `Classes/*.md` | `data/classes.json` | `{id, name, hit_die, primary_ability, saving_throws:[], proficiencies:[], features_by_level:{}}` | Character Model Adapter |
| Subclasses / Archetypes | `Classes/Subclasses/*.md` | `data/subclasses.json` | `{id, name, parent_class_id, features_by_level:{}}` | Character Model Adapter |
| Spells | `Spells/*.md` | `data/spells.db` | `{id, name, level, school, casting_time, range, components, duration, description, damage_dice, save_type, higher_levels}` | Combat Resolver, Weaver |
| Items & Equipment | `Items/*.md` | `data/items.db` | `{id, name, category, cost, weight, damage_dice, damage_type, properties:[], rarity, attunement, description}` | Combat Resolver, Weaver |
| Monsters / NPC Stat Blocks | `Bestiary/*.md` | `data/monsters.db` | `{id, name, size, type, alignment, ac, hp_formula, speed:{}, ability_scores:{}, skills:{}, senses:{}, cr, traits:[], actions:[], legendary_actions:[]}` | Encounter Director, Combat Resolver |
| Conditions | `Rules/conditions.md` | `data/conditions.json` | `{id, name, effects:[], mechanical_modifiers:{}}` | Condition Resolver |
| Skills | `Rules/skills.md` | `data/skills.json` | `{id, name, ability, description}` | Arbiter |
| Feats | `Feats/*.md` | `data/feats.json` | `{id, name, prerequisite, effects:[], mechanical_modifiers:{}}` | Character Model Adapter |
| Backgrounds | `Backgrounds/*.md` | `data/backgrounds.json` | `{id, name, proficiencies:[], equipment:[], feature_name, feature_description}` | Character Model Adapter |

### 2.3 — Executable Tier (Python)

Deterministic logic that must never be delegated to LLM inference.

| Category | Source Rules (Obsidian) | Target File | Interface Method | Notes |
|:---|:---|:---|:---|:---|
| Dice Engine | `Rules/dice.md` | `resolvers/dice.py` | `roll(notation: str) → RollResult` | Parses "2d6+3", "1d20", "4d6kh3" etc. |
| Ability Score Calculator | `Rules/abilities.md` | `resolvers/abilities.py` | `calc_modifier(score: int) → int` | `floor((score - 10) / 2)` |
| Attack Resolution | `Rules/combat.md` | `resolvers/combat.py` | `resolve_attack(attacker, target, weapon) → AttackResult` | d20 + mod vs AC, damage roll, crit logic |
| Saving Throw Resolution | `Rules/saves.md` | `resolvers/saves.py` | `resolve_save(target, dc, save_type) → SaveResult` | d20 + mod vs DC |
| Skill Check Resolution | `Rules/skills.md` | `resolvers/skill_check.py` | `resolve_check(actor, skill, dc) → CheckResult` | d20 + prof + mod vs DC |
| HP / Damage Tracker | `Rules/combat.md` | `resolvers/hp_tracker.py` | `apply_damage(entity, amount, type) → HPState` | Resistance/vulnerability/immunity logic |
| Condition Manager | `Rules/conditions.md` | `resolvers/conditions.py` | `apply_condition(entity, condition_id) → None` | Duration tracking, stacking rules |
| Initiative Engine | `Rules/combat.md` | `resolvers/initiative.py` | `roll_initiative(combatants) → TurnOrder` | DEX + mods, tie-breaking |
| Spell Slot Tracker | `Rules/spellcasting.md` | `resolvers/spell_slots.py` | `cast_spell(caster, spell, slot_level) → CastResult` | Slot expenditure, upcast logic |
| Leveling / XP Engine | `Rules/advancement.md` | `resolvers/progression.py` | `check_levelup(entity) → LevelUpResult` | XP thresholds, milestone tracking |
| Encounter Budget Calculator | `Rules/encounter_building.md` | `resolvers/encounter_budget.py` | `calculate_difficulty(party, monsters) → DifficultyRating` | CR math, XP thresholds |
| Rest Engine | `Rules/resting.md` | `resolvers/rest.py` | `apply_rest(entity, rest_type) → RestResult` | Short rest (Hit Dice), Long rest (full recovery) |

---

## §3 — Cartridge Directory Structure

Each ruleset cartridge is a self-contained directory under `src/layer4_rules/`. The directory layout is **mandatory** — the Builder Agent must produce this exact structure.

```
src/layer4_rules/<system_name>/
├── arbiter.py              # Master dispatcher — implements GameSystemArbiter interface
├── manifest.json           # Cartridge metadata and capability declarations
│
├── resolvers/              # Executable Tier — deterministic Python logic
│   ├── __init__.py
│   ├── dice.py
│   ├── combat.py
│   ├── saves.py
│   ├── skill_check.py
│   ├── hp_tracker.py
│   ├── conditions.py
│   ├── initiative.py
│   ├── spell_slots.py
│   ├── progression.py
│   ├── encounter_budget.py
│   ├── rest.py
│   └── abilities.py
│
├── data/                   # Tabular Tier — queryable structured data
│   ├── races.json
│   ├── classes.json
│   ├── subclasses.json
│   ├── spells.db           # SQLite for large datasets (100+ entries)
│   ├── items.db            # SQLite for large datasets
│   ├── monsters.db         # SQLite for large datasets
│   ├── conditions.json
│   ├── skills.json
│   ├── feats.json
│   └── backgrounds.json
│
├── knowledge/              # Semantic Tier — LLM context injection material
│   ├── lore.md
│   ├── tone_guide.md
│   ├── roleplay_rules.md
│   ├── alignment.md
│   ├── adventure_seeds.md
│   └── downtime.md
│
└── adapters/               # Character Model Adapters (optional)
    ├── __init__.py
    └── character_model.py  # Translates narrative intent into game stats
```

---

## §4 — `manifest.json` Schema

Every cartridge **must** contain a `manifest.json` at its root. This file declares the cartridge's identity, capabilities, and integration requirements. The Orchestrator reads this at load time.

```json
{
  "system_name": "D&D 5th Edition (SRD)",
  "system_id": "dnd_5e_srd",
  "version": "1.0.0",
  "author": "Builder Agent v1",
  "description": "System Reference Document rules for D&D 5th Edition.",

  "dice_notation": "standard",
  "primary_die": "d20",

  "capabilities": {
    "combat_resolution": true,
    "spell_casting": true,
    "skill_checks": true,
    "saving_throws": true,
    "conditions": true,
    "initiative": true,
    "leveling": true,
    "encounter_budgeting": true,
    "resting": true,
    "downtime": false
  },

  "data_files": {
    "races": "data/races.json",
    "classes": "data/classes.json",
    "spells": "data/spells.db",
    "items": "data/items.db",
    "monsters": "data/monsters.db",
    "conditions": "data/conditions.json",
    "skills": "data/skills.json",
    "feats": "data/feats.json",
    "backgrounds": "data/backgrounds.json"
  },

  "knowledge_files": {
    "lore": "knowledge/lore.md",
    "tone_guide": "knowledge/tone_guide.md",
    "roleplay_rules": "knowledge/roleplay_rules.md",
    "alignment": "knowledge/alignment.md"
  },

  "resolver_modules": {
    "dice": "resolvers.dice",
    "combat": "resolvers.combat",
    "saves": "resolvers.saves",
    "skill_check": "resolvers.skill_check",
    "hp_tracker": "resolvers.hp_tracker",
    "conditions": "resolvers.conditions",
    "initiative": "resolvers.initiative",
    "spell_slots": "resolvers.spell_slots",
    "progression": "resolvers.progression"
  }
}
```

---

## §5 — Arbiter Interface Contract

The `arbiter.py` is the **only file the Orchestrator imports directly**. It must implement the `GameSystemArbiter` class with the following interface. This is the integration boundary between the DNA Framework (Layers I-III) and the ruleset cartridge (Layer IV).

```python
class GameSystemArbiter:
    """
    Layer IV Master Dispatcher.
    
    The Orchestrator calls resolve_action() with a classified intent.
    The Arbiter routes to the correct resolver, queries data as needed,
    and returns a structured result the Narrative Weaver can prose-ify.
    """
    
    def __init__(self):
        self.system_name: str           # Human-readable name
        self.manifest: dict             # Loaded from manifest.json
        self.resolvers: dict            # Lazy-loaded resolver modules
        self.data: dict                 # Handles to data files / DB connections

    def resolve_action(self, action_intent: str, active_stats: dict = None) -> dict:
        """
        Primary dispatch method called by the Orchestrator.
        
        Args:
            action_intent: Classified intent string from Orchestrator 
                           (e.g., "attack_melee", "skill_check_stealth", 
                           "cast_spell", "save_vs_poison")
            active_stats:  Current entity state dict from WorldStateKeeper
                           (e.g., {"hp": 45, "ac": 16, "str_mod": 3, ...})
        
        Returns:
            dict with keys:
                "success": bool
                "narrative_effect": str   — flavor text for the Weaver
                "mechanical_delta": dict  — state changes to emit to EventLedger
                "details": dict           — raw numbers for logging/debugging
        """

    def query_data(self, table: str, query: dict) -> list:
        """
        Structured data lookup (items, spells, monsters, etc.)

        Args:
            table: Data file key from manifest (e.g., "spells", "monsters")
            query: Filter dict (e.g., {"name": "Fireball"}, {"cr_max": 5})
        
        Returns:
            List of matching records.
        """

    def get_knowledge(self, category: str) -> str:
        """
        Returns semantic Markdown content for LLM context injection.

        Args:
            category: Knowledge file key (e.g., "lore", "tone_guide")
        
        Returns:
            Raw Markdown string ready for prompt injection.
        """
```

---

## §6 — Builder Agent Protocol

This section defines the **exact rules** the secondary Builder Agent must follow when parsing an Obsidian Vault and constructing a cartridge.

### 6.1 — Source Parsing Rules

| Rule ID | Rule | Rationale |
|:---|:---|:---|
| `P-01` | Parse each Obsidian `.md` file independently. Do not rely on `[[wiki-links]]` for data extraction. | Links are navigational, not structural. |
| `P-02` | Extract YAML frontmatter first. If a file has `type: spell`, `type: monster`, etc., use that as the primary classifier. | Obsidian vaults often use frontmatter for metadata. |
| `P-03` | If no frontmatter exists, classify by directory name (e.g., files in `Spells/` are spells). | Fallback heuristic. |
| `P-04` | Treat Markdown tables as tabular data candidates. Extract into JSON/SQLite. | Tables within prose indicate structured data. |
| `P-05` | Treat blockquotes (`>`) as flavor text. Route to Semantic tier. | Blockquotes are narrative, not mechanical. |
| `P-06` | Treat inline code (`` `1d8+3` ``) as dice notation. Map to Executable tier references. | Inline code in TTRPG vaults is almost always dice or formulas. |
| `P-07` | If a file mixes narrative prose and stat blocks, **split it**: narrative → `knowledge/*.md`, stats → `data/*.json`. | Strict separation of concerns. |

### 6.2 — Data Transformation Rules

| Rule ID | Rule | Example |
|:---|:---|:---|
| `T-01` | All JSON files must use `id` as the primary key, derived from the entity name via `snake_case`. | `"Fireball"` → `"fireball"` |
| `T-02` | All ability scores must be stored as integers, not strings. Modifiers are computed at runtime by `abilities.py`. | `"str": 18` not `"str": "18 (+4)"` |
| `T-03` | All dice expressions must be stored as notation strings. Never pre-compute averages. | `"damage_dice": "2d6+3"` |
| `T-04` | Multi-value fields (traits, languages, proficiencies) must be JSON arrays, never comma-separated strings. | `"languages": ["Common", "Elvish"]` |
| `T-05` | Boolean flags must be actual booleans, never `"yes"/"no"` strings. | `"attunement": true` |
| `T-06` | Use SQLite for any table exceeding **100 entries**. Use JSON below that threshold. | Spells (300+) → `.db`, Conditions (15) → `.json` |
| `T-07` | All `.db` files must include a `_meta` table with columns `(key TEXT, value TEXT)` storing `schema_version` and `source_system`. | Versioning and provenance. |

### 6.3 — Resolver Implementation Rules

| Rule ID | Rule | Rationale |
|:---|:---|:---|
| `R-01` | Every resolver function must be **pure** — no side effects, no LLM calls, no network I/O. Input → Output. | Determinism. The Arbiter handles state mutation via return values. |
| `R-02` | Every resolver must return a typed dataclass or TypedDict, not a raw dict. | Type safety for downstream consumers. |
| `R-03` | All randomness must flow through `resolvers/dice.py`. No direct `random.randint()` calls elsewhere. | Single source of randomness for testing/seeding. |
| `R-04` | Resolver functions must accept primitive types and dicts only — no ORM objects, no framework types. | Decoupling from any specific framework. |
| `R-05` | Every resolver module must include at minimum a `# --- SMOKE TEST ---` block runnable via `if __name__ == "__main__"`. | Immediate validation without pytest. |

### 6.4 — Integration Wiring Rules

| Rule ID | Rule | Rationale |
|:---|:---|:---|
| `I-01` | The Arbiter must lazy-load resolvers on first call. Do not import all resolvers at `__init__` time. | Fast cartridge swap at runtime. |
| `I-02` | `manifest.json` must be loadable independently — no Python imports required to read it. | The Orchestrator may inspect manifests without loading full cartridges. |
| `I-03` | The `data/` directory must be readable without the `resolvers/` directory. | Data can be used for LLM context even without mechanical resolution. |
| `I-04` | Knowledge files must not exceed **8,000 tokens** each. Split into multiple files if necessary. | LLM context window budget management. |
| `I-05` | Cartridge must work with **zero** knowledge files (pure mechanical system). Knowledge is optional enrichment. | Minimum viable cartridge = Arbiter + Resolvers + Data. |

---

## §7 — Minimum Viable Cartridge (MVC) Checklist

The Builder Agent must verify this checklist before declaring a cartridge complete:

- [ ] `arbiter.py` exists and implements `GameSystemArbiter` with `resolve_action()`, `query_data()`, `get_knowledge()`
- [ ] `manifest.json` exists and is valid JSON with all required fields from §4
- [ ] `resolvers/dice.py` exists and handles the system's dice notation
- [ ] `resolvers/combat.py` exists and resolves at minimum: melee attack, ranged attack
- [ ] `resolvers/abilities.py` exists and computes ability modifiers
- [ ] `data/conditions.json` exists (even if the system has zero conditions, file must exist with `[]`)
- [ ] `data/skills.json` exists
- [ ] At minimum one `knowledge/*.md` file exists (can be a stub `tone_guide.md`)
- [ ] All resolver smoke tests pass
- [ ] `arbiter.py` can be imported and instantiated with zero arguments
- [ ] `arbiter.resolve_action("attack_melee", {"str_mod": 3, "weapon": "longsword"})` returns a valid dict

---

## §8 — Migration Path from Existing Stubs

The current repo has two stub cartridges (`one_page_5e`, `coin_flip`) that predate this specification. They are **not** compliant with this blueprint. The migration path:

| Current State | Target State |
|:---|:---|
| `one_page_5e/arbiter.py` (15 LOC stub) | Full cartridge per §3 directory structure |
| `coin_flip/arbiter.py` (20 LOC stub) | Keep as-is — intentionally minimal for testing hot-swap |
| No `manifest.json` | Required for both |
| No `resolvers/` | Required for `one_page_5e`, optional for `coin_flip` |
| No `data/` | Required for `one_page_5e` |
| No `knowledge/` | Optional but recommended |

> [!NOTE]
> The `coin_flip` cartridge is a deliberate edge case — a system with no tables, no complex resolution, and no knowledge. It should receive a `manifest.json` with all capabilities set to `false`, but otherwise remain minimal. It proves the cartridge interface works even with zero data.

---

*Blueprint version: 1.0 — Generated for Builder Agent consumption.*
