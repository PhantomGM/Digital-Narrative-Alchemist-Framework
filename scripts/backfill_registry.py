"""
Reconcile the registry against the vault, and derive the authoring worklist.

Usage (from the repo root):
    .\\venv\\Scripts\\python.exe scripts\\backfill_registry.py --registry data\\showcase_registry.json --vault "C:\\path\\to\\Vault"
    ... --apply                 write the harvested edges into the registry
    ... --apply --register-doctrines "Law of Utility" "Order of the Gate"

The registry records only the edges it created at generation time, so every
relationship the author wrote and every one a decoder left as bare prose is
invisible to context assembly. This finds them and writes them back.

No DNA and no model: a reconciliation between two things already on disk.
Canon pages are never modified — the only writes are to the registry's edge
store and to one derived worklist page.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.console import enable_safe_stdout
from common.paths import PathConfigError, resolve_vault_path
from layer5_dna_substrate.link_harvest import (
    apply_edges, candidate_entities, harvest_edges, load_pages,
    register_entities, render_worklist, unlinked_character_pairs,
)
from layer5_dna_substrate.registry import DNARegistry


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile the registry against the vault.")
    parser.add_argument("--registry", required=True)
    parser.add_argument("--vault", default=None,
                        help="Path to the vault (or set OBSIDIAN_VAULT_PATH)")
    parser.add_argument("--apply", action="store_true",
                        help="Write harvested edges into the registry")
    parser.add_argument("--kinds", default="wikilink,prose",
                        help="Which edge kinds to apply (default both)")
    parser.add_argument("--register-doctrines", nargs="*", metavar="NAME",
                        help="Register these named things as lore stubs")
    parser.add_argument("--page", default=os.path.join("Drafts", "Link Gaps.md"),
                        help="Vault-relative worklist page to derive")
    parser.add_argument("--no-page", action="store_true",
                        help="Skip writing the worklist page")
    args = parser.parse_args()

    try:
        vault = resolve_vault_path(args.vault)
    except PathConfigError as exc:
        raise SystemExit(f"{exc}\n  (pass --vault PATH)")

    registry_path = os.path.abspath(args.registry)
    if not os.path.isfile(registry_path):
        raise SystemExit(f"No registry at {registry_path}")

    registry = DNARegistry()
    registry.load_from_json(registry_path)
    pages = load_pages(vault)
    print(f"{len(pages)} content page(s), {len(registry._records)} record(s)\n")

    edges = harvest_edges(registry, pages)
    wiki = [e for e in edges if e["kind"] == "wikilink"]
    prose = [e for e in edges if e["kind"] == "prose"]
    print(f"unrecorded relationships: {len(edges)}"
          f"  ({len(wiki)} wikilinked, {len(prose)} prose-only)")
    for row in edges[:10]:
        print(f"   [{row['kind']:8}] {row['source'][:28]:28} -> "
              f"{row['target'][:28]:28} x{row['mentions']}")
    if len(edges) > 10:
        print(f"   ... and {len(edges) - 10} more")

    cands = candidate_entities(registry, pages)
    in_canon = [c for c in cands if c["canon_sources"]]
    print(f"\nnamed but unregistered candidates: {len(cands)}"
          f"  ({len(in_canon)} named in canon)")
    for row in in_canon[:12]:
        print(f"   {row['name'][:40]:40} <- {', '.join(row['canon_sources'][:2])}")

    pairs = unlinked_character_pairs(registry, pages)
    print(f"\ncharacters sharing a page with no link: {len(pairs)}")
    for row in pairs[:8]:
        print(f"   {row['a'][:26]:26} <-> {row['b'][:26]:26} "
              f"({row['weight']} shared page(s))")

    if args.apply:
        kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
        added = apply_edges(registry, edges, kinds)
        created = []
        if args.register_doctrines:
            wanted = set(args.register_doctrines)
            rows = [c for c in cands if c["name"] in wanted]
            # A name the detector missed is still registrable, but it must not
            # arrive without provenance: an unsourced stub shows up in the index
            # with a blank origin and no way back to the page that implied it.
            for name in sorted(wanted - {c["name"] for c in rows}):
                named_in = sorted(
                    stem for stem, page in pages.items()
                    if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", page["body"]))
                rows.append({
                    "name": name, "sources": named_in,
                    "canon_sources": [s for s in named_in
                                      if pages[s]["status"] == "canon"],
                })
            created = register_entities(registry, rows, "lore", pages)
        registry.save_to_json(registry_path)
        print(f"\napplied: {added} edge(s), {len(created)} stub(s) registered")
        print(f"saved: {registry_path}")
    else:
        print("\n(dry run -- pass --apply to write the registry)")

    if not args.no_page:
        out = os.path.join(vault, args.page)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(render_worklist(pairs, in_canon, edges))
        print(f"derived: {out}")


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
