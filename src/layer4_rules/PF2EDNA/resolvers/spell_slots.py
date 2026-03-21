from typing import Dict, Any, List

def cast_spell(caster_slots: Dict[str, int], spell_level: int, tradition: str = "arcane") -> Dict[str, Any]:
    """
    Spends a spell slot of the given level for the caster.
    caster_slots format: {"1": 3, "2": 2, "-1": 1} (-1 = focus points)
    Focus spells use focus points (-1).
    """
    key = str(spell_level)
    slots_available = caster_slots.get(key, 0)
    
    if slots_available > 0:
        updated_slots = caster_slots.copy()
        updated_slots[key] -= 1
        return {"success": True, "slots": updated_slots, "message": f"Cast spell using level {spell_level} slot."}
    else:
        return {"success": False, "slots": caster_slots, "message": f"No level {spell_level} slots remaining."}

def cast_focus_spell(caster_focus_points: int) -> Dict[str, Any]:
    if caster_focus_points > 0:
        return {"success": True, "focus_points": caster_focus_points - 1, "message": "Cast focus spell."}
    return {"success": False, "focus_points": caster_focus_points, "message": "No focus points remaining."}

# --- SMOKE TEST ---
if __name__ == "__main__":
    slots = {"1": 1, "2": 0}
    res = cast_spell(slots, 1)
    assert res["success"] is True
    assert res["slots"]["1"] == 0
    res2 = cast_spell(res["slots"], 1)
    assert res2["success"] is False
    res3 = cast_focus_spell(1)
    assert res3["success"] is True
    assert res3["focus_points"] == 0
    print("Smoke tests passed.")
