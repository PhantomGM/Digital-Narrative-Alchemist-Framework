"""
CanonComposer — builds a page for a stub from what CANON already says about it.

The third path, beside DNA generation and derivation. Many stubs name an entity
that an existing canon page already describes in full — a fortress, a food, a
mine, a sub-order. For those, rolling DNA is actively harmful: the random genome
invents traits that contradict the description (the same failure the "canon
overrides DNA" rule patches at decode time). This composer sidesteps it entirely:
it gathers every canon block that names the stub and assembles a sourced page,
inventing nothing and calling no LLM. Run it twice, get the same page.

It also triages: assess() reports whether a stub is COMPOSE-ready (canon already
describes it) or needs GENERATE (canon knows only its name, so DNA must invent).
"""

import re
from datetime import date
from typing import List, Dict, Optional, Tuple

from layer5_dna_substrate.phenotype_meta import strip_phenotype_tail

# A relation-edge bullet like "- **Mentions_X**: [[Y]]" is link metadata, not prose.
_RELATION_RE = re.compile(r"^\*{0,2}[\w '\-/]+\*{0,2}:\s*\[\[")
# An Unmade-Connections bullet like "[Type] Name: ..." or "**[Type] Name:** ..." —
# terse and redundant with the richer prose the entity is described in elsewhere.
_STUBLINE_RE = re.compile(r"^\*{0,2}\[\w+\]\s")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'\[])")
_BULLET_RE = re.compile(r"^(?:[*\-•]|\d+\.)\s+")


class CanonComposer:
    #: how much canon prose (chars, beyond the bare name) makes a stub compose-ready
    COMPOSE_MIN_CHARS = 160

    def __init__(self, registry):
        self.registry = registry

    def _canon_records(self) -> List[Dict]:
        return [r for r in self.registry._records.values() if "canonized" in r.get("tags", [])]

    # ── Block extraction ─────────────────────────────────────

    @staticmethod
    def _blocks(text: str) -> List[Tuple[str, str]]:
        """Split a phenotype into (kind, text) blocks — kind is 'bullet' or 'prose'.

        The structured YAML tail is stripped first. Headers, tables, callouts, fences,
        and relation-edge lines are dropped. Both '*/-/•' and numbered '1.' items are
        bullets (so landmark lists split into one block per landmark)."""
        text = strip_phenotype_tail(text or "")
        blocks: List[Tuple[str, str]] = []
        para: List[str] = []

        def flush():
            if para:
                blocks.append(("prose", " ".join(para).strip()))
                para.clear()

        for raw in text.splitlines():
            s = raw.strip()
            if not s or s.startswith(("#", "|", ">", "```", "---")):
                flush()
                continue
            if _BULLET_RE.match(s):
                flush()
                bullet = _BULLET_RE.sub("", s).strip()
                if bullet and not _RELATION_RE.match(bullet) and not _STUBLINE_RE.match(bullet):
                    blocks.append(("bullet", bullet))
            else:
                para.append(s)
        flush()
        return [(k, t) for k, t in blocks if t]

    @staticmethod
    def _mentions(block: str, name: str) -> bool:
        return re.search(r"\b" + re.escape(name) + r"\b", block, re.IGNORECASE) is not None

    # ── Gathering ────────────────────────────────────────────

    def gather(self, name: str, exclude_id: Optional[str] = None) -> List[Tuple[str, str]]:
        """Every canon block mentioning `name`, as (source_page, block_text), de-duplicated.

        The bare Unmade-Connections stub line is kept but marked terse (it is canon,
        just thin); richer descriptions are what make a stub compose-ready.
        """
        found: List[Tuple[str, str]] = []
        seen = set()
        for rec in self._canon_records():
            if rec["id"] == exclude_id:
                continue
            src = rec.get("name") or "?"
            for kind, block in self._blocks(rec.get("phenotype", "")):
                if not self._mentions(block, name):
                    continue
                if kind == "bullet":
                    fragments = [block]           # a bullet is a self-contained description
                else:
                    # A prose paragraph contributes only the sentence(s) that name the entity,
                    # so a passing mention doesn't drag in unrelated content.
                    fragments = [s for s in _SENTENCE_SPLIT.split(block) if self._mentions(s, name)]
                for frag in fragments:
                    frag = frag.strip()
                    key = frag.lower()[:120]
                    if frag and key not in seen:
                        seen.add(key)
                        found.append((src, frag))
        return found

    # ── Triage ───────────────────────────────────────────────

    def assess(self, stub: Dict) -> Dict:
        name = stub.get("name") or ""
        blocks = self.gather(name, exclude_id=stub["id"])
        # "Substantial" = a description, not a name-drop or the terse stub line.
        rich = [(s, b) for s, b in blocks
                if len(b) >= self.COMPOSE_MIN_CHARS and not _STUBLINE_RE.match(b)]
        rich_chars = sum(len(b) for _, b in rich)
        strategy = "compose" if rich_chars >= self.COMPOSE_MIN_CHARS else "generate"
        return {
            "name": name, "type": stub.get("type"), "strategy": strategy,
            "mentions": len(blocks), "rich_blocks": len(rich),
            "sources": sorted({s for s, _ in blocks}),
        }

    def triage_all(self) -> List[Dict]:
        stubs = [r for r in self.registry._records.values() if "stub" in r.get("tags", [])]
        return sorted((self.assess(s) for s in stubs),
                      key=lambda a: (a["strategy"] != "compose", -a["rich_blocks"], a["name"]))

    # ── Composition ──────────────────────────────────────────

    def compose(self, stub: Dict) -> Optional[str]:
        """Return a page BODY composed from canon (for record['phenotype']), or None
        if canon does not describe the stub richly enough to compose."""
        name = stub.get("name") or ""
        blocks = self.gather(name, exclude_id=stub["id"])
        rich = [(s, b) for s, b in blocks
                if len(b) >= self.COMPOSE_MIN_CHARS and not _STUBLINE_RE.match(b)]
        if sum(len(b) for _, b in rich) < self.COMPOSE_MIN_CHARS:
            return None

        sources = sorted({s for s, _ in blocks})
        lines = [
            f"### {name}",
            "",
            "> [!note] Composed from canon — no DNA",
            f"> This page is assembled from what existing canon already establishes about "
            f"{name}. It invents nothing; every statement below is drawn from a canon page and "
            f"cited to it. Expand it into a full entry, or canonize it as-is, at the author's discretion.",
            "",
            "### What the canon establishes",
            "",
        ]
        for src, block in blocks:
            lines.append(f"- {block} — [[{src}]]")
        lines += [
            "",
            "### Open questions",
            "",
            f"*Everything canon has not yet fixed about {name} — its own history, its people, "
            f"what it wants — is open, and a full expansion or the author's hand may decide it.*",
            "",
        ]
        return "\n".join(lines)

    def compose_into_record(self, stub_id: str) -> bool:
        """Compose a stub in place: replace its phenotype, retag, mark audit=composed.
        Returns True if composed, False if canon was insufficient (left untouched)."""
        stub = self.registry.get_element(stub_id)
        body = self.compose(stub)
        if body is None:
            return False
        stub["phenotype"] = body
        stub["dna"] = "COMPOSED"
        stub["gist"] = stub.get("gist") or (stub.get("stub_metadata", {}) or {}).get("description")
        stub["tags"] = [t for t in stub.get("tags", []) if t != "stub"] + ["canon-composed"]
        stub["audit"] = {"status": "composed", "notes": ["assembled from canon; no generation"],
                         "reviewed": date.today().isoformat()}
        return True
