import uuid
import os
import json
import re
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

    def register_element(self, element_type: str, raw_dna: str, decoded_profile: str, tags: list[str] = None, name: str = None,
                         gist: str = None, summary: str = None) -> str:
        """
        Registers a newly generated DNA element and returns its unique ID.

        gist: one-line identity of the entity (from the phenotype's structured tail).
        summary: ~100-word compression of the phenotype, used as generation context.
        """
        entity_id = str(uuid.uuid4())
        tags = tags or []

        record = {
            "id": entity_id,
            "type": element_type,
            "name": name,
            "dna": raw_dna,
            "phenotype": decoded_profile,
            "gist": gist,
            "summary": summary,
            "tags": tags
        }
        
        self._records[entity_id] = record
        self._edges[entity_id] = {"parent": [], "child": [], "peer": []}
        
        for tag in tags:
            tag_key = tag.lower()
            if tag_key not in self._tag_index:
                self._tag_index[tag_key] = set()
            self._tag_index[tag_key].add(entity_id)
            
        print(f"[DNARegistry] Registered new {element_type} with ID: {entity_id}")
        return entity_id

    def _entity_display_name(self, entity_id: str) -> str:
        """Returns a human-readable display name for an entity (prioritize 'name' field)."""
        record = self._records.get(entity_id)
        if not record:
            return entity_id[:8]
        
        name = record.get("name")
        if name:
            return f"{record['type'].title()} '{name}'"
            
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

    def retype_element(self, entity_id: str, new_type: str, force: bool = False) -> str:
        """
        Changes an element's type and returns the type it had before.

        Needed because a stub's type is guessed from a fuzzy match on the label a
        decoder wrote ("[Chronicle] The Divine Breath"), so entities regularly
        land under the wrong type and have to be corrected once a better type
        exists. Retyping is not cosmetic: ObsidianSync files a page by type, so a
        retyped entity's page is written to a different folder.

        That is why canonized entities are refused unless force=True. Their page
        is already canon, sync will not overwrite it, and moving where new pages
        are written would leave the canon page orphaned in its old folder while a
        second page appears elsewhere. Retype a canonized entity only when you
        intend to move its page by hand as well.
        """
        record = self._records.get(entity_id)
        if record is None:
            raise KeyError(f"No element with id {entity_id!r}")

        if not isinstance(new_type, str) or not new_type.strip():
            raise ValueError(f"new_type must be a non-empty string, got {new_type!r}")
        new_type = new_type.strip().lower()

        old_type = record["type"]
        if old_type == new_type:
            return old_type

        if "canonized" in (record.get("tags") or []) and not force:
            raise ValueError(
                f"{self._entity_display_name(entity_id)} is canonized; retyping would "
                f"orphan its canon page in the old folder. Pass force=True only if you "
                f"will move the page yourself."
            )

        record["type"] = new_type
        print(f"[DNARegistry] Retyped {self._entity_display_name(entity_id)}: "
              f"{old_type} -> {new_type}")
        return old_type

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

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Folds a name to its comparison form: lowercase, punctuation-insensitive,
        and without a leading article. Decoders refer to the same entity as
        "The Scriveners Guild" and "Scriveners Guild" interchangeably, and a
        stray article should not mint a duplicate.
        """
        folded = (name or "").strip().lower()
        for article in ("the ", "an ", "a "):
            if folded.startswith(article):
                folded = folded[len(article):]
                break
        # Apostrophes vanish rather than split, so "Scrivener's" folds onto
        # "Scriveners"; other punctuation becomes a separator.
        folded = folded.replace("'", "").replace("’", "")
        return re.sub(r"[^a-z0-9]+", " ", folded).strip()

    def find_by_name(self, name: str, element_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Case-insensitive lookup of an element by its registered name or any of
        its aliases (set when entities are merged or renamed). Matching ignores
        a leading article and punctuation differences.
        """
        if not name:
            return None
        needle = self._normalize_name(name)
        if not needle:
            return None
        for record in self._records.values():
            if element_type and record["type"] != element_type:
                continue
            candidates = [record.get("name")] + list(record.get("aliases", []))
            if any(c and self._normalize_name(c) == needle for c in candidates):
                return record
        return None

    def save_to_json(self, filepath: str):
        """
        Persists the entire registry and graph to a JSON file.

        The tag index holds sets, whose iteration order varies between processes.
        Serialising them unsorted made every save rewrite most of the file: a
        three-field change produced a 128-line diff of shuffled ids, which buries
        the real change and makes world-state history unreviewable. Sorting makes
        the output a function of the content alone.
        """
        data = {
            "records": self._records,
            "edges": self._edges,
            "tag_index": {k: sorted(v) for k, v in sorted(self._tag_index.items())}
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[DNARegistry] Saved to {filepath}")

    def load_from_json(self, filepath: str):
        """Loads registry and graph from a JSON file."""
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._records = data.get("records", {})
        self._edges = data.get("edges", {})
        self._tag_index = {k: set(v) for k, v in data.get("tag_index", {}).items()}
        print(f"[DNARegistry] Loaded {len(self._records)} entities from {filepath}")

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
