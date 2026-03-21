"""
Pre-Session Setup Pipeline (Session 0)

This module implements the AI Game Master's world bootstrapping sequence.
It runs once before the first session to generate the World DNA, consensus
history, and seed the World State Keeper with foundational lore. After
Session 0, the world state is updated incrementally through gameplay —
this pipeline is not re-run.

Pipeline:
    1. Generate World DNA via WorldDNAGenerator
    2. Decode World DNA into a narrative profile (via DNADecoder)
    3. Run the History Consensus Engine ("Microscope"-style epoch generation)
    4. Extract structural data (factions, NPCs, locations) from raw history
    5. Seed the World State Keeper with extracted facts
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure the project src directory is in the Python path when run as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

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
