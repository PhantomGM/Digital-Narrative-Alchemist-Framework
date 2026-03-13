import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.layer2_dna.generators.world import WorldDNAGenerator
from agents.layer2_dna.history_consensus import HistoryConsensusEngine
from agents.layer2_dna.lore_extractor import LoreExtractor
from agents.layer1_runtime.world_state import WorldStateKeeper
from agents.layer3_support.safety_governor import SafetyGovernor

async def run_pre_session_setup():
    load_dotenv()
    print("=== Initiating Pre-Session World Generation ===")
    
    # 1. Initialize Agents
    safety_governor = SafetyGovernor(campaign_tone="Dark Fantasy") # In real usage, wire ProfileManager here
    consensus_engine = HistoryConsensusEngine(safety_governor=safety_governor)
    lore_extractor = LoreExtractor()
    state_keeper = WorldStateKeeper()
    
    # 2. Generate Base World DNA
    print("\n[1/4] Generating Base World DNA...")
    world_generator = WorldDNAGenerator()
    raw_world_dna = world_generator.generate_dna()
    print(f"Generated raw DNA string length: {len(raw_world_dna)}")
    
    # 3. Decode the World DNA into a Profile (Mock decoded using a simple string for the test script)
    # Note: A real implementation would push raw_world_dna through decoder.py's World Prompt
    decoded_world_profile = f"A grim world of ancient ruins and burgeoning magic, defined by this DNA: {raw_world_dna[:100]}..."
    
    # 4. Run the History Consensus Engine ("Microscope" Style)
    print("\n[2/4] Running History Consensus Engine (Generating 2 Epochs)...")
    history_log = await consensus_engine.generate_history(decoded_world_profile, rounds=2)
    
    print("\n--- Generated Raw Narrative History ---")
    print(f"{history_log[:500]}\n...[Log Truncated]")
    
    # 5. Extract Structural Data (The "Crunch")
    print("\n[3/4] Extracting Structural Data Points (Crunch)...")
    extracted_json = await lore_extractor.extract_data(history_log)
    
    print("\n--- Extracted JSON Schema ---")
    print(extracted_json)
    
    # 6. Map to World State
    print("\n[4/4] Mapping Data to World State Keeper...")
    state_keeper.ingest_history_data(extracted_json)
    
    print("\n=== Pre-Session World Generation Complete ===")
    print("The World State Keeper is now seeded with empirical history and ready for SessionDirector handover.")

if __name__ == "__main__":
    asyncio.run(run_pre_session_setup())
