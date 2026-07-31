"""
Derive the master chronology from canon and rewrite Timeline.md's Chronology table.

Usage (from the repo root):
    .\\venv\\Scripts\\python.exe scripts\\compose_timeline.py --vault "C:\\...\\World Builder"

    --vault    Path to the Obsidian vault (or set WORLD_VAULT_PATH)
    --registry Optional registry JSON, to also pull events from record `events` lists
    --seed     One-time: ingest the current Timeline.md table into the event store
    --dry-run  Report what would change without writing

The event store lives at <vault>/History/timeline_events.json. On first use, run
with --seed to populate it from the hand-built table; thereafter append events to
the store (or to entity records) and re-run to regenerate the table.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from layer5_dna_substrate.timeline_composer import TimelineComposer
from common.console import enable_safe_stdout


def main():
    ap = argparse.ArgumentParser(description="Derive Timeline.md's Chronology from dated canon events.")
    ap.add_argument("--vault", default=os.environ.get("WORLD_VAULT_PATH"))
    ap.add_argument("--registry", default=None)
    ap.add_argument("--seed", action="store_true", help="Ingest the current table into the event store")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.vault:
        ap.error("--vault is required (or set WORLD_VAULT_PATH)")

    store = os.path.join(args.vault, "History", "timeline_events.json")
    composer = TimelineComposer(args.vault, store_path=store)

    registry = None
    if args.registry:
        from layer5_dna_substrate.registry import DNARegistry
        registry = DNARegistry()
        registry.load_from_json(args.registry)

    seeded_events = None
    if args.seed or not os.path.isfile(store):
        seeded_events = composer.seed_from_timeline_md()
        if not args.dry_run:
            with open(store, "w", encoding="utf-8", newline="\n") as f:
                json.dump(seeded_events, f, indent=2, ensure_ascii=False)
        print(f"Seeded {len(seeded_events)} events from the current table"
              + ("" if args.dry_run else " into the store."))

    if seeded_events is not None:
        # Use the just-seeded events (held in memory so --dry-run writes nothing),
        # unioned with any events declared on registry records.
        events = list(seeded_events)
        if registry is not None:
            seen = {(e.get("date_label", "").strip(), e.get("event", "").strip()) for e in events}
            for rec in registry._records.values():
                for ev in rec.get("events", []) or []:
                    ev = dict(ev); ev.setdefault("sources", f"[[{rec.get('name')}]]")
                    if (ev.get("date_label", "").strip(), ev.get("event", "").strip()) not in seen:
                        events.append(ev)
    else:
        events = composer.load_events(registry=registry)
    conflicts = composer.detect_conflicts(events)

    print(f"\n{len(events)} dated events collected.")
    if conflicts:
        print("Conflicts / quality flags:")
        for c in conflicts:
            print(f"  - {c}")
    else:
        print("No conflicts.")

    print("\nDerived chronology:")
    print(composer.render_chronology(events))

    if args.dry_run:
        print("\n[dry-run] Timeline.md not modified.")
    else:
        report = composer.write_timeline(events)
        print(f"\nWrote {report['events']} rows into Timeline.md's Chronology section.")


if __name__ == "__main__":
    # Unencodable characters must degrade, not crash: a piped
    # stdout on Windows is cp1252 and this output is not ASCII.
    enable_safe_stdout()
    main()
