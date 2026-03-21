import os
import pathlib
import re

ROOT_PATH = r"C:\Users\nickd\Desktop\OC2\DNA Brain\Brain Structure"

# Analyze carefully: The new architecture nodes to be expanded, heavily interlinked 
# via Dataview inline fields to guarantee Obsidian graph engine parsing.
NEW_TOPOLOGY = {
    "Layer_I_Core": {
        "_content": """> [!info] Status: Planned

Parent:: [[Brain Structure]]
Dependencies:: None
Tool_Use:: None

# Layer I: Core

The foundational operational layer of the AI Game Master.

<!-- folder_overview -->
""",
        "Orchestrator": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_I_Core]]
Dependencies:: [[World_State_Keeper]], [[Game_System_Arbiter]]
Tool_Use:: [[resolve_action]], [[query_data]]

# Orchestrator

The master routing hub. Intercepts player input, classifies intents, and decides if a mechanical rule needs to be invoked.
"""
        },
        "World_State_Keeper": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_I_Core]]
Dependencies:: [[Event_Ledger]]
Tool_Use:: [[read_state]], [[update_state]]

# World State Keeper

Tracks the authoritative present reality using an Event Ledger. Ensures all agents operate on the exact same micro-state canon.
"""
        }
    },
    "Layer_II_Narrative": {
        "_content": """> [!info] Status: Planned

Parent:: [[Brain Structure]]
Dependencies:: None
Tool_Use:: None

# Layer II: Narrative

Responsible for the prose generation and canonical event tracking.

<!-- folder_overview -->
""",
        "Narrative_Weaver": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_II_Narrative]]
Dependencies:: [[Event_Ledger]], [[World_State_Keeper]]
Tool_Use:: [[generate_prose]]

# Narrative Weaver

Translates raw state changes, decoded DNA, and mechanical outcomes into vivid, engaging prose for the players.
"""
        },
        "Event_Ledger": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_II_Narrative]]
Dependencies:: None
Tool_Use:: [[append_event]], [[get_history]]

# Event Ledger

The append-only log of all micro-state changes, serving as the ground truth for narrative generation and auditing.
"""
        }
    },
    "Layer_III_Operations": {
        "_content": """> [!info] Status: Planned

Parent:: [[Brain Structure]]
Dependencies:: None
Tool_Use:: None

# Layer III: Operations

Manages the pacing, safety, NPCs, and memory of the ongoing session.

<!-- folder_overview -->
""",
        "Session_Director": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_III_Operations]]
Dependencies:: [[NPC_Engines]], [[Safety_Governor]], [[Narrative_Weaver]]
Tool_Use:: [[frame_scene]], [[trigger_encounter]]

# Session Director

Controls structural pacing, scene framing, and encounter injection. Coordinates sub-agents through a parallel async pipeline.
"""
        },
        "NPC_Engines": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_III_Operations]]
Dependencies:: [[Memory_Manager]], [[Event_Ledger]]
Tool_Use:: [[generate_dialogue]], [[evaluate_motivation]]

# NPC Engines

Autonomous sub-routines that drive the behavior, dialogue, and goals of non-player characters within the scene.
"""
        },
        "Safety_Governor": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_III_Operations]]
Dependencies:: None
Tool_Use:: [[screen_input]], [[audit_output]]

# Safety Governor

Pre-screens input and analyzes output to enforce campaign bounds, Lines & Veils, and tonal consistency.
"""
        },
        "Memory_Manager": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_III_Operations]]
Dependencies:: [[Event_Ledger]]
Tool_Use:: [[compress_context]], [[retrieve_memory]]

# Memory Manager

Handles context window optimization, summarizing past events, and retrieving relevant lore to keep the LLM within token limits.
"""
        }
    },
    "Layer_IV_Rules": {
        "_content": """> [!info] Status: Planned

Parent:: [[Brain Structure]]
Dependencies:: None
Tool_Use:: None

# Layer IV: Rules

The modular game-system cartridges handling mechanics and tabular data lookup.

<!-- folder_overview -->
""",
        "Game_System_Arbiter": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_IV_Rules]]
Dependencies:: [[Resolvers]], [[Adapters]]
Tool_Use:: [[route_intent]]

# Game System Arbiter

The bridge interface. The Orchestrator calls this node to resolve mechanical intents by routing to specific Resolvers.
"""
        },
        "Resolvers": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_IV_Rules]]
Dependencies:: None
Tool_Use:: [[roll_dice]], [[calculate_damage]]

# Resolvers

Pure deterministic Python functions handling combat, dice math, and state mutation. Strictly LLM-free execution.
"""
        },
        "Adapters": {
            "_content": """> [!info] Status: Planned

Parent:: [[Layer_IV_Rules]]
Dependencies:: None
Tool_Use:: [[parse_tabular]], [[format_output]]

# Adapters

Translation layers that format tabular JSON/SQLite data into LLM-friendly structures or route API calls to specific cartridges.
"""
        }
    }
}

def build_node(path: pathlib.Path, name: str, node_data: dict, is_root: bool = False):
    """Recursively builds the folder notes structure with Dataview inline links."""
    
    current_dir = path
    if not is_root:
        current_dir = path / name
        current_dir.mkdir(parents=True, exist_ok=True)
    
    note_name = f"{current_dir.name}.md"
    note_path = current_dir / note_name
    
    if not is_root:
        content = node_data.get("_content", "")
        # Evaluate: Overwrite note to ensure new Dataview inline fields are applied.
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    # Recursively build children
    for child_name, child_data in node_data.items():
        if child_name == "_content":
            continue
        build_node(current_dir, child_name, child_data, is_root=False)

def update_root_index(root_path: pathlib.Path):
    """Safely inject links into the root index using regex to prevent overwriting."""
    index_path = root_path / f"{root_path.name}.md"
    
    links_to_add = [
        "[[Layer_I_Core]]",
        "[[Layer_II_Narrative]]",
        "[[Layer_III_Operations]]",
        "[[Layer_IV_Rules]]"
    ]
    
    if not index_path.exists():
        return
        
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find links we don't already have
    missing_links = [link for link in links_to_add if link not in content]
    
    if missing_links:
        # Evaluate: If there's an existing 'Expanded Architecture' header, append there.
        # Otherwise, add the header to the bottom of the file.
        header_pattern = r"(## Expanded Architecture Layers\n)"
        if re.search(header_pattern, content):
            replacement = r"\1" + "\n".join([f"- {link}" for link in missing_links]) + "\n"
            content = re.sub(header_pattern, replacement, content)
        else:
            content += "\n\n## Expanded Architecture Layers\n"
            for link in missing_links:
                content += f"- {link}\n"
                
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)

def main():
    root = pathlib.Path(ROOT_PATH)
    
    print(f"Executing Dataview-Linked Obsidian Vault Expansion at: {root}")
    
    root.mkdir(parents=True, exist_ok=True)
    build_node(root, root.name, NEW_TOPOLOGY, is_root=True)
    update_root_index(root)
    
    print("Vault expansion completed successfully.")
    print("All nodes interlinked via Dataview inline fields.")

if __name__ == "__main__":
    main()
