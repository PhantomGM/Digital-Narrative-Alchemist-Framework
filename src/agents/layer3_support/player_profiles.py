from typing import Dict, List

class PlayerProfileManager:
    """
    Acts as a registry for human players.
    Stores their playstyle preferences, character mappings, and specific safety
    boundaries (Lines & Veils) to be dynamically injected into the SafetyGovernor.
    """
    def __init__(self):
        self._profiles: Dict[str, dict] = {}
        
    def register_player(self, player_id: str, lines_and_veils: List[str] = None, preferences: str = ""):
        """Registers a player profile with their specific safety boundaries."""
        if lines_and_veils is None:
            lines_and_veils = []
            
        self._profiles[player_id] = {
            "lines_and_veils": lines_and_veils,
            "preferences": preferences
        }
        print(f"[PlayerProfileManager] Registered '{player_id}' with {len(lines_and_veils)} Lines & Veils.")

    def get_player_profile(self, player_id: str) -> dict:
        """Retrieves a single player's profile."""
        return self._profiles.get(player_id, {"lines_and_veils": [], "preferences": ""})
        
    def aggregate_safety_boundaries(self, active_player_ids: List[str]) -> str:
        """
        Takes a list of player IDs and returns a single concatenated string
        containing all of their specific Lines & Veils for the SafetyGovernor.
        """
        all_boundaries = set()
        for pid in active_player_ids:
            profile = self.get_player_profile(pid)
            for boundary in profile.get("lines_and_veils", []):
                 all_boundaries.add(boundary)
                 
        if not all_boundaries:
            return "No specific triggers listed. Maintain general PG-13 safety."
            
        boundary_list = "\n".join([f"- {b}" for b in all_boundaries])
        return f"STRICT CAMPAIGN BOUNDARIES (Lines & Veils):\n{boundary_list}"
