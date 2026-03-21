# PF2EDNA: Pathfinder 2E AI Game Master Cartridge

PF2EDNA is a modular, hot-swappable AI Game Master Cartridge that encapsulates the Pathfinder 2nd Edition (PF2E) ruleset. It translates the raw markdown of an Obsidian Vault into a highly deterministic, self-contained data structure designed to be plugged directly into an AI orchestration layer.

## Architecture Overview

The cartridge is split into three core tiers to handle the mechanical, data, and semantic needs of the DNA Framework:

### 1. Executable Tier (`resolvers/`)
Stateless Python modules that encode the mechanics of Pathfinder 2E:
- **`dice.py`**: Handles d20s, dX, and advantage/disadvantage equivalent tracking (kh/kl).
- **`combat.py`**: Computes Multiple Attack Penalties (MAP) and the PF2E 4 degrees of success (Crit Success, Success, Failure, Crit Failure).
- **`abilities.py`**: Calculates modifiers (`floor((score - 10) / 2)`) and the TEML proficiency system.
- **`hp_tracker.py`**: Applies Immunities, Weaknesses, and Resistances.
- **`saves.py` & `skill_check.py`**: Saving throws and skill resolution.
- **`conditions.py`**: Applies and reduces valued conditions (e.g. Frightened 2).
- **`initiative.py`**: Perception-based and skill-based initiative roll tracking.
- **`spell_slots.py`**: Traditional prepared/spontaneous spell slots and focus points.
- **`progression.py`**: Leveling thresholds (1000 XP increments).
- **`encounter_budget.py`**: Trivial to Extreme encounter XP scaling based on party size.
- **`rest.py`**: Daily preparations and 10-minute Refocus activities.

### 2. Tabular Tier (`data/`)
Databases and JSON schemas containing the mechanics of the game natively structured for immediate query:
- `conditions.json` and `skills.json`
- `feats.json`, `races.json` (Ancestries), `classes.json`, `subclasses.json`, `backgrounds.json`
- `spells.db`, `items.db`, `monsters.db`

### 3. Semantic Tier (`knowledge/`)
Markdown files optimized to provide raw contextual information to the AI GM:
- `lore.md`: Core history and geography (Golarion, Inner Sea, Age of Lost Omens).
- `tone_guide.md`: Core high-fantasy themes, consequence weight, and teamwork focus.
- `roleplay_rules.md`: NPC Attitude scales (Helpful to Hostile) and Diplomacy actions.
- `alignment.md`: The 9-grid alignment system and its direct mechanical/damage implications.

## Integration & Getting Started

The cartridge is governed by `manifest.json`, which maps the schema, and controlled via the `GameSystemArbiter` class found in `arbiter.py`.

### Using the Arbiter

You do not need to call the resolvers or databases directly. Instantiate the `GameSystemArbiter` and use its three primary methods:

```python
from arbiter import GameSystemArbiter

arbiter = GameSystemArbiter()

# 1. Resolve Actions
result = arbiter.resolve_action('attack_melee', {
    'attack_mod': 9, 
    'target_ac': 18, 
    'attack_count': 1
})
print(result['degree_of_success'])

# 2. Query Tabular Data
skills_data = arbiter.query_data('skills', {'name': 'Athletics'})

# 3. Retrieve Semantic Knowledge
lore = arbiter.get_knowledge('lore')
```

## Smoke Tests
You can verify the integrity of the Python executable tier by running any module independently:
```powershell
python -m resolvers.combat
python -m resolvers.abilities
python -m resolvers.hp_tracker
```
