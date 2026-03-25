import asyncio
from layer2_narrative.event_ledger import EventLedger, StateEvent

class WorldStateKeeper:
    """Tracks the authoritative 'present reality' (who is alive, what is broken)."""
    def __init__(self, event_ledger: EventLedger = None):
        self.event_ledger = event_ledger or EventLedger()

        # A mock dictionary database representing the active scene's reality
        self.state = {
            "Goblin Cave": {
                "entities": ["Player", "Goblin", "Bartender"],
                "hazards": ["Slippery floor"],
                "lighting": "Dim"
            }
        }
        # A dictionary to store the structural historical data generated pre-session.
        self.world_metadata = {
            "world_name": "Unknown Realm",
            "active_factions": [],
            "ruined_factions": [],
            "significant_locations": [],
            "historical_eras": [],
            "active_crises": [],
            "laws_of_magic": "Unknown",
            "timeline_year": 0
        }

    async def ingest_history_data(self, history_data: dict):
        """Ingest the extracted structural data points from the Microscope History Consensus."""
        self.world_metadata.update(history_data)
        print(f"[WorldStateKeeper] Successfully ingested historical data for world: '{self.world_metadata.get('world_name')}'")
        print(f"[WorldStateKeeper] Establishing timeline year: {self.world_metadata.get('timeline_year')}")

        # Emit a ledger event for the history ingestion via await
        await self.event_ledger.emit(StateEvent(
            event_type="HISTORY_INGESTED",
            target="world",
            delta={"world_name": history_data.get("world_name", "Unknown"),
                   "timeline_year": history_data.get("timeline_year", 0)},
            source_agent="WorldStateKeeper",
            location="global"
        ))

    def get_reality(self, context_key: str) -> dict:
        """Fetch the current authoritative state for a location or entity."""
        return self.state.get(context_key, {"entities": [], "hazards": [], "lighting": "Unknown"})

    async def get_context_window(self, context_key: str, n: int = 10) -> dict:
        """
        Returns the current reality for a location PLUS the last N state deltas
        as structured context. This ensures downstream agents (Orchestrator,
        Weaver, NPC Engines) all see the same micro-state.
        """
        reality = self.get_reality(context_key)
        recent_deltas = await self.event_ledger.render_context(n)
        return {
            "current_state": reality,
            "recent_changes": recent_deltas,
            "world_metadata": {
                "world_name": self.world_metadata.get("world_name", "Unknown"),
                "timeline_year": self.world_metadata.get("timeline_year", 0),
                "active_crises": self.world_metadata.get("active_crises", [])
            }
        }

    async def update_reality(self, context_key: str, updates: dict, source_agent: str = "WorldStateKeeper"):
        """Merges new facts into the authoritative state and emits a StateEvent delta."""
        if context_key not in self.state:
            self.state[context_key] = {}
        self.state[context_key].update(updates)
        print(f"[WorldStateKeeper] Reality updated for '{context_key}': {updates}")

        # Emit the delta to the Event Ledger via await
        await self.event_ledger.emit(StateEvent(
            event_type="UPDATE_REALITY",
            target=context_key,
            delta=updates,
            source_agent=source_agent,
            location=context_key
        ))

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
