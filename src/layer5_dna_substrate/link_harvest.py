"""
Reconcile the registry against what the vault actually says.

The registry only records edges it created at generation time. Everything the
author wrote by hand, and every relationship a decoder put in prose that never
became a wikilink, is invisible to it — which matters because the LINEAGE layer
of every generation prompt is a depth-2 walk over exactly this edge store. A
missing edge at hop one removes everything behind it at hop two.

Measured against the vault this gap was large: the registry knew 112 of the 165
relationships the wikilinks alone imply, and a further 47 existed only as bare
prose mentions. Nine named doctrines ("the Vow of the Blank Page", "the Law of
Utility") were named in canon but registered nowhere at all, so they never
reached the unmade-stub backlog.

Three harvests, all mechanical and all deterministic:

  * edges     - relationships the vault states and the registry lacks
  * entities  - named things canon uses that no record covers
  * pairs     - characters who share a page but no link (an authoring worklist)

Nothing here calls a model and nothing here writes prose. Page text is read
only. Canon is never modified: the harvest proposes, and applying it touches the
registry's edge store, never a page.
"""

import os
import re
from typing import Dict, List, Optional, Set

# Pages that exist to navigate the vault rather than describe the world. A
# mention inside one of these is a directory entry, not a relationship.
HUB_STEMS = {
    "Index", "Home", "Log", "README", "CLAUDE", "Drafts", "Unmade Stubs",
    "Timeline", "World Overview", "Atlas", "Characters", "Factions", "Cultures",
    "History", "Cosmology", "Systems", "Bestiary", "Artifacts", "Lore",
    "Encounters", "Traps", "Quests", "Realms", "Regions", "Settlements",
    "Locations", "Points of Interest", "Establishments", "Wonders", "Routes",
}
SKIP_DIRS = {".git", ".obsidian", ".zcode", ".agents", "graphify-out", "Templates"}

_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)


def load_pages(vault_path: str) -> Dict[str, dict]:
    """stem -> {body, folder, status}. Hubs and templates are excluded."""
    pages = {}
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for filename in files:
            if not filename.endswith(".md"):
                continue
            stem = filename[:-3]
            folder = os.path.basename(root)
            # A folder note carries the folder's name and is navigation.
            if stem in HUB_STEMS or stem == folder:
                continue
            with open(os.path.join(root, filename), "r",
                      encoding="utf-8", errors="replace") as handle:
                body = handle.read()
            status, page_type = "", ""
            head = _FRONTMATTER.match(body)
            if head:
                found = re.search(r"^status:\s*(\S+)", head.group(0), re.M)
                status = found.group(1).strip().strip('"') if found else ""
                found = re.search(r"^type:\s*(\S+)", head.group(0), re.M)
                page_type = found.group(1).strip().strip('"') if found else ""
            # Meta pages describe the vault, not the world. Excluding them is
            # also what stops this deriver reading its own output back in: the
            # worklist names every character, so on a second run it registered
            # as a page they all share, and every pair cited it as evidence.
            if page_type == "meta":
                continue
            pages[stem] = {"body": body, "folder": folder, "status": status}
    return pages


def entity_index(registry) -> Dict[str, str]:
    """name -> entity id, for every record that has a usable name."""
    index = {}
    for entity_id, record in registry._records.items():
        meta = record.get("stub_metadata") or {}
        name = (record.get("name") or meta.get("name") or "").strip()
        if name:
            index.setdefault(name, entity_id)
    return index


def existing_pairs(registry) -> Set[frozenset]:
    """Unordered id pairs the registry already links, in any relation."""
    pairs = set()
    for entity_id, relations in registry._edges.items():
        for items in relations.values():
            for item in items:
                other = item.get("id") if isinstance(item, dict) else item
                if other and other != entity_id:
                    pairs.add(frozenset((entity_id, other)))
    return pairs


def _mentions(body: str, name: str) -> int:
    """
    Word-boundary count of a full name.

    Full names only, never a prefix or a fragment. A substring test here would
    match 'Log' inside unrelated words and 'Aetherium' inside every artifact —
    the same defect that once polluted citation selection.
    """
    return len(re.findall(rf"(?<!\w){re.escape(name)}(?!\w)", body))


def harvest_edges(registry, pages: Dict[str, dict]) -> List[dict]:
    """
    Relationships the vault states that the registry does not hold.

    A wikilink is an explicit authorial statement; a bare prose mention is the
    same relationship the pipeline simply failed to record. Both are reported,
    tagged by kind so the caller can treat them differently.
    """
    names = entity_index(registry)
    known = existing_pairs(registry)
    seen: Set[frozenset] = set()
    out = []

    for stem, page in sorted(pages.items()):
        source_id = names.get(stem)
        if not source_id:
            continue
        body = page["body"]
        linked = {m.split("|")[0].split("#")[0].strip()
                  for m in _WIKILINK.findall(body)}

        for target, target_id in names.items():
            if target == stem or target_id == source_id:
                continue
            pair = frozenset((source_id, target_id))
            if pair in known or pair in seen:
                continue
            if target in linked:
                kind, count = "wikilink", max(1, _mentions(body, target))
            else:
                count = _mentions(body, target)
                if not count:
                    continue
                kind = "prose"
            seen.add(pair)
            out.append({
                "source_id": source_id, "target_id": target_id,
                "source": stem, "target": target, "kind": kind,
                "mentions": count, "label": f"mentions_{target}",
                "status": page["status"],
            })
    out.sort(key=lambda r: (r["kind"] != "wikilink", -r["mentions"], r["source"]))
    return out


# Emphasis and headings are how canon marks a named doctrine: "the Law of
# Utility", **Vow of the Blank Page**, *The Iron Unbinding*.
_EMPHASISED = [
    re.compile(r"\*\*([^*\n]{4,60})\*\*"),
    re.compile(r"(?<!\*)\*([^*\n]{4,60})\*(?!\*)"),
    re.compile(r"[\"“]([^\"”\n]{4,60})[\"”]"),
    re.compile(r"^#{2,4}\s+(.{4,60})$", re.M),
]
# Words that mark a section label rather than a thing in the world.
_SECTION_WORDS = {
    "secrets", "shadows", "hooks", "profile", "toolkit", "overview", "summary",
    "elements", "adventure", "example", "interaction", "connections", "stubs",
    "relations", "model", "trends", "situations", "life", "daily", "history",
    "appearance", "goals", "notes", "description", "gamemaster", "campaign",
    "behavioral", "story", "unmade", "dna", "traits", "abilities", "tactics",
}
_STOP_HEAD = {"the", "a", "an", "of", "and", "or", "in", "on", "for", "to"}


# Generated pages carry two machine-written blocks: the DNA Relations header and
# the Unmade Connections tail. Both are full of entity-shaped strings that are
# metadata, not prose, so they are cut before anything is read as a claim.
_MACHINE_BLOCK = re.compile(
    r"^#{1,4}\s*[^\n]*(?:DNA Relations|Unmade Connections)[^\n]*$.*?(?=^#{1,4}\s|\Z)",
    re.M | re.S)


def _prose_only(body: str) -> str:
    return _MACHINE_BLOCK.sub("", body)


def candidate_entities(registry, pages: Dict[str, dict],
                       min_pages: int = 1, max_pages: int = 3) -> List[dict]:
    """
    Named things canon emphasises that no record and no page covers.

    Deliberately conservative: a candidate must be a multi-word Title Case
    phrase, must not read as a section label, and must not already be an entity
    or a page. This is a proposal list for the author, never an auto-registration.

    The decisive filter is `max_pages`. Every generated page repeats the same
    bold phenotype field labels — 'Narrative Essence', 'Core Vulnerability',
    'Notable Possessions' — so a phrase emphasised on a dozen pages is a template
    slot, while a doctrine belongs to the one or two pages that invoke it. Word
    shape cannot separate those two; recurrence can.
    """
    names = set(entity_index(registry))
    lowered_names = {n.lower() for n in names}
    lowered_pages = {p.lower() for p in pages}
    hits: Dict[str, dict] = {}

    for stem, page in sorted(pages.items()):
        body = _prose_only(page["body"])
        # The label test below asks what FOLLOWS the phrase, so the emphasis
        # markers have to come off first -- otherwise the next character is
        # always the closing '**' and every candidate looks like a label.
        plain = re.sub(r"[*\"“”]", "", body)
        for pattern in _EMPHASISED:
            for raw in pattern.findall(body):
                phrase = raw.strip().strip(":;,.—-").strip()
                phrase = re.sub(r"\s+", " ", phrase)
                if "_" in phrase or "[[" in phrase:
                    continue  # a registry label, not something anyone wrote
                words = phrase.split()
                if not 2 <= len(words) <= 6:
                    continue
                if any(w.lower() in _SECTION_WORDS for w in words):
                    continue
                # Title Case: every word either capitalised or a small joiner.
                if not all(w[:1].isupper() or w.lower() in _STOP_HEAD
                           for w in words):
                    continue
                if words[0].lower() in _STOP_HEAD and len(words) < 3:
                    continue
                low = phrase.lower()
                # Known already, as an entity or a page -- including the
                # singular/plural slip ('Aetherium Shard' vs the real Shards).
                variants = {low, "the " + low, low.rstrip("s"), low + "s",
                            re.sub(r"^the ", "", low)}
                if variants & lowered_names or variants & lowered_pages:
                    continue
                # A template slot is only ever written as '**Label:**'. A thing
                # in the world gets talked about: 'the Blighted Accord was
                # forged in 42 AS'. Require at least one such use.
                if not re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)\s*(?!:)",
                                 plain):
                    continue

                row = hits.setdefault(phrase, {"name": phrase, "sources": set(),
                                               "canon_sources": set()})
                row["sources"].add(stem)
                if page["status"] == "canon":
                    row["canon_sources"].add(stem)

    out = [{"name": r["name"], "sources": sorted(r["sources"]),
            "canon_sources": sorted(r["canon_sources"])}
           for r in hits.values()
           if min_pages <= len(r["sources"]) <= max_pages]
    out.sort(key=lambda r: (-len(r["canon_sources"]), -len(r["sources"]), r["name"]))
    return out


def unlinked_character_pairs(registry, pages: Dict[str, dict],
                             char_type: str = "npc") -> List[dict]:
    """
    Characters who share a page but have no link between them.

    Skarn's people hang off institutions and never touch each other: of 14
    character pages only four name another character. Dramatic friction in play
    comes from person-to-person debts and grudges, so this is an authoring
    worklist, not a defect report — nothing here is written automatically.
    """
    names = entity_index(registry)
    chars = {name: eid for name, eid in names.items()
             if (registry.get_element(eid) or {}).get("type") == char_type}
    known = existing_pairs(registry)

    shared: Dict[frozenset, Set[str]] = {}
    for stem, page in sorted(pages.items()):
        present = [n for n in chars if _mentions(page["body"], n)]
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                shared.setdefault(frozenset((a, b)), set()).add(stem)

    out = []
    for pair, where in shared.items():
        a, b = sorted(pair)
        if frozenset((chars[a], chars[b])) in known:
            continue
        # A wikilink on either page is already an explicit relationship.
        def links_from(stem):
            body = pages.get(stem, {}).get("body", "")
            return {m.split("|")[0].split("#")[0].strip()
                    for m in _WIKILINK.findall(body)}

        if b in links_from(a) or a in links_from(b):
            continue
        out.append({"a": a, "b": b, "shared_pages": sorted(where),
                    "weight": len(where)})
    out.sort(key=lambda r: (-r["weight"], r["a"], r["b"]))
    return out


def apply_edges(registry, proposals: List[dict],
                kinds: Optional[Set[str]] = None) -> int:
    """Write harvested relationships into the registry as peer edges."""
    kinds = kinds or {"wikilink", "prose"}
    added = 0
    for row in proposals:
        if row["kind"] not in kinds:
            continue
        registry.link_elements(row["source_id"], row["target_id"],
                               "peer", row["label"])
        added += 1
    return added


def register_entities(registry, rows: List[dict], element_type: str,
                      pages: Dict[str, dict]) -> List[str]:
    """
    Register proposals as stubs, so the existing stub index surfaces them.

    Shaped exactly like ExpansionManager's stubs — same tags, same
    stub_metadata, same mentions_ edge back to the page that named it — so
    every downstream deriver treats them identically.
    """
    names = entity_index(registry)
    created = []
    for row in rows:
        name = row["name"]
        if name in names:
            continue
        source_stem = (row.get("canon_sources") or row.get("sources") or [None])[0]
        source_id = names.get(source_stem or "")
        gist = row.get("gist") or (
            f"Named in {source_stem}; not yet described." if source_stem
            else "Named in canon; not yet described.")
        tags = ["stub", name.replace(" ", "_").lower()]
        if source_id:
            tags.insert(1, f"from_{source_id}")
        stub_id = registry.register_element(
            element_type=element_type, raw_dna="STUB",
            decoded_profile=f"[STUB] {name}: {gist}",
            name=name, gist=gist, tags=tags)
        registry._records[stub_id]["stub_metadata"] = {
            "name": name, "description": gist, "source_id": source_id}
        if source_id:
            registry.link_elements(source_id, stub_id, "peer", f"mentions_{name}")
        names[name] = stub_id
        created.append(stub_id)
    return created


def render_worklist(pairs: List[dict], candidates: List[dict],
                    edges: List[dict]) -> str:
    """The authoring worklist, as a vault page. Derived: safe to overwrite."""
    lines = [
        "---", "type: meta", "status: draft", "tags:", "  - meta", "  - derived",
        "---", "", "# Link Gaps", "",
        "> Derived by `scripts/backfill_registry.py`. Do not hand-edit — rerun it.",
        "", "Relationships the vault implies that nothing records, and people who "
        "share a scene but no connection. Nothing here is canon; it is a queue.", "",
    ]

    lines += ["## Characters who share a page but no link", ""]
    if pairs:
        lines += ["An explicit debt, grudge, or alliance between any of these would "
                  "turn an institutional spoke into a relationship.", "",
                  "| Character | Character | Shared pages |", "| :--- | :--- | :--- |"]
        for row in pairs:
            where = ", ".join(f"[[{p}]]" for p in row["shared_pages"][:4])
            lines.append(f"| [[{row['a']}]] | [[{row['b']}]] | {where} |")
    else:
        lines.append("_None._")

    lines += ["", "## Named in canon, described nowhere", ""]
    if candidates:
        lines += ["| Name | Named in |", "| :--- | :--- |"]
        for row in candidates:
            where = ", ".join(f"[[{p}]]" for p in
                              (row["canon_sources"] or row["sources"])[:4])
            lines.append(f"| {row['name']} | {where} |")
    else:
        lines.append("_None._")

    prose = [e for e in edges if e["kind"] == "prose"]
    lines += ["", "## Relationships stated in prose but never linked", ""]
    if prose:
        lines += [f"{len(prose)} mention(s) that no `[[wikilink]]` records. "
                  "The registry now holds them; adding the wikilink would make "
                  "them visible in Obsidian's graph too.", "",
                  "| Page | Mentions | Times |", "| :--- | :--- | ---: |"]
        for row in prose[:60]:
            lines.append(f"| [[{row['source']}]] | [[{row['target']}]] "
                         f"| {row['mentions']} |")
    else:
        lines.append("_None._")

    return "\n".join(lines) + "\n"
