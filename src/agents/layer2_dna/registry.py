import uuid
from typing import Dict, Any, Optional

class DNARegistry:
    """
    Authoritative database for typed DNA strings and their corresponding decoded phenotypes.
    Allows other agents to look up fully generated entities and elements by ID or tag.
    """
    def __init__(self):
        # Format: { "id_123": { "type": "npc", "dna": "...", "phenotype": "...", "tags": ["merchant", "desert"] } }
        self._records: Dict[str, Dict[str, Any]] = {}
        
        # Simple inverted index for fast tag-based lookups
        self._tag_index: Dict[str, set] = {}
        
        # Graph edges to track relationships (Up, Down, Sideways)
        # Format: { "id_123": { "parent": ["id_456"], "child": ["id_789"], "peer": ["id_999"] } }
        self._edges: Dict[str, Dict[str, list[str]]] = {}

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
        
        for tag in tags:
            tag_key = tag.lower()
            if tag_key not in self._tag_index:
                self._tag_index[tag_key] = set()
            self._tag_index[tag_key].add(entity_id)
            
        print(f"[DNARegistry] Registered new {element_type} with ID: {entity_id}")
        return entity_id

    def link_elements(self, entity_a: str, entity_b: str, relationship: str):
        """
        Links two elements. relationship can be 'parent', 'child', or 'peer'.
        If A is parent to B, then B is child to A.
        If A is peer to B, then B is peer to A.
        """
        if entity_a not in self._records or entity_b not in self._records:
            raise KeyError("Cannot link elements that do not exist in the registry.")
            
        if relationship == "parent":
            if entity_b not in self._edges[entity_a]["parent"]:
                self._edges[entity_a]["parent"].append(entity_b)
            if entity_a not in self._edges[entity_b]["child"]:
                self._edges[entity_b]["child"].append(entity_a)
                
        elif relationship == "child":
            if entity_b not in self._edges[entity_a]["child"]:
                self._edges[entity_a]["child"].append(entity_b)
            if entity_a not in self._edges[entity_b]["parent"]:
                self._edges[entity_b]["parent"].append(entity_a)
                
        elif relationship == "peer":
            if entity_b not in self._edges[entity_a]["peer"]:
                self._edges[entity_a]["peer"].append(entity_b)
            if entity_a not in self._edges[entity_b]["peer"]:
                self._edges[entity_b]["peer"].append(entity_a)
        else:
            raise ValueError(f"Unknown relationship type: {relationship}. Must be parent, child, or peer.")
        
        print(f"[DNARegistry] Linked {entity_a[:8]} and {entity_b[:8]} as {relationship}")

    def get_links(self, entity_id: str) -> Dict[str, list[str]]:
        """Returns the dictionary of linked entity IDs for a given entity."""
        return self._edges.get(entity_id, {"parent": [], "child": [], "peer": []})

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
