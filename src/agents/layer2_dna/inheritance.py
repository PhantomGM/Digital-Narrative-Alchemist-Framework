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
        # For MVP, we pass the first 500 characters of the phenotype, plus tags.
        # In a fully scaled system, you might ask an LLM to summarize it first.
        phenotype = entity.get('phenotype', '')
        tags = ", ".join(entity.get('tags', []))
        summary = f"[Type: {entity.get('type')}] [Tags: {tags}]\n{phenotype[:500]}..."
        return summary

    def compile_constraints(self, origin_ids: list[str]) -> str:
        """
        Takes a list of IDs being used as the "basis" for a new generation.
        Fetches their profiles and any immediate linked relatives to build context.
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
            
            # Fetch relationships
            links = self.registry.get_links(origin_id)
            
            # DOWNWARD (Inheriting from Parents)
            if links.get("parent"):
                block += f"\n  -> Inheriting from PARENT Entities:\n"
                for parent_id in links["parent"]:
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
            if links.get("child"):
                block += f"\n  -> Must incorporate lore from CHILD Entities:\n"
                for child_id in links["child"]:
                    child = self.registry.get_element(child_id)
                    if child:
                        block += f"     - {self._extract_core_traits(child)}\n"
                        
            constraint_blocks.append(block)

        if not constraint_blocks:
            return ""

        final_constraints = "=== INHERITANCE CONSTRAINTS ===\n"
        final_constraints += "The following entities are related to the current generation task.\n"
        final_constraints += "You MUST adapt the output to respect, align with, or logically react to these traits:\n\n"
        final_constraints += "\n\n".join(constraint_blocks)
        final_constraints += "\n==============================="
        
        return final_constraints
