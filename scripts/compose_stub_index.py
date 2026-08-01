"""
Derive the pending-stub listing into the vault.

Usage (from the repo root):
    .\\venv\\Scripts\\python.exe scripts\\compose_stub_index.py --registry data\\world_builder_registry.json --vault "C:\\path\\to\\Vault"

Stubs are the entities an existing page has named without describing. They are not
written as pages — the sync holds them back, since a stub is a name plus a reason
and nothing else — so no vault search can find them. This derives them instead.

No DNA and no model: a view over registry state, idempotent, safe to re-run.
Only the '## Pending' section of the target page is rewritten.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.console import enable_safe_stdout
from common.paths import PathConfigError, resolve_vault_path
from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.stub_index import StubIndex


def main():
    parser = argparse.ArgumentParser(
        description="Derive the pending-stub listing into the vault.")
    parser.add_argument("--registry", required=True, help="Path to the registry JSON")
    parser.add_argument("--vault", default=None,
                        help="Path to the vault (or set OBSIDIAN_VAULT_PATH)")
    parser.add_argument("--page", default=os.path.join("Drafts", "Unmade Stubs.md"),
                        help="Vault-relative page to write")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be written, change nothing")
    args = parser.parse_args()

    enable_safe_stdout()

    try:
        vault = resolve_vault_path(args.vault)
    except PathConfigError as exc:
        raise SystemExit(f"{exc}\n  (pass --vault PATH)")

    registry_path = os.path.abspath(args.registry)
    if not os.path.isfile(registry_path):
        raise SystemExit(f"No registry at {registry_path}")

    registry = DNARegistry()
    registry.load_from_json(registry_path)

    index = StubIndex(registry, vault, page=args.page)
    rows = index.pending()

    print(f"{len(rows)} pending stub(s)")
    for ptype, entries in sorted(index.group(rows).items(),
                                 key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"   {ptype:14} {len(entries)}")

    if args.dry_run:
        print(f"\n(dry run — would rewrite the Pending section of {args.page})")
        return

    report = index.write(rows)
    action = "created" if report["created"] else "updated"
    print(f"\n{action}: {os.path.join(vault, args.page)}")


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
