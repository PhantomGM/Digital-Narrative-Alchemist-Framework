"""
Structured metadata carried at the tail of every decoded phenotype.

Every decoder prompt is instructed (via TAIL_INSTRUCTION, appended by DNADecoder)
to end its response with a single fenced YAML block containing the entity's
name, a one-line gist, a ~100-word summary, and a structured list of stubs
mirroring the "Unmade Connections" prose section.

This replaces regex-based name and stub extraction as the primary path:
downstream consumers (ExpansionManager, InheritanceEngine, ObsidianSync)
should call parse_phenotype_tail() and only fall back to regex heuristics
when the tail is missing or malformed.
"""

import re
from typing import Any, Dict, List, Optional

import yaml

VALID_STUB_TYPES = {
    "npc", "faction", "location", "settlement", "region",
    "item", "quest", "chronicle", "linguistic", "world",
    # Peoples, the things they believe, the documents carrying those beliefs, and
    # the beasts. Each files to its own part of the bible and each has its own
    # decoder (see ObsidianSync.TYPE_FOLDER_MAP).
    "culture", "lore", "text", "creature",
    # Play content rather than world content. Omitting trap was not harmless: an
    # unrecognised label falls through _resolve_stub_type's default, so every
    # "[Trap]" stub was silently registered as an npc and filed under Characters.
    "trap",
    # The same omission, found again in six more types. Each already had a
    # generator, a decoder and a folder of its own; none of them was reachable
    # from a stub, so a decoder writing "[Tavern] The Broken Wheel" produced a
    # person in Characters. The live world holds 112 records and not one of
    # these six types, which is what a type nobody can name looks like from
    # the outside.
    "agency", "establishment", "realm", "regional_poi", "travel", "wonder",
}

# The prompt's list of legal types is DERIVED from the set above rather than
# written out beside it. The two were maintained by hand and drifted: the set
# had grown to fifteen types while the prompt still offered ten, so decoders
# were never told that `creature`, `culture`, `lore`, `text` or `trap` existed
# and reached for an unlisted word instead. Deriving it makes that drift
# impossible. Sorted because set iteration order is not stable across
# processes, and an unstable prompt defeats caching.
TAIL_INSTRUCTION = f"""
### 🔩 MACHINE-READABLE TAIL (MANDATORY)

After the complete profile, end your response with ONE fenced YAML code block.
It must be the very last thing in your response - no text after it. Use exactly this shape:

```yaml
name: The entity's proper name
gist: One sentence (25 words max) naming the entity and its role in the world.
summary: >
  Roughly 100 words compressing the entity's nature, drives, secrets, and key
  relationships, written so it can guide the generation of related entities.
stubs:
  - type: npc
    name: Proper name of a mentioned-but-unmade entity
    gist: One sentence on what it is and how it relates to this entity.
```

Rules for the tail:
- The stubs list must mirror the entities in the Unmade Connections section, one entry each.
- Allowed stub types: {", ".join(sorted(VALID_STUB_TYPES))}.
- Use the closest type on that list. Do not invent a type: an unlisted word is
  read as a person, so a tavern labelled "establishment" becomes a place and the
  same tavern labelled "tavern" becomes an innkeeper.
- If there are no unmade connections, write "stubs: []".
- Plain YAML only: no wikilinks, no markdown formatting inside values.
"""

_YAML_FENCE_RE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Decoders sometimes echo the tail instruction's own heading above the fenced
# block. Stripping the block alone would leave that heading orphaned in the
# human-facing prose, so it is removed along with the tail.
_TAIL_HEADING_RE = re.compile(
    r"\n*(?:#{1,6}\s*)?[^\n]*MACHINE[- ]READABLE TAIL[^\n]*\n*\s*$",
    re.IGNORECASE,
)

# A parsed tail must carry at least one of these to be considered valid,
# so stray YAML blocks inside the prose don't get mistaken for the tail.
_REQUIRED_ANY = ("name", "gist", "summary")

def _candidate_blocks(phenotype: str) -> List[re.Match]:
    return list(_YAML_FENCE_RE.finditer(phenotype or ""))


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Coerces a raw parsed tail into the canonical shape."""
    meta: Dict[str, Any] = {
        "name": str(data.get("name") or "").strip() or None,
        "gist": str(data.get("gist") or "").strip() or None,
        "summary": str(data.get("summary") or "").strip() or None,
        "stubs": [],
    }

    raw_stubs = data.get("stubs") or []
    if isinstance(raw_stubs, list):
        for entry in raw_stubs:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            gist = str(entry.get("gist") or entry.get("description") or "").strip()
            s_type = str(entry.get("type") or "").strip().lower()
            if not name or not gist:
                continue
            meta["stubs"].append({"type": s_type, "name": name, "gist": gist})

    return meta


def parse_phenotype_tail(phenotype: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the structured YAML tail from a decoded phenotype.

    Scans fenced YAML blocks from last to first and returns the first one that
    parses to a dict carrying name/gist/summary. Returns None when no valid
    tail exists (callers fall back to legacy regex extraction).
    """
    for match in reversed(_candidate_blocks(phenotype)):
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and any(data.get(k) for k in _REQUIRED_ANY):
            return _normalize(data)
    return None


# Decoders intermittently emit fenced ASCII art and flow diagrams alongside the
# prose. Those are scaffolding, not content, and they read badly on a wiki page.
# In-world excerpts (journal quotes, inscriptions) also arrive fenced, so the two
# must be told apart rather than stripped wholesale.
_BARE_FENCE_RE = re.compile(r"\n```[ \t]*\n(.*?)\n?```[ \t]*\n", re.DOTALL)
_DIAGRAM_SYMBOLS = set("─│┌┐└┘├┤┬┴┼═║╔╗╚╝<>|/\\_+*=~^()[]{}.'`-")


def _looks_like_diagram(block: str) -> bool:
    """True when a fenced block is art or a flow diagram rather than prose."""
    text = block.strip()
    if not text:
        return True
    # Box drawing and arrow chains are unambiguous scaffolding.
    if re.search(r"─{2,}|-{2,}>|─+>|[┌┐└┘├┤┬┴┼═║╔╗╚╝]", text):
        return True
    letters = sum(ch.isalpha() for ch in text)
    symbols = sum(ch in _DIAGRAM_SYMBOLS for ch in text)
    return symbols > max(8, letters * 0.30)


def strip_decoder_artifacts(phenotype: str) -> str:
    """
    Removes fenced ASCII art and flow diagrams while leaving fenced prose
    (in-world quotations, inscriptions) intact.
    """
    def replace(match):
        return "\n" if _looks_like_diagram(match.group(1)) else match.group(0)

    return _BARE_FENCE_RE.sub(replace, phenotype or "")


def split_phenotype_tail(phenotype: str):
    """
    Splits a phenotype into (prose, tail_block). tail_block is the full fenced
    YAML tail (empty string when absent), so callers can transform the prose —
    e.g. the canonize gate's patch loop — and reattach the tail untouched.
    """
    matches = _candidate_blocks(phenotype)
    for match in reversed(matches):
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and any(data.get(k) for k in _REQUIRED_ANY):
            prose = phenotype[:match.start()] + phenotype[match.end():]
            prose = _TAIL_HEADING_RE.sub("", prose).rstrip() + "\n"
            return prose, match.group(0).strip()
    return _TAIL_HEADING_RE.sub("", phenotype).rstrip() + "\n" if _TAIL_HEADING_RE.search(phenotype) else phenotype, ""


def strip_phenotype_tail(phenotype: str) -> str:
    """
    Returns the phenotype with its structured tail removed, for human-facing
    surfaces (Obsidian notes, session prose) where the metadata is noise.
    """
    return split_phenotype_tail(phenotype)[0]
