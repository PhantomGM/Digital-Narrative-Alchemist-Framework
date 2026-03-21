from layer5_dna_substrate.generators import (
    generate_npc_dna, generate_faction_dna, generate_quest_dna, generate_item_dna,
    generate_location_dna, generate_travel_dna, generate_region_dna,
    generate_realm_dna, generate_agency_dna, generate_trap_dna,
    generate_world_wonder_dna, generate_establishment_dna, generate_regional_poi_dna,
    WorldDNAGenerator
)

class ProceduralForge:
    """
    Synthesizes new world elements by generating structured DNA strings.
    Utilizes modular Python generator scripts.
    """
    def __init__(self):
        self._world_gen = WorldDNAGenerator()
        self.generators = {
            "npc": generate_npc_dna,
            "faction": generate_faction_dna,
            "quest": generate_quest_dna,
            "item": generate_item_dna,
            "location": generate_location_dna,
            "settlement": generate_location_dna,  # Alias: location generator produces SETTLEMENT{} DNA
            "travel": generate_travel_dna,
            "region": generate_region_dna,
            "realm": generate_realm_dna,
            "agency": generate_agency_dna,
            "trap": generate_trap_dna,
            "wonder": generate_world_wonder_dna,
            "establishment": generate_establishment_dna,
            "regional_poi": generate_regional_poi_dna,
            "world": self._world_gen.generate_dna
        }

    def synthesize_element(self, element_type: str, constraint_package: str = "") -> dict:
        """Master dispatcher for DNA generation. Returns a dict containing the generated DNA format."""
        element_key = element_type.lower()
        if element_key in self.generators:
            dna_string = self.generators[element_key]()
            return {"type": element_key, "dna": dna_string, "constraints": constraint_package}
        else:
            raise NotImplementedError(f"Generation for {element_type} is not yet implemented or mapped.")
