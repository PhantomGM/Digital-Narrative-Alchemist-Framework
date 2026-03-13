class NPCActorEngine:
    \"\"\"Drives NPC behavior, goals, off-screen activity, and tactical/social choices based on phenotype.\"\"\"
    def determine_action(self, npc_phenotype: dict, context: str):
        return {"action": "wait", "reason": "No immediate threat"}
        
class NPCPersonaEngine:
    \"\"\"Dictates how an NPC expresses themselves (voice, tone, deception, emotional posture).\"\"\"
    def generate_dialogue(self, npc_phenotype: dict, intention: str) -> str:
        return f"NPC says: I intend to {intention}"
