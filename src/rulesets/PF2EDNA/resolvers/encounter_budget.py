from typing import Dict, Any

def get_threat_budget(party_size: int, threat: str = "moderate") -> Dict[str, Any]:
    """
    Returns the XP budget and character adjustment for a given threat level in PF2E.
    Base budget is for a party of 4.
    """
    base_budgets = {
        "trivial": {"base": 40, "adjustment": 10},
        "low": {"base": 60, "adjustment": 15},
        "moderate": {"base": 80, "adjustment": 20},
        "severe": {"base": 120, "adjustment": 30},
        "extreme": {"base": 160, "adjustment": 40}
    }
    
    threat = threat.lower()
    if threat not in base_budgets:
        raise ValueError(f"Unknown threat level: {threat}")
        
    budget = base_budgets[threat]
    diff = party_size - 4
    total_budget = budget["base"] + (diff * budget["adjustment"])
    
    return {
        "threat": threat,
        "party_size": party_size,
        "base_budget": budget["base"],
        "total_budget": total_budget
    }

# --- SMOKE TEST ---
if __name__ == "__main__":
    res = get_threat_budget(4, "moderate")
    assert res["total_budget"] == 80
    res2 = get_threat_budget(5, "severe")
    assert res2["total_budget"] == 150 # 120 + 30
    res3 = get_threat_budget(3, "low")
    assert res3["total_budget"] == 45 # 60 - 15
    print("Smoke tests passed.")
