import random

class FactionSimulator:
    """Runs macro-social actors, tracking geopolitical reactions, alliances, ideology."""
    def simulate_turn(self):
        # Stub for future faction turn resolution
        pass

class EnvironmentSimulator:
    """Manages physical space, weather, terrain affordances, and hazard logic."""
    def generate_weather(self, region_phenotype: dict = None) -> str:
        conditions = ["Overcast with light rain", "Blistering heat", "Unnatural, still fog", "Crisp, clear skies"]
        return random.choice(conditions)

    def trigger_environmental_hazard(self, location_tag: str) -> dict:
        """Injects a physical obstacle into the scene."""
        hazards = [
            "A sudden structural collapse blocks the path forward.",
            "A patch of toxic, luminescent fungi begins releasing spores.",
            "The ground gives way to a hidden sinkhole."
        ]
        return {"type": "environmental_hazard", "description": random.choice(hazards)}

class EncounterDirector:
    """Analyzes the current environment and pacing to inject dynamic obstacles or combat encounters."""
    def __init__(self, pacing_target="dynamic"):
        self.pacing_target = pacing_target

    def assess_encounter_chance(self, current_pacing: str, location_danger: int = 5) -> bool:
        """Determines if the Session Director should throw an encounter at the players."""
        if current_pacing == "calm" and random.randint(1, 10) <= location_danger:
            return True
        return False

    def generate_encounter(self, context: dict) -> dict:
        """Creates a narrative or combat obstacle."""
        encounters = [
            "A rival adventuring party demands a toll.",
            "A pack of starved, mutated wolves catches your scent.",
            "A frantic merchant begs for protection from unseen pursuers."
        ]
        return {"type": "combat_or_social", "description": random.choice(encounters)}
