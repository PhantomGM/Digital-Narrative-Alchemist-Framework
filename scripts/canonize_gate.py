"""
Runs the Canonize Gate over a saved registry, then syncs drafts to the vault.

Usage (from the repo root):
    .\\venv\\Scripts\\python.exe scripts\\canonize_gate.py --registry world.json --vault "C:\\Users\\nickd\\Desktop\\World Builder"

    --registry   Path to a registry JSON (saved via DNARegistry.save_to_json)
    --vault      Path to the Obsidian world-bible vault (or set WORLD_VAULT_PATH)
    --force      Re-audit entities that already passed
    --skip-audit Skip the LLM audit; just sync current state as drafts
    --no-sync    Audit only; don't write to the vault

The audit step calls the ConsistencyAuditor (LLM, fail-closed), so API keys
from .env are required unless --skip-audit is given. Audit verdicts are saved
back into the registry JSON either way.
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.vault_adapter import VaultAdapter
from layer5_dna_substrate.context_assembler import ContextAssembler
from layer5_dna_substrate.canonize_gate import CanonizeGate
from layer5_dna_substrate.obsidian_sync import ObsidianSync


def main():
    parser = argparse.ArgumentParser(description="Audit decoded entities against canon and sync drafts to the vault.")
    parser.add_argument("--registry", required=True, help="Path to the registry JSON file")
    parser.add_argument("--vault", default=os.environ.get("WORLD_VAULT_PATH"),
                        help="Path to the Obsidian vault (default: WORLD_VAULT_PATH env var)")
    parser.add_argument("--force", action="store_true", help="Re-audit already-passed entities")
    parser.add_argument("--skip-audit", action="store_true", help="Skip the LLM audit step")
    parser.add_argument("--no-sync", action="store_true", help="Skip syncing drafts to the vault")
    args = parser.parse_args()

    if not args.vault:
        parser.error("--vault is required (or set WORLD_VAULT_PATH)")

    registry = DNARegistry()
    registry.load_from_json(args.registry)

    if not args.skip_audit:
        assembler = ContextAssembler(registry, VaultAdapter(args.vault))
        from layer3_operations.consistency_auditor import ConsistencyAuditor
        gate = CanonizeGate(registry, assembler, ConsistencyAuditor())
        reports = asyncio.run(gate.review_all(force=args.force))
        registry.save_to_json(args.registry)

        flagged = [r for r in reports if r["status"] in ("flagged", "unreviewed")]
        if flagged:
            print("\nNeeds the author's attention:")
            for report in flagged:
                print(f"  - {report['name'] or report['entity_id'][:8]} [{report['status']}]: "
                      f"{'; '.join(report['notes']) or 'no details'}")

    if not args.no_sync:
        counts = ObsidianSync(registry, args.vault).sync()
        print(f"\nDone. {counts['written']} drafts are in the vault awaiting review; "
              f"promote with the vault's 'canonize' operation.")


if __name__ == "__main__":
    main()
