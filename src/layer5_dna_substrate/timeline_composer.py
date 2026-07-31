"""
TimelineComposer — derives the master chronology from structured dated events.

This is a DERIVER, not a generator. A timeline is a *view* over the canon graph:
every dated event, sorted, sourced, conflict-checked. It must never invent or
vary — running it twice on the same canon yields the same table. It therefore
rolls no DNA and (by default) calls no LLM.

Sources of events, unioned and de-duplicated:
  1. A structured store: data/timeline_events.json (authored / seeded).
  2. An optional `events` list on any registry record, so a pipeline-generated
     entity can carry its own dated events and have them appear automatically.

Each event is a dict:
  {
    "date_label": "c. 1 BS" | "**0**" | "42 AS" | "— *disputed*",   # verbatim, rendered as-is
    "event":      "<the event text, verbatim — may contain [[links]] and **bold**>",
    "era":        "Golden Age" | "The Collapse" | "Post-Collapse",
    "sources":    "[[Page A]], [[Page B]]"                          # verbatim source cell
  }

The date_label is stored verbatim (so formatting round-trips perfectly) and a
numeric sort key is derived from it. write_timeline() replaces ONLY the table
inside the "## Chronology" section of Timeline.md; the authored Calendar, the
intro note, and the Eras section are preserved.
"""

import json
import os
import re
from typing import List, Dict, Optional, Tuple

ERA_ORDER = {"Golden Age": 0, "The Collapse": 1, "Post-Collapse": 2}
# Sort anchors for undated events: bucket them at the front of their era.
_UNDATED_ANCHOR = {0: -1e9, 1: -1e6, 2: 1e9}

_YEAR_RE = re.compile(r"(\d+)\s*(?:[–—-]\s*\d+\s*)?(AS|BS)\b", re.IGNORECASE)


def parse_sort(date_label: str) -> Tuple[Optional[float], bool]:
    """
    Parse a date label into (year_or_None, inferred).

    year: AS positive, BS negative; a range uses its start; the Sky-Shatter / a
    bare "0" is year 0. Undated labels (—, disputed with no number) return None.
    inferred: True when the label is approximate ("c. ...").
    """
    if not date_label:
        return None, False
    s = date_label.replace("*", "").strip()
    inferred = bool(re.match(r"\s*c\.", s, re.IGNORECASE))
    s_nolabel = re.sub(r"disputed", "", s, flags=re.IGNORECASE).strip(" —-–—")

    m = _YEAR_RE.search(s_nolabel)
    if m:
        year = int(m.group(1))
        return (float(year) if m.group(2).upper() == "AS" else float(-year)), inferred
    # No AS/BS: year zero is written as a bare "0" (the Sky-Shatter, by definition).
    if re.search(r"\b0\b", s_nolabel) or "sky-shatter" in s.lower() or "year zero" in s.lower():
        return 0.0, inferred
    return None, inferred


def _sort_key(event: Dict, idx: int) -> Tuple[float, int]:
    year, _ = parse_sort(event.get("date_label", ""))
    if year is not None:
        return (year, idx)
    anchor = _UNDATED_ANCHOR[ERA_ORDER.get(event.get("era", "Post-Collapse"), 2)]
    return (anchor, idx)


class TimelineComposer:
    def __init__(self, vault_path: str, store_path: Optional[str] = None):
        self.vault_path = vault_path
        self.timeline_md = os.path.join(vault_path, "History", "Timeline.md")
        self.store_path = store_path

    # ── Event collection ─────────────────────────────────────

    def load_events(self, registry=None) -> List[Dict]:
        """Union events from the JSON store and any registry record `events` lists, de-duplicated."""
        events: List[Dict] = []
        seen = set()

        def add(ev):
            key = (ev.get("date_label", "").strip(), ev.get("event", "").strip())
            if key not in seen and ev.get("event"):
                seen.add(key)
                events.append(ev)

        if self.store_path and os.path.isfile(self.store_path):
            with open(self.store_path, encoding="utf-8") as f:
                for ev in json.load(f):
                    add(ev)

        if registry is not None:
            for record in registry._records.values():
                for ev in record.get("events", []) or []:
                    ev = dict(ev)
                    ev.setdefault("sources", f"[[{record.get('name')}]]")
                    add(ev)

        return events

    def sort(self, events: List[Dict]) -> List[Dict]:
        return [e for _, e in sorted(
            ((_sort_key(e, i), e) for i, e in enumerate(events)), key=lambda p: p[0])]

    # ── Conflict / quality checks ────────────────────────────

    @staticmethod
    def _is_exact_zero(event: Dict) -> bool:
        """True only for a precise, singular year-zero label ('0'), not 'c. 0' or a '0–40' range."""
        label = event.get("date_label", "").replace("*", "").strip()
        if re.search(r"\d\s*[–—-]\s*\d", label):     # a range like 0–40
            return False
        year, inferred = parse_sort(event.get("date_label", ""))
        return year == 0.0 and not inferred and label == "0"

    def detect_conflicts(self, events: List[Dict]) -> List[str]:
        issues = []
        for ev in events:
            label = ev.get("date_label", "")
            year, _ = parse_sort(label)
            if year is None and label.replace("*", "").strip(" —-–—").lower() not in ("", "disputed"):
                issues.append(f"Unparseable date {label!r} for: {ev.get('event','')[:60]}")
            if not ev.get("sources", "").strip():
                issues.append(f"Missing source for: {ev.get('event','')[:60]}")
        # Year zero is the Sky-Shatter by definition; two EXACT-zero events is a real conflict.
        exact_zeros = [ev.get("event", "")[:60] for ev in events if self._is_exact_zero(ev)]
        if len(exact_zeros) > 1:
            issues.append(f"Multiple events pinned to exact year 0 (only the Sky-Shatter should be): {exact_zeros}")
        return issues

    # ── Rendering ────────────────────────────────────────────

    def render_chronology(self, events: List[Dict]) -> str:
        rows = ["| Date | Event | Era | Source |", "| ---- | ----- | --- | ------ |"]
        for ev in self.sort(events):
            rows.append(
                f"| {ev.get('date_label','—')} | {ev.get('event','')} | "
                f"{ev.get('era','')} | {ev.get('sources','')} |")
        return "\n".join(rows)

    def write_timeline(self, events: List[Dict]) -> Dict:
        """
        Replace ONLY the table inside the '## Chronology' section of Timeline.md,
        preserving the section's heading, intro note, and every other section.
        Returns a small report.
        """
        with open(self.timeline_md, encoding="utf-8") as f:
            lines = f.read().splitlines()

        # Find the Chronology section bounds.
        start = next((i for i, ln in enumerate(lines) if ln.strip() == "## Chronology"), None)
        if start is None:
            raise ValueError("No '## Chronology' section in Timeline.md")
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))

        section = lines[start:end]
        # Keep everything in the section that is not a table row; drop old table rows.
        preserved = [ln for ln in section if not ln.lstrip().startswith("|")]
        # Trim trailing blank lines from preserved intro, then append the fresh table.
        while preserved and preserved[-1].strip() == "":
            preserved.pop()
        new_section = preserved + ["", self.render_chronology(events), ""]

        new_lines = lines[:start] + new_section + lines[end:]
        with open(self.timeline_md, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(new_lines) + "\n")

        return {"events": len(events), "conflicts": self.detect_conflicts(events)}

    # ── Seeder: ingest the current hand-built table into the store ──

    def seed_from_timeline_md(self) -> List[Dict]:
        """Parse the existing '## Chronology' table rows into structured events."""
        with open(self.timeline_md, encoding="utf-8") as f:
            lines = f.read().splitlines()
        start = next((i for i, ln in enumerate(lines) if ln.strip() == "## Chronology"), None)
        if start is None:
            return []
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))

        events = []
        for ln in lines[start:end]:
            if not ln.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) != 4 or cells[0] in ("Date", "----") or set(cells[0]) <= set("- "):
                continue
            events.append({"date_label": cells[0], "event": cells[1],
                           "era": cells[2], "sources": cells[3]})
        return events
