from typing import Dict, Any

from .dice import parse_and_roll
from .combat import determine_degree_of_success

def resolve_check(skill_modifier: int, dc: int, skill_name: str) -> Dict[str, Any]:
    """Resolves a standard skill check with PF2E 4 degrees of success."""
    roll_res = parse_and_roll("1d20")
    degree = determine_degree_of_success(roll_res["rolls"][0], skill_modifier, dc)
    
    return {
        "roll": roll_res["rolls"][0],
        "modifier": skill_modifier,
        "total": roll_res["rolls"][0] + skill_modifier,
        "dc": dc,
        "skill": skill_name,
        "degree_of_success": degree
    }

# --- SMOKE TEST ---
if __name__ == "__main__":
    res = resolve_check(8, 20, "Athletics")
    print(f"Athletics check vs DC 20 with +8: {res['total']} -> {res['degree_of_success']}")
    assert res["skill"] == "Athletics"
    print("Smoke tests passed.")
