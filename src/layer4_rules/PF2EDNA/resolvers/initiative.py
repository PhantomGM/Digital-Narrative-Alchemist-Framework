from typing import Dict, List, Any

from .skill_check import resolve_check

def roll_initiative(combatants: List[Dict[str, Any]], default_skill: str = "Perception") -> List[Dict[str, Any]]:
    """
    PF2E Initiative is usually a Perception check, or a relevant skill check if sneaking/etc.
    combatants: [{"id": "c1", "modifier": 5, "skill": "Perception", "tiebreaker": 10}]
    Tiebreaker is usually the raw modifier or Dex.
    """
    results = []
    for c in combatants:
        skill = c.get("skill", default_skill)
        mod = c["modifier"]
        # Use our skill_check logic against a generic DC (just to get the roll)
        # For initiative, we only care about the total, not success degree
        roll_res = resolve_check(mod, 10, skill)
        results.append({
            "id": c["id"],
            "initiative": roll_res["total"],
            "tiebreaker": c.get("tiebreaker", mod)
        })
        
    # Sort descending by initiative, then by tiebreaker.
    results.sort(key=lambda x: (x["initiative"], x["tiebreaker"]), reverse=True)
    return results

# --- SMOKE TEST ---
if __name__ == "__main__":
    combs = [
        {"id": "goblin", "modifier": 4, "tiebreaker": 4},
        {"id": "fighter", "modifier": 4, "tiebreaker": 2}, # Fighter loses tie breaker
        {"id": "wizard", "modifier": 10, "tiebreaker": 10}
    ]
    res = roll_initiative(combs)
    print("Initiative Order:", [x["id"] for x in res])
    assert len(res) == 3
    print("Smoke tests passed.")
