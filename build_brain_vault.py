import os
import pathlib

ROOT_PATH = r"C:\Users\nickd\Desktop\OC2\DNA Brain\Brain Structure"

# Evaluate the DNA Framework to map the cognitive architecture for Obsidian Folder Notes.
# analyze carefully the folder-to-note mapping required by the plugin.
BRAIN_TOPOLOGY = {
    "_content": """# The DNA Brain

Welcome to the cognitive architecture of the Digital Narrative Alchemist (DNA).
This knowledge graph represents the deterministic multi-agent topology of the AI Game Master.

## Neural Pathways
- [[Layer_I_Core_Runtime]]
- [[Layer_II_DNA_Substrate]]
- [[Layer_III_Support]]
- [[Layer_IV_Cartridges]]
""",
    "Layer_I_Core_Runtime": {
        "_content": """# Layer I: Core Runtime Intelligence

The active, real-time "brain" of the AI GM. These agents manage session flow, pacing, and the authoritative truth of the game world.

**Neural Nodes:**
- [[Orchestrator]]
- [[Session_Director]]
- [[World_State_Keeper]]
- [[Narrative_Weaver]]
- [[Simulators]]
""",
        "Orchestrator": {
            "_content": """# Orchestrator

The master routing hub. Intercepts player input, classifies intents, and decides if a mechanical rule from [[Layer_IV_Cartridges]] needs to be invoked, or if the action can be resolved natively by the [[Narrative_Weaver]]."""
        },
        "Session_Director": {
            "_content": """# Session Director

Controls structural pacing, scene framing, and encounter injection. Coordinates sub-agents through a parallel async pipeline, invoking the [[Safety_Governor]] and [[Orchestrator]] simultaneously."""
        },
        "World_State_Keeper": {
            "_content": """# World State Keeper

Tracks the authoritative present reality using an Event Ledger. Ensures all agents, including the [[Consistency_Auditor]], operate on the exact same micro-state canon."""
        },
        "Narrative_Weaver": {
            "_content": """# Narrative Weaver

Translates raw state changes, decoded DNA, and mechanical outcomes into vivid, engaging prose for the players."""
        },
        "Simulators": {
            "_content": """# Simulators

Autonomous background agents (Faction, Environment, Encounter) that inject dynamic hazards and macro-events into the world based on the [[Session_Director]]'s pacing algorithms."""
        }
    },
    "Layer_II_DNA_Substrate": {
        "_content": """# Layer II: DNA / PCG Substrate

The procedural engine. Generates raw world elements (Genotypes) and translates them into rich narrative content (Phenotypes) via LLM invocation.

**Neural Nodes:**
- [[Procedural_Forge]]
- [[DNA_Decoder]]
- [[DNA_Registry]]
- [[Inheritance_Engine]]
""",
        "Procedural_Forge": {
            "_content": """# Procedural Forge

The master builder. Routes `synthesize_element` calls to specific Python generators to produce deterministic DNA strings."""
        },
        "DNA_Decoder": {
            "_content": """# DNA Decoder

Auto-loads `.md` prompts to translate raw DNA strings into evocative, playable profiles, escaping syntax via Langchain workflows."""
        },
        "DNA_Registry": {
            "_content": """# DNA Registry

Graph-augmented database mapping DNA strings to decoded phenotypes. Serves queries for the [[Inheritance_Engine]] using relationship labels and BFS traversal."""
        },
        "Inheritance_Engine": {
            "_content": """# Inheritance Engine

Resolves Multi-Directional constraints (Up, Down, Sideways) by analyzing the [[DNA_Registry]] graph to enforce contextual logic on newly generated DNA."""
        }
    },
    "Layer_III_Support": {
        "_content": """# Layer III: Support Boundaries

Middleware guardrails ensuring safe, logical, and tonally consistent operation across the cognitive graph.

**Neural Nodes:**
- [[Consistency_Auditor]]
- [[Safety_Governor]]
- [[Chronicler]]
""",
        "Consistency_Auditor": {
            "_content": """# Consistency Auditor (Patch Agent)

Intercepts output from the [[Narrative_Weaver]]. If an impossibility is detected against the [[World_State_Keeper]], it surgically patches the localized text to prevent infinite rollback loops."""
        },
        "Safety_Governor": {
            "_content": """# Safety Governor

Pre-screens input and analyzes output to enforce campaign bounds, Lines & Veils, and tone using parallel execution with the [[Session_Director]]."""
        },
        "Chronicler": {
            "_content": """# Chronicler

Background agent that compresses the Event Ledger into dense factual summaries to maintain the context window budget over long sessions."""
        }
    },
    "Layer_IV_Cartridges": {
        "_content": """# Layer IV: Modular Game-System Cartridges

Swappable logic cartridges governed by the `ruleset_ingestion_blueprint.md`. They dictate all hard-coded TTRPG mathematics and semantics.

**Neural Nodes:**
- [[Game_System_Arbiter]]
- [[Resolvers]]
- [[Tabular_Data]]
- [[Semantic_Knowledge]]
""",
        "Game_System_Arbiter": {
            "_content": """# Game System Arbiter

The bridge interface. The [[Orchestrator]] calls this node to resolve mechanical intents, query [[Tabular_Data]], or fetch [[Semantic_Knowledge]]."""
        },
        "Resolvers": {
            "_content": """# Executable Resolvers

Pure deterministic Python functions handling combat, dice math, and state mutation. Strictly LLM-free execution."""
        },
        "Tabular_Data": {
            "_content": """# Tabular Data

Queryable, structured datasets (items, spells, monster stat blocks) stored in JSON or SQLite. Used strictly for mechanical lookup."""
        },
        "Semantic_Knowledge": {
            "_content": """# Semantic Knowledge

Pure flavor, world lore, and roleplay rules written in Markdown. Sourced directly into the LLM context window by the [[Narrative_Weaver]] and [[Orchestrator]]."""
        }
    }
}


def build_node(path: pathlib.Path, name: str, node_data: dict, is_root: bool = False):
    """Recursively builds the folder notes structure."""
    
    # Analyze carefully: Create the directory for this node unless it's the root placeholder
    current_dir = path
    if not is_root:
        current_dir = path / name
        current_dir.mkdir(parents=True, exist_ok=True)
    
    # Evaluate the Folder Note Plugin requirement: note name must strictly match folder name.
    # For the root, the name is 'Brain Structure' based on the specified path.
    note_name = f"{current_dir.name}.md"
    note_path = current_dir / note_name
    
    # Extract the markdown content
    content = node_data.get("_content", f"# {name}\n\nEmpty node.")
    
    # Write the Folder Note
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Recursively build children
    for child_name, child_data in node_data.items():
        if child_name == "_content":
            continue
        build_node(current_dir, child_name, child_data, is_root=False)

def main():
    root = pathlib.Path(ROOT_PATH)
    
    print(f"Executing Obsidian Folder Notes Vault Construction at: {root}")
    
    # Create the root vault folder if it doesn't exist
    root.mkdir(parents=True, exist_ok=True)
    
    # Build the topology (treating the TARGET structure as the root node)
    build_node(root, root.name, BRAIN_TOPOLOGY, is_root=True)
    
    print("Vault construction completed successfully.")
    print("Graph links, directories, and Folder Notes strictly adhere to plugin requirements.")

if __name__ == "__main__":
    main()
