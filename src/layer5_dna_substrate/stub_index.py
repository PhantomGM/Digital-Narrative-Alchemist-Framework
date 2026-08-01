"""
Stub Index: a derived view of the entities the world has implied but not yet made.

Why this cannot be a vault search. Every other listing in the bible can be found
by Obsidian, because the things listed are pages. Stubs are not pages — the sync
holds them back on purpose, since a stub has a name and a one-line reason for
existing and nothing else, and writing 33 near-empty notes would bury the pages
that have content. They live only in the registry.

So this is a deriver, the same shape as the Timeline: a view over state that must
not vary when regenerated. No DNA, no model, idempotent. It rewrites only the
'## Pending' section of its target page, leaving everything the author wrote
around it intact.
"""

import os
import re
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional

from layer5_dna_substrate.registry import DNARegistry

_SECTION = "## Pending"

# Reading order: who is owed a page, then what, then where, then the rest.
_TYPE_ORDER = ["npc", "faction", "culture", "creature", "item", "text", "lore",
               "location", "settlement", "region", "realm", "regional_poi",
               "establishment", "wonder", "travel", "chronicle", "linguistic",
               "trap", "quest", "world", "agency", "system", "deity"]

_TYPE_LABEL = {
    "npc": "People", "faction": "Factions", "culture": "Peoples",
    "creature": "Creatures", "item": "Artifacts", "text": "Documents",
    "lore": "Beliefs", "location": "Locations", "settlement": "Settlements",
    "region": "Regions", "realm": "Realms", "regional_poi": "Points of Interest",
    "establishment": "Establishments", "wonder": "Wonders", "travel": "Routes",
    "chronicle": "Events", "linguistic": "Languages", "trap": "Traps",
    "quest": "Quests", "world": "Worlds", "agency": "Agencies",
}


class StubIndex:
    """Derives the pending-stub listing from a registry."""

    def __init__(self, registry: DNARegistry, vault_path: str,
                 page: str = os.path.join("Drafts", "Unmade Stubs.md")):
        self.registry = registry
        self.vault_path = vault_path
        self.page_path = os.path.join(vault_path, page)

    # ── gather ──────────────────────────────────────────────

    def pending(self) -> List[Dict]:
        """Every stub still awaiting expansion, with what the world said about it."""
        rows = []
        for entity_id, record in self.registry._records.items():
            if "stub" not in (record.get("tags") or []):
                continue
            meta = record.get("stub_metadata") or {}
            source = self.registry.get_element(meta.get("source_id") or "") or {}
            rows.append({
                "id": entity_id,
                "name": (meta.get("name") or record.get("name") or "").strip(),
                "type": record.get("type") or "unknown",
                "gist": (record.get("gist") or meta.get("description") or "").strip(),
                "source": (source.get("name") or "").strip(),
            })
        return rows

    @staticmethod
    def group(rows: List[Dict]) -> Dict[str, List[Dict]]:
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["type"]].append(row)
        for entries in grouped.values():
            entries.sort(key=lambda r: r["name"].lower())
        return grouped

    # ── render ──────────────────────────────────────────────

    @staticmethod
    def _cell(text: str, limit: int = 150) -> str:
        """Table-safe single line: pipes escaped, newlines collapsed, clipped."""
        flat = " ".join((text or "").split()).replace("|", r"\|")
        return flat if len(flat) <= limit else flat[:limit].rstrip() + "..."

    def render(self, rows: List[Dict]) -> str:
        if not rows:
            return ("*No pending stubs. Every entity the world has named has a page.*")

        grouped = self.group(rows)
        ordered = [t for t in _TYPE_ORDER if t in grouped]
        ordered += sorted(t for t in grouped if t not in _TYPE_ORDER)

        out = [
            f"*{len(rows)} entities have been named by an existing page but not yet "
            f"written. Derived from the registry — regenerate rather than edit by hand.*",
            "",
        ]
        for ptype in ordered:
            entries = grouped[ptype]
            label = _TYPE_LABEL.get(ptype, ptype.replace("_", " ").title())
            out.append(f"### {label} ({len(entries)})")
            out.append("")
            out.append("| Stub | Implied by | What the world said |")
            out.append("| :--- | :--- | :--- |")
            for row in entries:
                source = f"[[{row['source']}]]" if row["source"] else "—"
                out.append(f"| {self._cell(row['name'], 60)} | {source} "
                           f"| {self._cell(row['gist'])} |")
            out.append("")
        return "\n".join(out).rstrip()

    # ── write ───────────────────────────────────────────────

    def _new_page(self, body: str) -> str:
        today = date.today().isoformat()
        return (
            "---\n"
            "type: meta\n"
            "status: canon\n"
            f"created: {today}\n"
            f"updated: {today}\n"
            "tags:\n"
            "  - meta\n"
            "  - drafts\n"
            "---\n\n"
            "# Unmade Stubs\n\n"
            "Entities an existing page has named without describing — the world's own "
            "list of what it still owes. A stub has a name and a reason for existing "
            "and nothing more, so it gets no page of its own until it is expanded; "
            "that is why none of these can be found by searching the vault.\n\n"
            "Derived from the DNA registry by `scripts/compose_stub_index.py`. Only the "
            "**Pending** section is rewritten, so notes added elsewhere on this page "
            "survive regeneration.\n\n"
            f"{_SECTION}\n\n"
            f"{body}\n"
        )

    def write(self, rows: Optional[List[Dict]] = None) -> Dict:
        """
        Rewrite only the '## Pending' section, creating the page if absent.
        Returns a small report.
        """
        rows = self.pending() if rows is None else rows
        body = self.render(rows)

        os.makedirs(os.path.dirname(self.page_path), exist_ok=True)

        if not os.path.isfile(self.page_path):
            with open(self.page_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(self._new_page(body))
            return {"stubs": len(rows), "created": True,
                    "by_type": {k: len(v) for k, v in self.group(rows).items()}}

        with open(self.page_path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()

        start = next((i for i, ln in enumerate(lines) if ln.strip() == _SECTION), None)
        if start is None:
            # The section was removed; append it rather than overwriting the page.
            lines += ["", _SECTION, "", body]
        else:
            end = next((i for i in range(start + 1, len(lines))
                        if lines[i].startswith("## ")), len(lines))
            lines = lines[:start + 1] + ["", body, ""] + lines[end:]

        text = "\n".join(lines).rstrip() + "\n"
        text = re.sub(r"^updated: .*$", f"updated: {date.today().isoformat()}",
                      text, count=1, flags=re.M)
        with open(self.page_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)

        return {"stubs": len(rows), "created": False,
                "by_type": {k: len(v) for k, v in self.group(rows).items()}}
