import asyncio
from typing import List, Dict, Any, Optional
from layer5_dna_substrate.expansion_manager import ExpansionManager

class SpecialistAgent:
    """
    A specialist agent with a specific focus (e.g., Geography, NPCs, History).
    """
    def __init__(self, name: str, focus: str, manager: ExpansionManager):
        self.name = name
        self.focus = focus
        self.manager = manager
        self.expansion_count = 0

    async def expand_task(self, stub_id: str) -> Dict[str, Any]:
        """Expands a single stub with the agent's specialist context."""
        print(f"[{self.name}] Expanding stub {stub_id} with focus on {self.focus}...")
        
        # Add specialist context to the expansion
        specialist_context = f"You are the {self.name}, a specialist in {self.focus}. Ensure this entity's narrative emphasizes its role in the world's {self.focus}."
        
        # Pass the specialist context to the expansion manager
        phenotype = self.manager.expand_stub(stub_id, extra_context=specialist_context)
        self.expansion_count += 1
        
        return {
            "agent": self.name,
            "stub_id": stub_id,
            "status": "completed",
            "phenotype": phenotype
        }

class MultiAgentCoordinator:
    """
    Coordinates a team of specialist agents to expand the world bible.
    """
    def __init__(self, manager: ExpansionManager):
        self.manager = manager
        self.team = {
            "cartographer": SpecialistAgent("The Cartographer", "Geography and Atlas", manager),
            "social_weaver": SpecialistAgent("The Social Weaver", "NPCs and Factions", manager),
            "relic_scholar": SpecialistAgent("The Relic Scholar", "Items and Relics", manager),
            "chronicler": SpecialistAgent("The Chronicler", "History and Timeline", manager)
        }

    def _get_specialist_for_type(self, entity_type: str) -> SpecialistAgent:
        """Routes the entity type to the appropriate specialist."""
        mapping = {
            "location": "cartographer",
            "settlement": "cartographer",
            "region": "cartographer",
            "npc": "social_weaver",
            "faction": "social_weaver",
            "item": "relic_scholar",
            "relic": "relic_scholar",
            "chronicle": "chronicler",
            "event": "chronicler",
            "world": "cartographer",
            "linguistic": "social_weaver"
        }
        agent_key = mapping.get(entity_type.lower(), "social_weaver")
        return self.team[agent_key]

    async def expand_stubs_parallel(self, stub_ids: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Coordinates parallel expansion of multiple stubs using the specialist team.
        """
        tasks = []
        for stub_id in stub_ids[:limit]:
            stub_record = self.manager.registry.get_element(stub_id)
            if not stub_record:
                continue
            
            agent = self._get_specialist_for_type(stub_record["type"])
            tasks.append(agent.expand_task(stub_id))
        
        results = await asyncio.gather(*tasks)
        return results

    def generate_report(self, results: List[Dict[str, Any]]):
        """Generates a summary of the team's expansion efforts."""
        print("\n" + "="*40)
        print("🌍 WORLD EXPANSION REPORT (MULTI-AGENT)")
        print("="*40)
        for res in results:
            stub_id = res["stub_id"]
            agent = res["agent"]
            name = self.manager.registry.get_element(stub_id).get("name", "Unknown")
            print(f"✅ {name} expanded by {agent}")
        print("="*40)
        print(f"Total Expansions: {len(results)}")
        print("="*40 + "\n")
