import sys
import os
import asyncio
import argparse
from typing import List

# Add src and project root to path for cross-script and package imports
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(script_dir) 
sys.path.append(os.path.abspath(os.path.join(script_dir, '../src')))
sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.forge import ProceduralForge
from layer5_dna_substrate.inheritance import InheritanceEngine
from layer5_dna_substrate.decoder import DNADecoder
from layer5_dna_substrate.expansion_manager import ExpansionManager
from layer1_core.multi_agent_coordinator import MultiAgentCoordinator
from common.console import enable_safe_stdout
from sync_to_obsidian import sync_registry_to_obsidian, resolve_vault_or_exit

async def main(limit: int = 5, vault: str = None):
    print("🎭 INITIALIZING MULTI-AGENT WORLD BIBLE COORDINATOR")

    # Resolve the sync destination before spending any API quota — the expansion
    # below is the expensive part, and it would be wasted if the vault is bad.
    vault_path = resolve_vault_or_exit(vault)

    # 1. Setup Framework
    registry = DNARegistry()
    
    # Load existing registry
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/dna_registry.json'))
    if os.path.exists(data_path):
        print(f"📂 Loading existing registry from {data_path}...")
        registry.load_from_json(data_path)
    
    if not registry._records:
        print("🌱 Registry is empty. Please run 'seed_to_bible_demo.py' first to create a seed world.")
        return

    forge = ProceduralForge()
    inheritance = InheritanceEngine(registry)
    decoder = DNADecoder()
    manager = ExpansionManager(registry, forge, inheritance, decoder)
    
    # 2. Setup Multi-Agent Coordinator
    coordinator = MultiAgentCoordinator(manager)
    
    # 3. Get stubs
    stubs = [uid for uid, rec in registry._records.items() if "stub" in rec.get("tags", [])]
    
    if not stubs:
        print("✅ No stubs found in the registry to expand.")
        return
    
    print(f"👥 Coordination Team ready. {len(stubs)} stubs detected. Assigning specialists...")
    
    # 4. Execute Parallel Expansion
    results = await coordinator.expand_stubs_parallel(stubs, limit=limit)
    
    # 5. Report and Save
    coordinator.generate_report(results)
    
    # Save registry
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
    os.makedirs(data_dir, exist_ok=True)
    registry.save_to_json(os.path.join(data_dir, "dna_registry.json"))
    
    # Sync to Obsidian
    print("🔄 Syncing team output to Obsidian vault...")
    sync_registry_to_obsidian(registry, vault_path)
    print("✨ Sync complete! Check your Obsidian vault for the new entries.")

if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    parser = argparse.ArgumentParser(description="Multi-Agent DNA Expansion Demo")
    parser.add_argument("--limit", type=int, default=5, help="Number of stubs to expand concurrently")
    parser.add_argument("--vault", default=None,
                        help="Obsidian vault to sync into (or set OBSIDIAN_VAULT_PATH)")
    args = parser.parse_args()

    asyncio.run(main(limit=args.limit, vault=args.vault))
