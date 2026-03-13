class WorldStateKeeper:
    """Tracks the authoritative 'present reality' (who is alive, what is broken)."""
    def __init__(self):
        # A mock dictionary database representing the active scene's reality
        self.state = {
            "Goblin Cave": {
                "entities": ["Player", "Goblin", "Bartender"],
                "hazards": ["Slippery floor"],
                "lighting": "Dim"
            }
        }

    def get_reality(self, context_key: str) -> dict:
        """Fetch the current authoritative state for a location or entity."""
        return self.state.get(context_key, {"entities": [], "hazards": [], "lighting": "Unknown"})

    def update_reality(self, context_key: str, updates: dict):
        """Merges new facts into the authoritative state."""
        if context_key not in self.state:
            self.state[context_key] = {}
        self.state[context_key].update(updates)
        print(f"[WorldStateKeeper] Reality updated for '{context_key}': {updates}")

class ContinuityArchivist:
    """Stores and retrieves past scenes to maintain long-term campaign canon."""
    def __init__(self):
        # Simulated Vector Database (ChromaDB architecture)
        self.memory_store = []

    def save_scene(self, scene_data: str):
        self.memory_store.append(scene_data)
        print(f"[ContinuityArchivist] Saved to long-term memory canon.")
        
    def retrieve_context(self, query: str) -> list:
        # Placeholder for Semantic Search
        print(f"[ContinuityArchivist] Retrieving historical context for: '{query}'")
        return [f"Historical memory matching: {query}"]
