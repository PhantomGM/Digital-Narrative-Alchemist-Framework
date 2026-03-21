from typing import Dict, Any, List

def apply_damage(hp: int, amount: int, damage_type: str, resistances: Dict[str, int] = None, weaknesses: Dict[str, int] = None, immunities: List[str] = None) -> Dict[str, Any]:
    """
    Applies PF2E damage rules, including IWR (Immunities, Weaknesses, Resistances).
    Immunity negates damage completely.
    Weakness adds flat damage if the attack triggers it.
    Resistance reduces flat damage.
    """
    if immunities is None: immunities = []
    if weaknesses is None: weaknesses = {}
    if resistances is None: resistances = {}
    
    if damage_type in immunities or "all" in immunities:
        return {"old_hp": hp, "new_hp": hp, "damage_taken": 0, "notes": "Immune"}
        
    final_damage = amount
    notes = []
    
    # Apply weakness
    if damage_type in weaknesses:
        final_damage += weaknesses[damage_type]
        notes.append(f"Weakness {weaknesses[damage_type]}")
        
    # Apply resistance
    if damage_type in resistances:
        final_damage -= resistances[damage_type]
        notes.append(f"Resistance {resistances[damage_type]}")
    elif "all" in resistances:
        final_damage -= resistances["all"]
        notes.append(f"Resistance All {resistances['all']}")
        
    final_damage = max(0, final_damage)
    new_hp = max(0, hp - final_damage)
    
    return {
        "old_hp": hp,
        "new_hp": new_hp,
        "damage_taken": max(0, hp - new_hp),
        "notes": ", ".join(notes)
    }

# --- SMOKE TEST ---
if __name__ == "__main__":
    res = apply_damage(50, 10, "fire", weaknesses={"fire": 5}, resistances={"cold": 5})
    assert res["damage_taken"] == 15
    res2 = apply_damage(50, 10, "fire", immunities=["fire"])
    assert res2["damage_taken"] == 0
    res3 = apply_damage(50, 10, "slashing", resistances={"all": 3})
    assert res3["damage_taken"] == 7
    print("Smoke tests passed.")
