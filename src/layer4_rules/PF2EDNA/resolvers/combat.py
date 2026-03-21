from typing import Dict, Any, Literal

from .dice import parse_and_roll

DegreeOfSuccess = Literal["critical_success", "success", "failure", "critical_failure"]

def determine_degree_of_success(roll: int, modifier: int, dc: int) -> DegreeOfSuccess:
    """Standard PF2E 4 degrees of success logic:
    Crit Success: meets/exceeds DC+10 OR rolls a Nat 20 and meets DC
    Success: meets/exceeds DC
    Failure: misses DC
    Crit Failure: misses DC by 10+ OR rolls a Nat 1 and misses DC
    PF2E Rule: Nat 20 upgrades success by 1 step, Nat 1 downgrades by 1 step.
    """
    total = roll + modifier
    
    # Base degree
    if total >= dc + 10:
        base = "critical_success"
    elif total >= dc:
        base = "success"
    elif total <= dc - 10:
        base = "critical_failure"
    else:
        base = "failure"
        
    degrees = ["critical_failure", "failure", "success", "critical_success"]
    idx = degrees.index(base)
    
    # Nat 20/1 shifts
    if roll == 20:
        idx = min(idx + 1, 3)
    elif roll == 1:
        idx = max(idx - 1, 0)
        
    return degrees[idx]

def resolve_attack(attacker_mod: int, target_ac: int, attack_count: int = 1, agile: bool = False) -> Dict[str, Any]:
    """Resolves a PF2E attack incorporating Multiple Attack Penalty (MAP)."""
    # MAP calculations
    map_penalty = 0
    if attack_count == 2:
        map_penalty = -4 if agile else -5
    elif attack_count >= 3:
        map_penalty = -8 if agile else -10
        
    roll_res = parse_and_roll("1d20")
    total_mod = attacker_mod + map_penalty
    
    degree = determine_degree_of_success(roll_res["rolls"][0], total_mod, target_ac)
    
    return {
        "roll": roll_res["rolls"][0],
        "modifier": total_mod,
        "total": roll_res["rolls"][0] + total_mod,
        "target_ac": target_ac,
        "agile": agile,
        "attack_count": attack_count,
        "degree_of_success": degree
    }

# --- SMOKE TEST ---
if __name__ == "__main__":
    # Test standard success
    res = resolve_attack(7, 15, 1)
    print(f"Attack vs AC 15 with +7: {res['total']} -> {res['degree_of_success']}")
    
    # Test MAP
    res2 = resolve_attack(7, 15, 2)
    print(f"Second Attack vs AC 15 with +7 (MAP): {res2['total']} -> {res2['degree_of_success']}")
    
    # Test Nat 20 Upgrade logic implicitly
    assert determine_degree_of_success(20, 0, 25) == "success" # 20 vs 25 is fail, upgraded to success
    assert determine_degree_of_success(1, 10, 5) == "failure" # 1+10=11 vs DC 5 is Success, Nat 1 downgrades to Failure
    print("Smoke tests passed.")
