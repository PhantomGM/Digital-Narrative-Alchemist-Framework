from typing import Dict, Any

PF2E_XP_THRESHOLD = 1000

def award_xp(current_xp: int, current_level: int, amount: int) -> Dict[str, Any]:
    """Awards XP to an entity and checks for level up using PF2E 1000XP rule."""
    new_xp = current_xp + amount
    levels_gained = 0
    
    while new_xp >= PF2E_XP_THRESHOLD:
        new_xp -= PF2E_XP_THRESHOLD
        levels_gained += 1
        
    return {
        "old_xp": current_xp,
        "new_xp": new_xp,
        "old_level": current_level,
        "new_level": current_level + levels_gained,
        "leveled_up": levels_gained > 0
    }

# --- SMOKE TEST ---
if __name__ == "__main__":
    res = award_xp(800, 1, 300)
    assert res["new_level"] == 2
    assert res["new_xp"] == 100
    assert res["leveled_up"] is True
    print("Smoke tests passed.")
