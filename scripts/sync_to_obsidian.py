import os
import sys

# Add src and project root to path for cross-script and package imports
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(script_dir) 
sys.path.append(os.path.abspath(os.path.join(script_dir, '../src')))
sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.obsidian_sync import ObsidianSync

def sync_registry_to_obsidian(registry: DNARegistry, vault_path: str = None):
    """Syncs a given registry instance to an Obsidian vault."""
    if vault_path is None:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "C:\\Users\\nickd\\Desktop\\Hermes")
    
    print(f"🔄 Syncing registry to vault at {vault_path}...")
    syncer = ObsidianSync(registry, vault_path)
    syncer.sync()

def run_sync():
    # 1. Configuration
    registry_file = os.path.join(os.path.dirname(__file__), "../data/dna_registry.json")
    
    # 2. Initialize Registry
    registry = DNARegistry()
    if os.path.exists(registry_file):
        registry.load_from_json(registry_file)
    else:
        print(f"No registry found at {registry_file}. Please run a generator first (e.g., seed_to_bible_demo.py).")
        return

    # 3. Run Sync
    sync_registry_to_obsidian(registry)

if __name__ == "__main__":
    run_sync()
