"""
The Context Assembler: answers "what does the world say here?" for every
decode and every audit.

It merges the two memories of the system —
  - the DNA Registry (working memory: this run's entities and their graph)
  - the world-bible vault via VaultAdapter (long-term memory: canon)
— into a budgeted, layered ContextPackage:

  1. World Frame   - pillars, tone, calendar, naming rules (global anchor)
  2. Locale        - the containment chain where the entity is being placed
  3. Lineage       - the source entity and its graph neighborhood
  4. Negative Space- roster of existing entities: reference, don't recreate
  5. Directives    - the stub imprint and caller guidance

package.for_decoder() feeds generation (prevention);
package.canon_slice() feeds the ConsistencyAuditor (verification) —
both read the same truth.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.vault_adapter import VaultAdapter

# Fraction of the token budget granted to each capped decoder layer.
_LAYER_BUDGET = {"world_frame": 0.25, "locale": 0.25, "lineage": 0.20,
                 "roster": 0.30}
_CHARS_PER_TOKEN = 4

# How much of each cited canon page to carry, and how many pages at most.
# A gist is one line; verifying a claim needs the paragraph that established it —
# and the deciding paragraph can sit anywhere in the page, so a short head
# excerpt is no better than the gist. Corin's reveal about the Litany lies past
# 3,000 characters into its page.
_CITATION_CHARS_PER_PAGE = 6000
_MAX_CITED_PAGES = 8
# Citations get an absolute ceiling rather than a share of budget_tokens: they
# exist only in the audit slice, so scaling them through the shared budget would
# inflate the decoder layers to no purpose. The anchor page is emitted first and
# therefore survives truncation.
_CITATION_TOTAL_CHARS = 40000
# Naming rules with worked examples, plus the idioms and taboos. Skarn's own
# profile needs 3037 characters, so a 3000 cap severed its last taboo
# mid-sentence — and half a taboo is worse than none, since "words that
# translate to failure are avoided in formal contexts" reads as a rule while
# the clause naming the euphemisms reads as the way out of it. The headroom is
# deliberate. Phonetics and register are still excluded rather than raising
# this further; they describe a sound the naming rules already demonstrate.
_NAMING_CHARS = 3400
_NAMING_HEADER_CANON = (
    "[LANGUAGE - canon. Any name invented for a person, place, faction or "
    "object must obey these rules rather than falling back on generic fantasy "
    "naming. The taboos are binding: a speaker who breaks one is doing "
    "something transgressive, and should be written as such.]")
_NAMING_HEADER_DRAFT = (
    "[LANGUAGE - draft, not yet approved as canon. Follow these when inventing "
    "a name, and treat the taboos as how people speak here. Because they are "
    "unapproved, they do not override anything canon already establishes.]")

# Vault machinery, not world facts. Log.md in particular is a 35KB append-only
# operations log that would swallow the whole citation budget.
_NON_CANON_SOURCES = {"log", "index", "home", "world overview"}

_CITATION_HEADER = (
    "FULL TEXT of the canon pages this passage refers to. These are the "
    "authoritative record. A statement that agrees with them is correct even if "
    "the one-line summaries below omit it; a statement that contradicts them is "
    "wrong. Where these pages leave a question open, it IS open — do not treat "
    "silence as permission to resolve it:"
)

_ROSTER_HEADER = (
    "The following entities ALREADY EXIST in this world. Reference them and "
    "build relationships to them where natural. Do NOT recreate them and do "
    "NOT reuse their names for new entities:"
)


SPATIAL_TYPES = {"location", "settlement", "region", "world", "realm"}


def resolve_locale(registry: DNARegistry, entity_id: Optional[str]) -> Optional[str]:
    """
    The spatial entity an operation should be grounded in: the entity itself
    if spatial, else its first spatial container. Containers live on "child"
    edges (link_elements(A, B, "parent") makes A the parent OF B, stored as
    edges[B]["child"]=[A]).
    """
    if not entity_id:
        return None
    record = registry.get_element(entity_id)
    if not record:
        return None
    if record["type"] in SPATIAL_TYPES:
        return entity_id
    for container_id in registry.get_link_ids(entity_id).get("child", []):
        container = registry.get_element(container_id)
        if container and container["type"] in SPATIAL_TYPES:
            return container_id
    return None


@dataclass
class AssemblyRequest:
    element_type: str
    anchor_id: Optional[str] = None      # source/parent entity in the registry
    locale_id: Optional[str] = None      # where the entity is being placed
    imprint: str = ""                    # stub name + description from Unmade Connections
    directives: str = ""                 # caller's specialist guidance
    budget_tokens: int = 3000
    # The text to be verified. Supplied by the auditor path only; when present,
    # the canon pages it names are carried in full (see _build_citations).
    passage: str = ""


@dataclass
class ContextPackage:
    world_frame: str = ""
    locale: str = ""
    lineage: str = ""
    roster: str = ""
    directives: str = ""
    # Full text of the canon pages the audited passage refers to. Audit slice
    # only: generation is steered by roster and locale, verification needs sources.
    citations: str = ""
    # The world's naming rules. Held apart from world_frame because the two
    # consumers need different things: a decoder should follow the best rules
    # available, canon or not, while the auditor must only ever weigh a page
    # against approved canon. Folding these into world_frame made an unapproved
    # draft profile part of the baseline other pages are judged against.
    naming: str = ""
    naming_is_canon: bool = False

    def _sections(self, include_directives: bool) -> List[str]:
        parts = []
        if self.world_frame:
            parts.append("## WORLD FRAME (applies to everything)\n" + self.world_frame)
        if self.naming:
            parts.append(self.naming)
        if self.locale:
            parts.append("## LOCALE (where this entity lives)\n" + self.locale)
        if self.lineage:
            parts.append("## LINEAGE (entities this one descends from or relates to)\n" + self.lineage)
        if self.roster:
            parts.append("## EXISTING ENTITIES (negative space)\n" + self.roster)
        if include_directives and self.directives:
            parts.append("## DIRECTIVES FOR THIS GENERATION\n" + self.directives)
        return parts

    def for_decoder(self) -> str:
        """Full package, for injection into a decoder prompt's context slot."""
        sections = self._sections(include_directives=True)
        return "\n\n".join(sections) if sections else "No additional context provided."

    def canon_slice(self) -> str:
        """
        The authoritative-truth subset, for use as the ConsistencyAuditor's
        world state.

        Citations come before the roster deliberately. The roster is one gist per
        entity, enough to prevent duplicate names but not to verify a claim — and
        judging claims against gists caused every audit failure on this world. A
        TRUE statement about Kaelen was patched away because his gist did not
        mention it, and a page asserting proof about the First Architects passed
        because no gist contradicted it. The cited pages are the actual record;
        the roster is only a directory.
        """
        parts = []
        if self.world_frame:
            parts.append(self.world_frame)
        # Only canonized naming rules are evidence. A draft profile is a
        # proposal; auditing canon pages against it would let unapproved
        # content generate contradictions in approved ones.
        if self.naming and self.naming_is_canon:
            parts.append(self.naming)
        if self.locale:
            parts.append(self.locale)
        if self.citations:
            parts.append(self.citations)
        if self.roster:
            parts.append(
                "SUMMARY DIRECTORY (one line each, for names only — an omission "
                "here is not evidence of anything):\n" + self.roster)
        return "\n\n".join(parts)


class ContextAssembler:
    def __init__(self, registry: DNARegistry, vault: Optional[VaultAdapter] = None):
        self.registry = registry
        self.vault = vault

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _cap(text: str, budget_tokens: int, fraction: float) -> str:
        """Caps a layer at its budget share, dropping whole trailing lines."""
        max_chars = int(budget_tokens * fraction * _CHARS_PER_TOKEN)
        if len(text) <= max_chars:
            return text
        capped = text[:max_chars].rsplit("\n", 1)[0].rstrip()
        return capped

    def _entity_line(self, record: dict) -> str:
        name = record.get("name") or f"{record.get('type', 'entity').title()} (unnamed)"
        gist = record.get("gist") or (record.get("phenotype") or "")[:120].replace("\n", " ")
        return f"- {name} ({record.get('type')}): {gist}"

    def _entity_block(self, record: dict) -> str:
        """Name + gist + summary for a lineage/locale entity."""
        lines = [self._entity_line(record)]
        summary = record.get("summary")
        if summary:
            lines.append(f"  {summary}")
        return "\n".join(lines)

    def _containment_chain(self, locale_id: str, max_depth: int = 4) -> List[dict]:
        """
        Walks upward from the locale to its containers, innermost first.

        Registry edge semantics: link_elements(A, B, "parent") means A is the
        parent OF B, stored as edges[A]["parent"]=[B] and edges[B]["child"]=[A].
        So an entity's containers live on its "child" edges.
        """
        chain = []
        current = locale_id
        seen = set()
        for _ in range(max_depth):
            if not current or current in seen:
                break
            seen.add(current)
            record = self.registry.get_element(current)
            if not record:
                break
            chain.append(record)
            containers = self.registry.get_link_ids(current).get("child", [])
            current = containers[0] if containers else None
        return chain

    def _nearby_ids(self, start_ids: List[str], depth: int = 2) -> List[str]:
        """BFS over all edge types, collecting entity IDs within `depth` hops."""
        found: List[str] = []
        seen = set(i for i in start_ids if i)
        queue = [(i, 0) for i in start_ids if i]
        while queue:
            current, dist = queue.pop(0)
            if dist >= depth:
                continue
            for ids in self.registry.get_link_ids(current).values():
                for linked in ids:
                    if linked not in seen:
                        seen.add(linked)
                        found.append(linked)
                        queue.append((linked, dist + 1))
        return found

    def _linguistic_anchor(self, chain_ids: List[str]) -> Optional[dict]:
        """
        The linguistic profile linked to the locale chain, else the first one.

        Written profiles beat stubs. A stub is a name and a reason for existing,
        so anchoring to one supplies no conventions at all while still looking
        like a hit — and the stub would then shadow a real profile elsewhere in
        the registry.
        """
        linguistics = [r for r in self.registry.get_all_by_type("linguistic")
                       if "stub" not in (r.get("tags") or [])]
        if not linguistics:
            return None
        chain_set = set(chain_ids)
        for record in linguistics:
            links = self.registry.get_link_ids(record["id"])
            neighbors = set(links.get("parent", []) + links.get("peer", []) + links.get("child", []))
            if neighbors & chain_set:
                return record
        return linguistics[0]

    def _naming_conventions(self, chain_ids: List[str]) -> tuple:
        """
        The world's naming rules, verbatim, for the decoder to follow.

        The linguistic decoder exists to be a "Root Truth ... across all future
        NPCs, Locations, and Factions", and it earns that by being concrete:
        five worked example names and the rule behind them. A gist cannot carry
        that. Without it every decode invents names from the model's own
        defaults, which is why one DNA string across five worlds produced three
        characters surnamed Vane and two called Lyra.
        """
        record = self._linguistic_anchor(chain_ids)
        if not record:
            return "", False
        body = (record.get("phenotype") or "").strip()
        if not body:
            return "", False
        is_canon = "canonized" in (record.get("tags") or [])

        # Prefer the naming section; the phonetics and idioms matter less to a
        # decoder that only has to name a person and make them sound local.
        # Naming Conventions through the end of Common Idioms & Taboos.
        #
        # Naming alone was too little. The taboos in particular are not flavour:
        # Skarn's language forbids speaking the pre-Collapse architects' names,
        # which is an in-world reason nobody can identify them — the same thing
        # the standing ruling protects from the other direction. Dropping it
        # left a canon-safety rule out of every prompt.
        #
        # Phonetics and "Influence on Other DNA" are still skipped. Both are
        # abstract descriptions of how the language sounds, which the naming
        # rules and idioms already demonstrate concretely, and context budget
        # spent on them buys less than the same space spent on locale or lineage.
        match = re.search(
            r"^.{0,8}\**\s*Naming Conventions\b.*?(?=^\s*\**\s*(?:Influence on "
            r"Other|###)|\Z)",
            body, re.M | re.S | re.I)
        section = match.group(0).strip() if match else body
        if len(section) > _NAMING_CHARS:
            section = section[:_NAMING_CHARS].rsplit("\n", 1)[0]
        name = record.get("name") or "the world's language"
        header = _NAMING_HEADER_CANON if is_canon else _NAMING_HEADER_DRAFT
        return f"{header}\n({name})\n{section}", is_canon

    # ── Layers ───────────────────────────────────────────────

    def _with_rulings(self, frame: str) -> str:
        """
        Guarantee the standing rulings are in the world frame, appended after the
        cap rather than subject to it.

        The rulings sit at the end of the World Overview, which is longer than the
        world-frame budget, so capping silently cut exactly the content that
        exists to prevent canon violations — in both the decoder context and the
        audit slice. Rules that are not in the prompt cannot be followed.
        """
        if not self.vault:
            return frame
        rulings = self.vault.standing_rulings()
        if not rulings:
            return frame
        # Compare the ruling BODY, not the tagged block: the "[CANON RULINGS...]"
        # header is added here and never appears in the overview, so testing the
        # whole string always missed and appended a duplicate copy.
        body = rulings.split("\n", 1)[-1].strip()
        if body and body in frame:
            return frame
        return f"{frame}\n\n{rulings}" if frame else rulings

    def _build_world_frame(self, chain_ids: List[str]) -> str:
        parts = []
        if self.vault:
            overview = self.vault.world_overview()
            if overview:
                parts.append(overview)
            calendar = self.vault.calendar_rules()
            if calendar:
                parts.append(calendar)
        # The naming conventions are NOT added here. They are appended after the
        # cap by _with_naming, because anything added here is subject to
        # truncation and they were being cut every time.
        return "\n\n".join(parts)

    def _build_locale(self, locale_id: Optional[str]) -> str:
        if not locale_id:
            return ""
        chain = self._containment_chain(locale_id)
        if not chain:
            return ""
        parts = []
        for record in chain:
            block = self._entity_block(record)
            if self.vault and record.get("name"):
                excerpt = self.vault.page_excerpt(record["name"])
                if excerpt:
                    block += "\n" + excerpt
            parts.append(block)
        return "\n".join(parts)

    def _build_lineage(self, anchor_id: Optional[str]) -> str:
        if not anchor_id:
            return ""
        record = self.registry.get_element(anchor_id)
        if not record:
            return ""
        parts = [self._entity_block(record)]
        facts = self.registry.query_graph(anchor_id, depth=2)
        if facts:
            parts.append("Relational facts:")
            parts.extend(f"  • {fact}" for fact in facts)
        return "\n".join(parts)

    def _cited_page_names(self, passage: str, anchor_id: Optional[str] = None) -> List[str]:
        """
        Canon pages whose text is needed to verify this passage, most specific first.

        Three sources, in priority order:

        1. The anchor's own page. The entity being audited was generated FROM it,
           so it is the page most likely to contain the fact under test — and it
           is frequently not named in the prose at all. The Litany never writes
           "The First Truth of the Unbroken Thread", yet that page is where its
           canon description lives.
        2. Pages the passage names outright. At audit time references are bare
           names, since ObsidianSync only adds wikilinks afterwards.
        3. Nothing else. An unrelated canon page is noise that costs budget.

        Matching is on word boundaries: a substring test let "Log" — the vault's
        operations log — match on "technological".
        """
        if not self.vault:
            return []

        selected: List[str] = []

        def consider(name: str) -> None:
            if not name or name.lower() in _NON_CANON_SOURCES:
                return
            if any(name.lower() == chosen.lower() for chosen in selected):
                return
            # A shorter name already covered by a selected one adds nothing.
            if any(name.lower() in chosen.lower() for chosen in selected):
                return
            selected.append(name)

        entries = [e for e in self.vault.roster()
                   if e["status"] == "canon" and e["name"]
                   and not e["gist"].lower().startswith("hub")]

        by_name = {e["name"].strip().lower(): e["name"] for e in entries}

        def consider_entity(entity_id: Optional[str]) -> None:
            record = self.registry.get_element(entity_id) if entity_id else None
            name = (record or {}).get("name")
            if name and name.strip().lower() in by_name:
                consider(by_name[name.strip().lower()])

        # 1. the anchor's own page, then the entity it was generated FROM.
        #    The source matters most and is the one a passage rarely names: the
        #    Litany never writes "The First Truth of the Unbroken Thread", yet
        #    that page holds its canon description and Corin's reveal.
        if anchor_id:
            consider_entity(anchor_id)
            record = self.registry.get_element(anchor_id) or {}
            consider_entity((record.get("stub_metadata") or {}).get("source_id"))
            for tag in record.get("tags", []):
                if tag.startswith("from_"):
                    consider_entity(tag[len("from_"):])

        # 2. Pages the passage names, ordered by how much it discusses them.
        #    Ranking by name LENGTH (as a specificity proxy) crowded out short but
        #    central names: "Archivist Kaelen" lost its slot to eight longer names
        #    on the very page whose central claim concerns him. Mention count is
        #    the better signal, with first appearance breaking ties.
        if passage:
            haystack = passage.lower()
            hits = []
            for name in {e["name"] for e in entries}:
                pattern = rf"(?<!\w){re.escape(name.lower())}(?!\w)"
                found = list(re.finditer(pattern, haystack))
                if found:
                    hits.append((len(found), -found[0].start(), len(name), name))
            # Most-mentioned first, then earliest, then the more specific name.
            for _, _, _, name in sorted(hits, reverse=True):
                if len(selected) >= _MAX_CITED_PAGES:
                    break
                consider(name)

        return selected[:_MAX_CITED_PAGES]

    def _build_citations(self, passage: str, anchor_id: Optional[str] = None) -> str:
        """
        Full text of the canon pages needed to verify this passage.

        Citations are evidence FOR a passage, so nothing is built without one.
        for_decoder() ignores this layer — generation is steered by the roster and
        locale — which would otherwise make this pure waste on every decode.
        """
        if not passage:
            return ""
        names = self._cited_page_names(passage, anchor_id)
        if not names:
            return ""

        blocks = []
        for name in names:
            excerpt = self.vault.page_excerpt(name, max_chars=_CITATION_CHARS_PER_PAGE)
            if excerpt.strip():
                blocks.append(excerpt)

        if not blocks:
            return ""
        body = "\n\n---\n\n".join(blocks)
        if len(body) > _CITATION_TOTAL_CHARS:
            body = body[:_CITATION_TOTAL_CHARS].rsplit("\n", 1)[0].rstrip()
        return _CITATION_HEADER + "\n\n" + body

    def _build_roster(self, req: AssemblyRequest, chain_ids: List[str]) -> str:
        lines: List[str] = []
        seen_names = set()

        def add(name: str, gist: str, status: str = ""):
            key = name.strip().lower()
            if not key or key in seen_names:
                return
            seen_names.add(key)
            suffix = f" [{status}]" if status and status != "unknown" else ""
            lines.append(f"- {name}: {gist}{suffix}")

        # Priority 1: registry entities of the same type (direct name-collision risk)
        for record in self.registry.get_all_by_type(req.element_type):
            if record.get("name"):
                add(record["name"], record.get("gist") or "", "")

        # Priority 2: graph-nearby entities of any type
        for entity_id in self._nearby_ids([req.anchor_id, req.locale_id]):
            record = self.registry.get_element(entity_id)
            if record and record.get("name"):
                add(record["name"], record.get("gist") or "", "")

        # Priority 3: the vault index (canon and draft pages)
        if self.vault:
            for entry in self.vault.roster():
                if entry["status"] == "deprecated":
                    continue
                add(entry["name"], entry["gist"], entry["status"])

        if not lines:
            return ""
        return _ROSTER_HEADER + "\n" + "\n".join(lines)

    # ── Entry point ──────────────────────────────────────────

    def assemble(self, req: AssemblyRequest) -> ContextPackage:
        chain_ids = [r["id"] for r in self._containment_chain(req.locale_id)] if req.locale_id else []
        naming_text, naming_is_canon = self._naming_conventions(chain_ids)

        directives = "\n\n".join(p for p in [req.imprint.strip(), req.directives.strip()] if p)

        return ContextPackage(
            world_frame=self._with_rulings(
                self._cap(self._build_world_frame(chain_ids),
                          req.budget_tokens, _LAYER_BUDGET["world_frame"])),
            # Not capped, and not folded into the frame: see ContextPackage.naming.
            naming=naming_text,
            naming_is_canon=naming_is_canon,
            locale=self._cap(self._build_locale(req.locale_id), req.budget_tokens, _LAYER_BUDGET["locale"]),
            lineage=self._cap(self._build_lineage(req.anchor_id), req.budget_tokens, _LAYER_BUDGET["lineage"]),
            roster=self._cap(self._build_roster(req, chain_ids), req.budget_tokens, _LAYER_BUDGET["roster"]),
            directives=directives,
            citations=self._build_citations(req.passage, req.anchor_id),
        )
