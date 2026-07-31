"""
Compose thin pages for stubs that canon already fully describes — no DNA, no LLM.

Usage (from the repo root):
    # Triage: which stubs are compose-ready vs need a real decode
    ... compose_from_canon.py --registry world.json --vault "C:\\...\\World Builder" --triage

    # Compose one named stub into a draft page and sync it
    ... compose_from_canon.py --registry world.json --vault "..." --compose "The Bastion of the Unwavering Word"

    # Compose every compose-ready stub
    ... compose_from_canon.py --registry world.json --vault "..." --compose-all

Composed pages are drafts, filed to their type's folder, marked audit: composed.
They invent nothing; the author expands or canonizes them.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.canon_composer import CanonComposer
from layer5_dna_substrate.obsidian_sync import ObsidianSync
from common.console import enable_safe_stdout


def main():
    ap = argparse.ArgumentParser(description="Compose stub pages from canon (no DNA).")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--vault", default=os.environ.get("WORLD_VAULT_PATH"))
    ap.add_argument("--triage", action="store_true", help="Report compose-ready vs generate for all stubs")
    ap.add_argument("--compose", metavar="NAME", help="Compose one named stub")
    ap.add_argument("--compose-all", action="store_true", help="Compose every compose-ready stub")
    args = ap.parse_args()
    if not args.vault:
        ap.error("--vault is required (or set WORLD_VAULT_PATH)")

    registry = DNARegistry()
    registry.load_from_json(args.registry)
    composer = CanonComposer(registry)

    if args.triage:
        rows = composer.triage_all()
        ready = [r for r in rows if r["strategy"] == "compose"]
        print(f"{len(rows)} stubs — {len(ready)} compose-ready, {len(rows) - len(ready)} need a decode.\n")
        print("COMPOSE-READY (canon already describes these — no DNA needed):")
        for r in ready:
            print(f"  [{r['type']:>9}] {r['name']:38} {r['rich_blocks']} rich / "
                  f"{r['mentions']} mentions across {', '.join(r['sources'][:3])}")
        print("\n(everything else needs a real decode; run with --triage-verbose to list)")
        if os.environ.get("TRIAGE_VERBOSE"):
            print("\nNEEDS A DECODE:")
            for r in rows:
                if r["strategy"] != "compose":
                    print(f"  [{r['type']:>9}] {r['name']:38} {r['mentions']} mention(s)")
        return

    to_compose = []
    if args.compose:
        rec = registry.find_by_name(args.compose)
        if not rec:
            ap.error(f"No stub named {args.compose!r}")
        to_compose = [rec["id"]]
    elif args.compose_all:
        to_compose = [r["id"] for r in registry._records.values() if "stub" in r.get("tags", [])
                      if composer.assess(r)["strategy"] == "compose"]
    else:
        ap.error("Pass --triage, --compose NAME, or --compose-all")

    composed = []
    for sid in to_compose:
        name = registry.get_element(sid).get("name")
        if composer.compose_into_record(sid):
            composed.append(name)
            print(f"  composed: {name}")
        else:
            print(f"  skipped (canon too thin): {name}")

    if composed:
        registry.save_to_json(args.registry)
        counts = ObsidianSync(registry, args.vault).sync()
        print(f"\n{len(composed)} composed page(s) synced. {counts}")


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
