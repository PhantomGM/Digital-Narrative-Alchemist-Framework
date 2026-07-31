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

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.vault_adapter import VaultAdapter

# Fraction of the token budget granted to each capped layer
_LAYER_BUDGET = {"world_frame": 0.25, "locale": 0.25, "lineage": 0.20, "roster": 0.30}
_CHARS_PER_TOKEN = 4

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


@dataclass
class ContextPackage:
    world_frame: str = ""
    locale: str = ""
    lineage: str = ""
    roster: str = ""
    directives: str = ""

    def _sections(self, include_directives: bool) -> List[str]:
        parts = []
        if self.world_frame:
            parts.append("## WORLD FRAME (applies to everything)\n" + self.world_frame)
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
        The authoritative-truth subset (world frame + locale + roster),
        for use as the ConsistencyAuditor's world state.
        """
        parts = []
        if self.world_frame:
            parts.append(self.world_frame)
        if self.locale:
            parts.append(self.locale)
        if self.roster:
            parts.append(self.roster)
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
        """The linguistic profile linked to the locale chain, else the first one."""
        linguistics = self.registry.get_all_by_type("linguistic")
        if not linguistics:
            return None
        chain_set = set(chain_ids)
        for record in linguistics:
            links = self.registry.get_link_ids(record["id"])
            neighbors = set(links.get("parent", []) + links.get("peer", []) + links.get("child", []))
            if neighbors & chain_set:
                return record
        return linguistics[0]

    # ── Layers ───────────────────────────────────────────────

    def _build_world_frame(self, chain_ids: List[str]) -> str:
        parts = []
        if self.vault:
            overview = self.vault.world_overview()
            if overview:
                parts.append(overview)
            calendar = self.vault.calendar_rules()
            if calendar:
                parts.append(calendar)
        linguistic = self._linguistic_anchor(chain_ids)
        if linguistic:
            parts.append("Naming conventions:\n" + self._entity_block(linguistic))
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

        directives = "\n\n".join(p for p in [req.imprint.strip(), req.directives.strip()] if p)

        return ContextPackage(
            world_frame=self._cap(self._build_world_frame(chain_ids), req.budget_tokens, _LAYER_BUDGET["world_frame"]),
            locale=self._cap(self._build_locale(req.locale_id), req.budget_tokens, _LAYER_BUDGET["locale"]),
            lineage=self._cap(self._build_lineage(req.anchor_id), req.budget_tokens, _LAYER_BUDGET["lineage"]),
            roster=self._cap(self._build_roster(req, chain_ids), req.budget_tokens, _LAYER_BUDGET["roster"]),
            directives=directives,
        )
