"""
Sync a DNA registry into an Obsidian vault.

Usage:
    python scripts/sync_to_obsidian.py --vault "/path/to/vault" [--registry data/dna_registry.json]

The vault path must be given explicitly (--vault) or via OBSIDIAN_VAULT_PATH.
This script deliberately refuses to guess it. A hardcoded machine-specific
default used to live here, and when the project was run under WSL that Windows
path ("C:\\Users\\...\\Hermes") was not a path at all — POSIX does not treat "\\"
as a separator, so the whole string became a single directory name, with ":" and
"\\" mapped into the U+F000 private-use range. The result was an entire generated
vault silently stranded inside the repository under a mangled filename.

Validation lives in common.paths.resolve_vault_path(), shared with the other
call sites that had the same bug. See src/common/paths.py.
"""

import argparse
import os
import sys

# Add src and project root to path for cross-script and package imports
script_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(script_dir)
sys.path.append(os.path.abspath(os.path.join(script_dir, "..", "src")))
sys.path.append(os.path.abspath(os.path.join(script_dir, "..")))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.obsidian_sync import ObsidianSync
from common.paths import PathConfigError, resolve_vault_path
from common.console import enable_safe_stdout

DEFAULT_REGISTRY = os.path.abspath(os.path.join(script_dir, "..", "data", "dna_registry.json"))


def resolve_vault_or_exit(explicit: str = None, create: bool = False) -> str:
    """CLI wrapper: turn a PathConfigError into a clean exit rather than a traceback."""
    try:
        return resolve_vault_path(explicit, create=create)
    except PathConfigError as exc:
        raise SystemExit(f"{exc}\n  (pass --vault PATH, or --create to make it)")


def sync_registry_to_obsidian(registry: DNARegistry, vault_path: str = None, create: bool = False):
    """Syncs a given registry instance to an Obsidian vault."""
    vault_path = resolve_vault_or_exit(vault_path, create=create)
    print(f"Syncing registry to vault at {vault_path} ...")
    return ObsidianSync(registry, vault_path).sync()


def run_sync(argv=None):
    ap = argparse.ArgumentParser(description="Sync a DNA registry into an Obsidian vault.")
    ap.add_argument("--vault", default=None,
                    help="Path to the Obsidian vault (or set OBSIDIAN_VAULT_PATH)")
    ap.add_argument("--registry", default=DEFAULT_REGISTRY,
                    help=f"Registry JSON to sync (default: {DEFAULT_REGISTRY})")
    ap.add_argument("--create", action="store_true",
                    help="Create the vault directory if it does not exist")
    args = ap.parse_args(argv)

    # Validate the destination BEFORE loading, so a bad path fails fast.
    vault_path = resolve_vault_or_exit(args.vault, create=args.create)

    registry_file = os.path.abspath(args.registry)
    if not os.path.exists(registry_file):
        raise SystemExit(
            f"No registry found at {registry_file}.\n"
            "  Run a generator first (e.g. scripts/seed_to_bible_demo.py)."
        )

    registry = DNARegistry()
    registry.load_from_json(registry_file)
    return sync_registry_to_obsidian(registry, vault_path)


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    run_sync()
