import uuid
from typing import Dict, Any, List, Optional, Set

class DNARegistry:
    """
    Authoritative database for typed DNA strings and their corresponding decoded phenotypes.
    Allows other agents to look up fully generated entities and elements by ID or tag.

    Supports graph-augmented retrieval: deterministic relationship queries via
    the entity graph, combined with semantic phenotype excerpts for LLM injection.
    """
    def __init__(self):
        # Format: { "id_123": { "type": "npc", "dna": "...", "phenotype": "...", "tags": [...] } }
        self._records: Dict[str, Dict[str, Any]] = {}

        # Simple inverted index for fast tag-based lookups
        self._tag_index: Dict[str, set] = {}

        # Graph edges — each edge stores the linked entity ID and an optional semantic label.
        # Format: { "id_123": { "parent": [{"id": "id_456", "label": "faction_of"}], ... } }
        self._edges: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

    def register_element(self, element_type: str, raw_dna: str, decoded_profile: str, tags: list[str] = None) -> str:
        """
        Registers a newly generated DNA element and returns its unique ID.
        """
        entity_id = str(uuid.uuid4())
        tags = tags or []
        
        record = {
            "id": entity_id,
            "type": element_type,
            "dna": raw_dna,
            "phenotype": decoded_profile,
            "tags": tags
        }
        
        self._records[entity_id] = record
        self._edges[entity_id] = {"parent": [], "child": [], "peer": []}
        self._name_cache: Dict[str, str] = {}  # id -> display name for graph queries
        
        for tag in tags:
            tag_key = tag.lower()
            if tag_key not in self._tag_index:
                self._tag_index[tag_key] = set()
            self._tag_index[tag_key].add(entity_id)
            
        print(f"[DNARegistry] Registered new {element_type} with ID: {entity_id}")
        return entity_id

    def _entity_display_name(self, entity_id: str) -> str:
        """Returns a human-readable display name for an entity (type + first tag or short ID)."""
        record = self._records.get(entity_id)
        if not record:
            return entity_id[:8]
        tags = record.get("tags", [])
        name_hint = tags[0].title() if tags else entity_id[:8]
        return f"{record['type'].title()} '{name_hint}'"

    def _edge_ids_for(self, entity_id: str, relationship: str) -> Set[str]:
        """Get a set of linked entity IDs for a given relationship direction."""
        return {edge["id"] for edge in self._edges.get(entity_id, {}).get(relationship, [])}

    def link_elements(self, entity_a: str, entity_b: str, relationship: str, label: str = None):
        """
        Links two elements. relationship can be 'parent', 'child', or 'peer'.
        An optional label provides a semantic name for the relationship
        (e.g., 'hates', 'father_of', 'trades_with', 'secret_ally_of').

        If A is parent to B, then B is child to A.
        If A is peer to B, then B is peer to A.
        """
        if entity_a not in self._records or entity_b not in self._records:
            raise KeyError("Cannot link elements that do not exist in the registry.")

        def _add_edge(source, target, rel, lbl):
            existing_ids = self._edge_ids_for(source, rel)
            if target not in existing_ids:
                self._edges[source][rel].append({"id": target, "label": lbl or rel})

        if relationship == "parent":
            _add_edge(entity_a, entity_b, "parent", label)
            _add_edge(entity_b, entity_a, "child", label)

        elif relationship == "child":
            _add_edge(entity_a, entity_b, "child", label)
            _add_edge(entity_b, entity_a, "parent", label)

        elif relationship == "peer":
            _add_edge(entity_a, entity_b, "peer", label)
            _add_edge(entity_b, entity_a, "peer", label)
        else:
            raise ValueError(f"Unknown relationship type: {relationship}. Must be parent, child, or peer.")

        label_str = f" (label: {label})" if label else ""
        print(f"[DNARegistry] Linked {entity_a[:8]} and {entity_b[:8]} as {relationship}{label_str}")

    def get_links(self, entity_id: str) -> Dict[str, List[Dict[str, str]]]:
        """Returns the dictionary of linked entities (with labels) for a given entity."""
        return self._edges.get(entity_id, {"parent": [], "child": [], "peer": []})

    def get_link_ids(self, entity_id: str) -> Dict[str, List[str]]:
        """Legacy-compatible: returns link dicts with just the IDs (no labels)."""
        links = self.get_links(entity_id)
        return {
            rel: [edge["id"] for edge in edges]
            for rel, edges in links.items()
        }

    def get_element(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific element by its ID."""
        return self._records.get(entity_id)

    def find_by_tag(self, tag: str, element_type: str = None) -> list[Dict[str, Any]]:
        """Finds elements matching a specific tag, optionally filtered by type."""
        tag_key = tag.lower()
        if tag_key not in self._tag_index:
            return []
            
        matching_ids = self._tag_index[tag_key]
        results = [self._records[eid] for eid in matching_ids]
        
        if element_type:
            results = [r for r in results if r["type"] == element_type]
            
        return results

    def get_all_by_type(self, element_type: str) -> list[Dict[str, Any]]:
        """Returns all registered elements of a specific type."""
        return [record for record in self._records.values() if record["type"] == element_type]

    # ──────────────────────────────────────────────────────────
    # Graph-Augmented Retrieval (Bucket D Enhancement)
    # ──────────────────────────────────────────────────────────

    def query_graph(self, entity_id: str, depth: int = 2) -> List[str]:
        """
        Traverses the relationship graph up to `depth` hops from the given entity.
        Returns a list of human-readable relational fact strings suitable for
        direct injection into an LLM prompt.

        Example output:
            "Faction 'Iron Guild' -[parent / faction_of]-> Npc 'Kael'"
            "Npc 'Kael' -[peer / trades_with]-> Npc 'Merchant'"
        """
        if entity_id not in self._records:
            return []

        facts: List[str] = []
        visited: Set[str] = set()
        queue: List[tuple] = [(entity_id, 0)]  # (id, current_depth)

        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)

            source_name = self._entity_display_name(current_id)
            edges = self.get_links(current_id)

            for rel_type, edge_list in edges.items():
                for edge in edge_list:
                    target_id = edge["id"]
                    label = edge.get("label", rel_type)
                    target_name = self._entity_display_name(target_id)
                    fact = f"{source_name} -[{rel_type} / {label}]-> {target_name}"
                    if fact not in facts:
                        facts.append(fact)

                    if target_id not in visited and current_depth + 1 <= depth:
                        queue.append((target_id, current_depth + 1))

        return facts

    def get_contextual_brief(self, entity_id: str, phenotype_chars: int = 400,
                             graph_depth: int = 2) -> str:
        """
        Produces a combined context block for a given entity that merges:
        1. Deterministic graph facts (from query_graph) — hard relational truths
        2. Semantic phenotype excerpt — flavor text and descriptive content

        This is the primary method downstream agents should use when they need
        context about an entity for LLM prompt injection.
        """
        record = self.get_element(entity_id)
        if not record:
            return f"Entity {entity_id} not found in registry."

        # 1. Graph facts (deterministic)
        graph_facts = self.query_graph(entity_id, depth=graph_depth)
        graph_block = "\n".join(f"  • {fact}" for fact in graph_facts) if graph_facts else "  (no known relationships)"

        # 2. Phenotype excerpt (semantic)
        phenotype = record.get("phenotype", "No decoded profile available.")
        phenotype_excerpt = phenotype[:phenotype_chars]
        if len(phenotype) > phenotype_chars:
            phenotype_excerpt += "..."

        tags = ", ".join(record.get("tags", [])) or "none"

        brief = (
            f"=== ENTITY BRIEF: {self._entity_display_name(entity_id)} ==="
            f"\nType: {record.get('type')}  |  Tags: {tags}"
            f"\n\n--- Deterministic Relationships ---"
            f"\n{graph_block}"
            f"\n\n--- Phenotype Excerpt ---"
            f"\n{phenotype_excerpt}"
            f"\n==============================================="
        )
        return brief
