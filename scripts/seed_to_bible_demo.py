import sys
import os
import json
import argparse

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
from common.console import enable_safe_stdout

def main():
    parser = argparse.ArgumentParser(description="Seed-to-Bible Workflow Demo")
    parser.add_argument("--seed-type", type=str, default="npc", help="Type of entity to seed (npc, location, item, faction)")
    parser.add_argument("--seed-prompt", type=str, default="", help="Optional specific prompt for the seed entity")
    args = parser.parse_args()

    print("🚀 Initializing Seed-to-Bible Workflow...")
    
    # 1. Setup Components
    registry = DNARegistry()
    forge = ProceduralForge()
    inheritance = InheritanceEngine(registry)
    decoder = DNADecoder()
    
    # The ExpansionManager ties it all together
    manager = ExpansionManager(registry, forge, inheritance, decoder)
    
    # 2. SEED: Create a starting entity
    print("\n--- SEED: Ensuring Linguistic Anchor ---")
    linguistic_elements = [id for id, rec in registry._records.items() if rec.get("type") == "linguistic"]
    if not linguistic_elements:
        l_dna = forge.synthesize_element("linguistic")
        l_pheno = decoder.decode_element(l_dna)
        l_id = registry.register_element(
            element_type="linguistic",
            raw_dna=l_dna["dna"],
            decoded_profile=l_pheno,
            name="World Phonetics",
            tags=["anchor", "root"]
        )
        print(f"Created Linguistic Anchor: {l_id}")
    
    print(f"\n--- SEED: Generating initial {args.seed_type.upper()} ---")
    
    # Use the seed prompt if provided
    context = {"additional_notes": args.seed_prompt} if args.seed_prompt else {}
    
    # Synthesize DNA
    dna_data = forge.synthesize_element(args.seed_type)
    
    # Decode to Phenotype
    phenotype = decoder.decode_element(dna_data, context=context)
    
    element_id = registry.register_element(
        element_type=args.seed_type,
        raw_dna=dna_data["dna"],
        decoded_profile=phenotype,
        name=manager._extract_name(phenotype),
        tags=["seed", "protagonist"]
    )
    
    print(f"Created Seed {args.seed_type.upper()}: {element_id}")
    print("--- FULL PHENOTYPE ---")
    print(phenotype)
    print("--- END PHENOTYPE ---")
    
    # 3. BLOOM: Parse for stubs
    print("\n--- BLOOM: Parsing for Unmade Connections ---")
    stubs = manager.parse_and_register_stubs(element_id, phenotype)
    
    if not stubs:
        print("No stubs found. (Check if the decoder is producing the '🔗 Unmade Connections' section)")
        # Save anyway so we can sync the seed
    else:
        print(f"Found {len(stubs)} stubs:")
        for sid in stubs:
            record = registry.get_element(sid)
            meta = record.get("stub_metadata", {})
            print(f"  - [{record['type']}] {meta['name']}: {meta['description']}")

        # 4. EXPAND: Pick one stub and expand it
        target_stub_id = stubs[0]
        print(f"\n--- EXPAND: Expanding stub {target_stub_id} ---")
        
        expanded_phenotype = manager.expand_stub(target_stub_id)
        
        print(f"Expanded Entity Profile:")
        print(expanded_phenotype[:500] + "...")
    
    # 5. VERIFY: Check graph for sideways consistency
    print("\n--- VERIFY: Relationship Graph ---")
    facts = registry.query_graph(element_id, depth=2)
    for fact in facts:
        print(f"  • {fact}")

    # 6. SAVE: Persist for Sync
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    os.makedirs(data_dir, exist_ok=True)
    registry.save_to_json(os.path.join(data_dir, "dna_registry.json"))
    print(f"\nRegistry saved. Run 'python scripts/sync_to_obsidian.py --vault <path>' to export to your World Bible.")

if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
