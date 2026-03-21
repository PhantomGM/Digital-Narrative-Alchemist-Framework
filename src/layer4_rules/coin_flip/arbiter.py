import random

class GameSystemArbiter:
    """
    The Layer IV cartridge for a pure 50/50 Coin Flip rule system.
    Used to test hot-swapping narrative outcomes.
    """
    def __init__(self):
        self.system_name = "Coin Flip"
        
    def resolve_action(self, action_intent: str, active_stats: dict = None) -> dict:
        """
        Resolves purely on a 50/50 chance regardless of stats.
        """
        print(f"[{self.system_name}] Resolving {action_intent}...")
        is_success = random.choice([True, False])
        if is_success:
            return {"success": True, "narrative_effect": "Fortune favors you!"}
        return {"success": False, "narrative_effect": "A stroke of bad luck."}
