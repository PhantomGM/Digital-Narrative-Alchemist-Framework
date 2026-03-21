from typing import Dict, Any

def apply_rest(hp: int, max_hp: int, status_conditions: Dict[str, int], focus_points: int, max_focus_points: int, rest_type: str = "daily") -> Dict[str, Any]:
    """
    Applies PF2E rest mechanics.
    "refocus" (10 minutes) -> Regains 1 focus point (assuming criteria met).
    "daily" (8 hours rest + prep) -> Regains level*con_mod HP (simplified to full for this MVP), all focus points, removes fatigued.
    """
    new_hp = hp
    new_focus = focus_points
    new_conditions = status_conditions.copy()
    
    if rest_type == "refocus":
        new_focus = min(max_focus_points, focus_points + 1)
        return {
            "rest_type": "refocus",
            "hp": new_hp,
            "focus_points": new_focus,
            "conditions": new_conditions,
            "notes": "Regained 1 focus point."
        }
    elif rest_type == "daily":
        new_hp = max_hp  # In full PF2E this is con_mod*level, but full heal is common house rule/simplified.
        new_focus = max_focus_points
        if "fatigued" in new_conditions:
            del new_conditions["fatigued"]
        if "doomed" in new_conditions:
            new_conditions["doomed"] -= 1
            if new_conditions["doomed"] <= 0: del new_conditions["doomed"]
            
        return {
            "rest_type": "daily",
            "hp": new_hp,
            "focus_points": new_focus,
            "conditions": new_conditions,
            "notes": "Fully rested. Regained HP, Focus, reduced doomed, removed fatigued."
        }
    else:
        raise ValueError(f"Unknown rest type: {rest_type}")

# --- SMOKE TEST ---
if __name__ == "__main__":
    conds = {"fatigued": 1, "doomed": 2, "frightened": 1}
    # Refocus
    res = apply_rest(10, 20, conds, 0, 3, "refocus")
    assert res["focus_points"] == 1
    assert "fatigued" in res["conditions"]
    
    # Daily
    res2 = apply_rest(10, 20, conds, 0, 3, "daily")
    assert res2["hp"] == 20
    assert res2["focus_points"] == 3
    assert "fatigued" not in res2["conditions"]
    assert res2["conditions"]["doomed"] == 1
    
    print("Smoke tests passed.")
