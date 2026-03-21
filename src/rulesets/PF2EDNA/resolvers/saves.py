from typing import Dict, Any

from .dice import parse_and_roll
from .combat import determine_degree_of_success, DegreeOfSuccess

def resolve_save(save_modifier: int, dc: int, save_type: str = "reflex") -> Dict[str, Any]:
    """Resolves a saving throw with PF2E 4 degrees of success."""
    roll_res = parse_and_roll("1d20")
    total_mod = save_modifier
    degree = determine_degree_of_success(roll_res["rolls"][0], total_mod, dc)
    
    return {
        "roll": roll_res["rolls"][0],
        "modifier": total_mod,
        "total": roll_res["rolls"][0] + total_mod,
        "dc": dc,
        "save_type": save_type,
        "degree_of_success": degree
    }

# --- SMOKE TEST ---
if __name__ == "__main__":
    res = resolve_save(5, 15, "fortitude")
    print(f"Fortitude Save vs DC 15 with +5: {res['total']} -> {res['degree_of_success']}")
    assert res["save_type"] == "fortitude"
    print("Smoke tests passed.")
