import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.orchestrator import Orchestrator
from agents.layer1_runtime.narrative_weaver import NarrativeWeaver
from agents.layer1_runtime.world_state import WorldStateKeeper
from agents.layer2_dna.forge import ProceduralForge
from agents.layer2_dna.decoder import DNADecoder
from agents.layer2_dna.registry import DNARegistry
from agents.layer2_dna.inheritance import InheritanceEngine
from rulesets.one_page_5e.arbiter import GameSystemArbiter as OnePage5eArbiter
from rulesets.coin_flip.arbiter import GameSystemArbiter as CoinFlipArbiter
from agents.layer1_runtime.session_director import SessionDirector

# The freestanding test_input function has been removed.
# The SessionDirector now handles this logic internally via advance_scene.

async def main():
    print("=== Initializing Digital Narrative Alchemist (DNA) Framework ===\n")
    
    # Initialize Core Agents
    orchestrator = Orchestrator()
    weaver = NarrativeWeaver()
    state_keeper = WorldStateKeeper()
    
    # Initialize Layer II Agents
    forge = ProceduralForge()
    decoder = DNADecoder()
    registry = DNARegistry()
    inheritance_engine = InheritanceEngine(registry)
    
    one_page_5e = OnePage5eArbiter()
    coin_flip = CoinFlipArbiter()

    # Initialize Session Director (The Hub)
    director = SessionDirector(orchestrator, weaver, state_keeper, registry)
    
    # Register a PC for the Arc Tracker & Profile Manager
    director.arc_tracker.register_pc("PC_01_Fighter", ["Become a famous hero", "Find lost brother"], ["Reckless in combat"])
    director.profile_manager.register_player(
        "PC_01_Fighter", 
        lines_and_veils=["Arachnophobia: Absolutely no spiders or spider-like monsters."], 
        preferences="Likes tactical combat."
    )

    location_tag = "Goblin Cave"

    print("\n--- Phase 3: Layer I Core Loop (Session Director Test) ---")
    print("Loading One Page 5e Cartridge...")
    orchestrator.load_ruleset(one_page_5e)
    
    # Frame scene explicitly
    print(director.frame_scene(location_tag))
    
    # Force the pacing to tense so we can guarantee we see a hazard trigger on the first or second loop
    director.pacing_level = "calm" 

    prose_output = await director.advance_scene(
        "PC_01_Fighter", 
        "I carefully inspect the slippery floor, watching out for the giant venomous spiders that live here.", 
        location_tag
    )
    print(f"\nNarrativeWeaver Output:\n> \"{prose_output}\"")
    
    print("\nHot-Swapping to Coin Flip Cartridge...")
    orchestrator.load_ruleset(coin_flip)
    print(f"Loaded ruleset: {orchestrator.ruleset_cartridge.system_name}\n")
    
    prose_output_2 = await director.advance_scene("PC_01_Fighter", "I attack the goblin with my longsword!", location_tag)
    print(f"\nNarrativeWeaver Output:\n> \"{prose_output_2}\"")
    
    # Phase 4: Test Layer II: PCG Substrate & Inheritance Engine
    print("\n--- Phase 4: Testing Layer II (Inheritance Engine) ---")
    
    # 1. Generate the Faction (The Parent)
    print("Generating Parent Faction...")
    faction_data = forge.synthesize_element("faction")
    context_faction = {"setting": "A bustling desert market", "theme": "A subterranean smuggling ring"}
    decoded_faction = decoder.decode_element(faction_data, context=context_faction)
    
    faction_id = registry.register_element(
        element_type="faction", 
        raw_dna=faction_data['dna'], 
        decoded_profile=decoded_faction, 
        tags=["smugglers", "desert"]
    )
    print(f"Faction Registered! (ID: {faction_id})")
    
    # 2. Extract Constraints for a Child NPC
    print("\nCompiling inheritance constraints for a new child NPC...")
    constraints = inheritance_engine.compile_constraints([faction_id])
    print(f"Constraints Compiled! Length: {len(constraints)} characters.")

    # 3. Generate the NPC (The Child), passing constraints to Forge and Decoder
    print("\nGenerating Child NPC with inherited constraints...")
    npc_data = forge.synthesize_element("npc", constraint_package=constraints)
    
    context_npc = {"setting": "A bustling desert market", "role_needed": "A suspicious merchant who belongs to the generated faction"}
    decoded_npc = decoder.decode_element(npc_data, context=context_npc)
    print("\nDecoded NPC Profile (Inherited Traits):")
    print(decoded_npc[:400] + "...\n[Profile Truncated for Output]") 

    npc_id = registry.register_element(
        element_type="npc", 
        raw_dna=npc_data['dna'], 
        decoded_profile=decoded_npc, 
        tags=["merchant", "desert"]
    )
    
    # 4. Link them in the graph
    registry.link_elements(faction_id, npc_id, "parent")
    
    print("\nVerifying Links in Registry:")
    print(f"NPC Links: {registry.get_links(npc_id)}")

    print("\n=== DNA Framework Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
