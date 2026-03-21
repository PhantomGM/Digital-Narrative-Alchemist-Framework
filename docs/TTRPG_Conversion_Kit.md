# TTRPG Ruleset Conversion Kit

This document provides the standardized methodology for scaling the DNA Framework's Layer IV by converting external Markdown-based TTRPG rulesets (e.g., Obsidian vaults) into production-ready runtime cartridges.

To eliminate structural drift, schema violations, and manual boilerplate, this conversion process is strictly automated. The methodology relies on an `init_cartridge.py` bootstrap script that enforces the 3-Tier Modality architecture (Semantic, Tabular, Executable) and establishes mandatory Test-Driven Development (TDD) pipelines.

---

## 🏗️ 3-Tier Modality Refresher

Every cartridge must strictly silo its data based on how the Orchestrator and LLM runtime consume it.

1. **Semantic Tier (`knowledge/*.md`)**: Pure flavor, world lore, and roleplay rules. Injected raw into the LLM context window. **No mechanical execution logic or math.**
2. **Tabular Tier (`data/*.json` or `*.db`)**: Queryable, structured datasets (items, spells, monster stat blocks). Stored as JSON arrays or SQLite databases with `_meta` tables.
3. **Executable Tier (`resolvers/*.py`)**: Deterministic python modules handling combat, dice math, and state mutation. **Must be pure functions with zero LLM inference.**

---

## 🤖 AI Builder Agent Handoff

Converting a massive Obsidian vault manually is inefficient. Instead, the workflow is:
1. A human developer runs `init_cartridge.py --name "SystemName"`.
2. The script scaffolds the pristine directory tree, stubs out compliant `manifest.json` and `arbiter.py` interfaces, generates `pytest` TDD suites, and builds a strict `TODO.md` prompt.
3. A secondary AI Assistant (the **Builder Agent**) is activated within the cartridge directory. It reads the `TODO.md` and uses its tool-calling capabilities to ingest, parse, and populate the cartridge autonomously.

---

## 🚀 Bootstrap Script (`init_cartridge.py`)

Save the following code as `init_cartridge.py` at the root of the project to automate cartridge creation.

```python
import os
import sys
import json
import argparse

def scaffold_cartridge(name: str):
    system_id = name.lower().replace(" ", "_").replace("-", "_")
    base_dir = os.path.join("src", "rulesets", name)
    
    if os.path.exists(base_dir):
        print(f"Error: Cartridge '{name}' already exists at {base_dir}")
        sys.exit(1)
        
    print(f"Scaffolding Layer IV Cartridge: {name} ({system_id})...")
    
    # 1. Create Directory Tree
    dirs = [
        "",
        "resolvers",
        "data",
        "knowledge",
        "adapters",
        "tests"
    ]
    
    for d in dirs:
        os.makedirs(os.path.join(base_dir, d), exist_ok=True)
        
    # 2. Generate Pristine manifest.json
    manifest = {
        "system_name": name,
        "system_id": system_id,
        "version": "1.0.0",
        "author": "DNA Bootstrap System",
        "description": f"Ruleset cartridge for {name}.",
        "cartridge_type": "Layer_IV_Ruleset",
        "primary_die": "d20",
        "capabilities": {
            "combat_resolution": False,
            "skill_checks": False,
            "saving_throws": False,
            "spellcasting": False,
            "rest_mechanics": False,
            "encounter_budgeting": False
        },
        "data_files": {},
        "knowledge_files": {
            "tone_guide": "knowledge/tone_guide.md"
        },
        "resolver_modules": {
            "dice": "resolvers.dice",
            "combat": "resolvers.combat"
        }
    }
    
    with open(os.path.join(base_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    # 3. Generate Basic Arbiter (arbiter.py)
    arbiter_code = f'''import os
import json
import importlib

class GameSystemArbiter:
    """Master Layer IV Dispatcher for {name}."""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.root_dir, "manifest.json"), "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
        self._resolvers = {{}}
        
    def _get_resolver(self, module_key: str):
        if module_key not in self._resolvers:
            path = self.manifest["resolver_modules"].get(module_key)
            if not path: raise ValueError(f"Resolver {{module_key}} not mapped.")
            # Ensure sys.path knows about our root for relative-like imports during hot load
            import sys
            if self.root_dir not in sys.path:
                sys.path.insert(0, self.root_dir)
            self._resolvers[module_key] = importlib.import_module(path)
        return self._resolvers[module_key]

    def resolve_action(self, action_intent: str, active_stats: dict = None) -> dict:
        """Route mechanical intents to Executable Tier py modules."""
        if action_intent == "attack":
            return self._get_resolver("combat").resolve_attack(active_stats)
        raise NotImplementedError(f"Intent {{action_intent}} not mapped.")

    def query_data(self, table: str, query: dict) -> list:
        raise NotImplementedError("Tabular dataset querying not implemented.")

    def get_knowledge(self, topic: str) -> str:
        """Inject Semantic Tier markdown into LLM context."""
        rel_path = self.manifest["knowledge_files"].get(topic)
        if not rel_path: raise ValueError(f"Topic {{topic}} missing.")
        with open(os.path.join(self.root_dir, rel_path), "r", encoding="utf-8") as f:
            return f.read()
'''
    with open(os.path.join(base_dir, "arbiter.py"), "w", encoding="utf-8") as f:
        f.write(arbiter_code)
        
    # 4. Generate Executable Tier Stubs
    with open(os.path.join(base_dir, "resolvers", "dice.py"), "w", encoding="utf-8") as f:
        f.write('def roll(notation: str) -> int:\n    """Parse and roll standard dice notation."""\n    return 1 # TODO\n')

    with open(os.path.join(base_dir, "resolvers", "combat.py"), "w", encoding="utf-8") as f:
        f.write('from .dice import roll\n\ndef resolve_attack(stats: dict) -> dict:\n    return {"success": True, "damage": roll("1d8")}\n')

    # 5. Generate TDD Stubs
    with open(os.path.join(base_dir, "tests", "test_combat.py"), "w", encoding="utf-8") as f:
        f.write(f'''from src.rulesets.{name}.resolvers.combat import resolve_attack

def test_resolve_attack():
    """Verify combat abstraction remains deterministic and LLM-free."""
    res = resolve_attack({{"attack_mod": 5}})
    assert "success" in res
    assert "damage" in res
''')

    # 6. Generate Builder Agent AI Prompt Payload (TODO.md)
    todo_code = f'''# {name} Conversion Manifest

<mission_brief>
    <objective>
        You are an autonomous Builder Agent. Your directive is to ingest a human-written Obsidian Vault TTRPG ruleset and translate it into this strict 3-tier Layer IV Cartridge.
    </objective>
    <execution_protocol>
        1. **DISCOVER**: Use `list_dir` and `view_file` to read the raw Obsidian Markdown files provided by the human.
        2. **SEMANTIC PASS**: Extract pure lore, world-building, and roleplay flavor tones. Write these directly into `knowledge/*.md`. Do NOT copy math charts into here.
        3. **TABULAR PASS**: Extract classes, races, items, and spells. Format these as strictly typed JSON arrays and write them to `data/*.json`. If a dataset exceeds 100 items, write a python tool to migrate it to SQLite `data/*.db` ensuring a `_meta` table exists.
        4. **EXECUTABLE PASS**: Translate dice math, saving throw thresholds, and combat damage equations into pure Python functions inside `resolvers/`.
        5. **MANIFEST WIRING**: After saving your files, you MUST use `replace_file_content` to update `manifest.json`. Map your new data files into the `"data_files"` dict, and toggle `"capabilities"` booleans to `true`.
        6. **TDD ENFORCEMENT**: Before declaring completion, you must write `pytest` unit tests in `tests/` for every resolver you created. Run `pytest src/rulesets/{name}/tests/`. You are NOT authorized to notify the user of completion if tests fail.
    </execution_protocol>
</mission_brief>
'''
    with open(os.path.join(base_dir, "TODO.md"), "w", encoding="utf-8") as f:
        f.write(todo_code)
        
    # Write a stub knowledge file
    with open(os.path.join(base_dir, "knowledge", "tone_guide.md"), "w", encoding="utf-8") as f:
        f.write(f"# Tone Guide: {name}\n\nEstablish the campaign vibe here.")

    print(f"\\n✅ Cartridge '{name}' successfully scaffolded!")
    print(f"\\nNext Steps:\\n1. Point a Builder Agent to '{base_dir}/TODO.md'\\n2. Provide the Builder Agent with the raw Obsidian Vault path.\\n3. Let it build.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold a new TTRPG Ruleset Cartridge.")
    parser.add_argument("--name", required=True, help="The formal name of the system (e.g., CyberpunkDNA)")
    args = parser.parse_args()
    scaffold_cartridge(args.name)
```

## Running the Bootstrap

From the root of your workspace:

```bash
python init_cartridge.py --name "CyberpunkDNA"
```

Once generated, point an AI coding assistant at the `src/rulesets/CyberpunkDNA/TODO.md` file. The file is formatted as an explicit machine-readable mission brief utilizing `<mission_brief>` and `<execution_protocol>` tags, guaranteeing the secondary LLM correctly navigates the Data Structure Matrix without human micromanagement.
