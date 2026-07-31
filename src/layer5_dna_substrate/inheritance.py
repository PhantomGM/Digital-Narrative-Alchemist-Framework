import json
from typing import Dict, Any

class InheritanceEngine:
    """
    The Multi-Directional Inheritance Engine.
    Queries the DNA Registry for linked entities and compiles their relevant phenotypes
    into a structured "constraint package" to guide future generation.
    """
    def __init__(self, registry):
        self.registry = registry

    def _extract_core_traits(self, entity: dict) -> str:
        """Helper to boil down a massive phenotype into actionable constraints."""
        tags = ", ".join(entity.get('tags', []))
        header = f"[Type: {entity.get('type')}] [Tags: {tags}]"

        # Prefer the structured summary/gist written by the decoder's tail —
        # it compresses drives, secrets, and relationships, which is exactly
        # what constraints need. Raw phenotype truncation is the legacy path
        # (its first 500 chars are mostly name and appearance).
        name = entity.get('name')
        gist = entity.get('gist')
        summary = entity.get('summary')
        if gist or summary:
            parts = [header]
            if name:
                parts.append(f"Name: {name}")
            if gist:
                parts.append(gist)
            if summary:
                parts.append(summary)
            return "\n".join(parts)

        phenotype = entity.get('phenotype', '')
        return f"{header}\n{phenotype[:500]}..."

    def compile_constraints(self, origin_ids: list[str]) -> str:
        """
        Takes a list of IDs being used as the "basis" for a new generation.
        Fetches their profiles and any immediate linked relatives to build context.

        Enhanced with graph-augmented retrieval: includes deterministic relational
        facts alongside phenotype excerpts.
        """
        if not self.registry:
            return "No Registry Linked - No Constraints."

        if not origin_ids:
            return "No Origin Entities provided."

        constraint_blocks = []

        for origin_id in origin_ids:
            entity = self.registry.get_element(origin_id)
            if not entity:
                continue

            block = f"--- CONTEXT ENTITY (ID: {origin_id}) ---\n"
            block += self._extract_core_traits(entity) + "\n"

            # Fetch relationships (using legacy-compatible ID-only method)
            # Registry edge semantics: link_elements(A, B, "parent") makes A the
            # parent OF B, stored as edges[A]["parent"]=[B] and edges[B]["child"]=[A].
            # So an entity's actual parents sit on its "child" edges and its
            # children on its "parent" edges.
            links = self.registry.get_link_ids(origin_id)

            # DOWNWARD (Inheriting from Parents)
            if links.get("child"):
                block += f"\n  -> Inheriting from PARENT Entities:\n"
                for parent_id in links["child"]:
                    parent = self.registry.get_element(parent_id)
                    if parent:
                        block += f"     - {self._extract_core_traits(parent)}\n"

            # SIDEWAYS (Influenced by Peers)
            if links.get("peer"):
                block += f"\n  -> Influenced by PEER Entities:\n"
                for peer_id in links["peer"]:
                    peer = self.registry.get_element(peer_id)
                    if peer:
                        block += f"     - {self._extract_core_traits(peer)}\n"

            # UPWARD (Incorporating lore from Children)
            if links.get("parent"):
                block += f"\n  -> Must incorporate lore from CHILD Entities:\n"
                for child_id in links["parent"]:
                    child = self.registry.get_element(child_id)
                    if child:
                        block += f"     - {self._extract_core_traits(child)}\n"

            # Graph-Augmented Facts (deterministic relational truths)
            graph_facts = self.registry.query_graph(origin_id, depth=2)
            if graph_facts:
                block += f"\n  -> Deterministic Relational Facts (Graph):\n"
                for fact in graph_facts:
                    block += f"     • {fact}\n"

            constraint_blocks.append(block)

        if not constraint_blocks:
            return ""

        final_constraints = "=== INHERITANCE CONSTRAINTS ===\n"
        final_constraints += "The following entities are related to the current generation task.\n"
        final_constraints += "You MUST adapt the output to respect, align with, or logically react to these traits:\n\n"
        final_constraints += "\n\n".join(constraint_blocks)
        final_constraints += "\n==============================="

        return final_constraints

