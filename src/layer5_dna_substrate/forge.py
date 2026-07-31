from layer5_dna_substrate.generators import (
    generate_npc_dna, generate_faction_dna, generate_quest_dna, generate_item_dna,
    generate_location_dna, generate_travel_dna, generate_region_dna,
    generate_realm_dna, generate_agency_dna, generate_trap_dna, generate_creature_dna,
    generate_culture_dna, generate_lore_dna,
    generate_world_wonder_dna, generate_establishment_dna, generate_regional_poi_dna,
    WorldDNAGenerator
)
from layer5_dna_substrate.generators.chronicle import generate_chronicle_dna
from layer5_dna_substrate.generators.linguistic import generate_linguistic_dna

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
            "creature": generate_creature_dna,
            "culture": generate_culture_dna,
            "lore": generate_lore_dna,
            "wonder": generate_world_wonder_dna,
            "establishment": generate_establishment_dna,
            "regional_poi": generate_regional_poi_dna,
            "world": self._world_gen.generate_dna,
            "chronicle": generate_chronicle_dna,
            "linguistic": generate_linguistic_dna
        }

    def synthesize_element(self, element_type: str, constraint_package: str = "", **gen_kwargs) -> dict:
        """
        Master dispatcher for DNA generation. Returns a dict containing the generated DNA format.

        gen_kwargs are forwarded to the generator for the types that accept them
        (e.g. creature accepts `seed` and axis pins). Passing gen_kwargs to a
        generator that takes no arguments will raise, by design — only pass them
        for types you know support them.
        """
        element_key = element_type.lower()
        if element_key in self.generators:
            generator = self.generators[element_key]
            dna_string = generator(**gen_kwargs) if gen_kwargs else generator()
            return {"type": element_key, "dna": dna_string, "constraints": constraint_package}
        else:
            raise NotImplementedError(f"Generation for {element_type} is not yet implemented or mapped.")
