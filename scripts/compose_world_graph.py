"""
Derive an interactive knowledge graph of the world from the registry.

Usage (from the repo root):
    .\\venv\\Scripts\\python.exe scripts\\compose_world_graph.py --registry data\\showcase_registry.json

(data\\showcase_registry.json is the curated example world that ships with the
repo. Point --registry at your own working registry to graph your own world.)

The registry already holds a graph: every entity the pipeline created, its type
and gist, and the labelled edges it recorded while building. This renders that
into one self-contained HTML file — no CDN, no server, no model call, no quota.

Like the Timeline and the Stub Index this is a DERIVE path: a view over state
that must not vary. Same registry in, same page out.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.console import enable_safe_stdout
from layer5_dna_substrate.graph_view import build_graph, write_html


def main():
    parser = argparse.ArgumentParser(
        description="Render the registry as an interactive graph.")
    parser.add_argument("--registry", required=True, help="Path to the registry JSON")
    parser.add_argument("--out", default=os.path.join("graphify-out", "world-graph.html"),
                        help="Where to write the HTML (default: graphify-out/)")
    parser.add_argument("--title", default="Skarn - World Graph")
    parser.add_argument("--stats", action="store_true",
                        help="Report the graph shape, write nothing")
    args = parser.parse_args()

    registry_path = os.path.abspath(args.registry)
    if not os.path.isfile(registry_path):
        raise SystemExit(f"No registry at {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    graph = build_graph(data)

    types = {}
    statuses = {}
    for node in graph["nodes"]:
        types[node["type"]] = types.get(node["type"], 0) + 1
        statuses[node["status"]] = statuses.get(node["status"], 0) + 1

    print(f"{len(graph['nodes'])} entities, {len(graph['edges'])} relationships")
    print("  by status: " + ", ".join(
        f"{k} {v}" for k, v in sorted(statuses.items())))
    print("  by type:   " + ", ".join(
        f"{k} {v}" for k, v in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))))
    kinds = {}
    for edge in graph["edges"]:
        kinds[edge["kind"]] = kinds.get(edge["kind"], 0) + 1
    print("  by edge:   " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))

    if args.stats:
        return

    out_path = os.path.abspath(args.out)
    parent = os.path.dirname(out_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    report = write_html(data, out_path, title=args.title)
    size = os.path.getsize(out_path)
    print(f"\nwrote {report['path']} ({size / 1024:.0f} KB)")


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
