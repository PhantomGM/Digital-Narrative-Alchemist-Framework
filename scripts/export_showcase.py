"""
Export a curated example registry for the public repository.

Usage (from the repo root):
    .\\venv\\Scripts\\python.exe scripts\\export_showcase.py --registry data\\world_builder_registry.json --out data\\showcase_registry.json --names-file data\\showcase_names.txt --neighbours

The working registry is a live world and is not tracked. This carves a fixed
slice out of it so the repository still ships example data — enough for the
derivers, the graph view and the tests to run against a real, populated world.

Selection is by name and deliberately manual: what to show is an authorial
choice, not something a heuristic should make.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.console import enable_safe_stdout
from layer5_dna_substrate.showcase import build_showcase, summarise


def main():
    parser = argparse.ArgumentParser(
        description="Carve a curated example registry out of a working one.")
    parser.add_argument("--registry", required=True, help="The working registry")
    parser.add_argument("--out", required=True, help="Where to write the slice")
    parser.add_argument("--names", nargs="*", default=[], metavar="NAME")
    parser.add_argument("--names-file", default=None,
                        help="One entity name per line; # comments allowed")
    parser.add_argument("--neighbours", action="store_true",
                        help="Also include whatever the selection points at")
    parser.add_argument("--drop", nargs="*", default=[], metavar="FIELD",
                        help="Record fields to strip, e.g. phenotype summary")
    args = parser.parse_args()

    names = list(args.names)
    if args.names_file:
        with open(args.names_file, "r", encoding="utf-8") as handle:
            names += [line.split("#")[0].strip() for line in handle]
    names = [n for n in names if n]
    if not names:
        raise SystemExit("No names given (use --names or --names-file)")

    source = os.path.abspath(args.registry)
    if not os.path.isfile(source):
        raise SystemExit(f"No registry at {source}")
    with open(source, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    try:
        showcase = build_showcase(data, names,
                                  include_neighbours=args.neighbours,
                                  drop_fields=set(args.drop))
    except KeyError as exc:
        raise SystemExit(str(exc))

    report = summarise(showcase)
    print(f"selected {len(names)} name(s)"
          f"{' + neighbours' if args.neighbours else ''}"
          f" -> {report['records']} record(s), {report['edge_items']} edge item(s)")
    print("  types: " + ", ".join(
        f"{k} {v}" for k, v in sorted(report["types"].items(),
                                      key=lambda kv: (-kv[1], kv[0]))))
    print(f"  prose carried: {report['prose_chars'] / 1024:.0f} KB")

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(showcase, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print(f"\nwrote {out} ({os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
