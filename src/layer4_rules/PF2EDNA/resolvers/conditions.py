from typing import Dict, Any, List

def apply_condition(current_conditions: Dict[str, int], condition_name: str, value: int = None) -> Dict[str, Any]:
    """
    Applies a status condition to an entity. Adjusts values if the condition already exists.
    e.g. Frightened 2 + Frightened 1 -> Frightened 2.
    """
    updated_conditions = current_conditions.copy()
    
    # If the condition doesn't stack or have a value
    if value is None:
        updated_conditions[condition_name] = 1
        return {"conditions": updated_conditions, "added": condition_name}
        
    # Valued conditions usually take the higher value
    current_val = updated_conditions.get(condition_name, 0)
    new_val = max(current_val, value)
    updated_conditions[condition_name] = new_val
    
    return {
        "conditions": updated_conditions,
        "added": f"{condition_name} {value}",
        "new_value": new_val
    }
    
def reduce_condition(current_conditions: Dict[str, int], condition_name: str, amount: int = 1) -> Dict[str, Any]:
    """Reduces a valued condition (like Frightened decreasing at end of turn)."""
    updated_conditions = current_conditions.copy()
    if condition_name in updated_conditions:
        updated_conditions[condition_name] -= amount
        if updated_conditions[condition_name] <= 0:
            del updated_conditions[condition_name]
            
    return {"conditions": updated_conditions}

# --- SMOKE TEST ---
if __name__ == "__main__":
    c = {}
    res = apply_condition(c, "frightened", 1)
    assert res["conditions"]["frightened"] == 1
    res2 = apply_condition(res["conditions"], "frightened", 2)
    assert res2["conditions"]["frightened"] == 2
    res3 = reduce_condition(res2["conditions"], "frightened", 1)
    assert res3["conditions"]["frightened"] == 1
    res4 = reduce_condition(res3["conditions"], "frightened", 1)
    assert "frightened" not in res4["conditions"]
    print("Smoke tests passed.")
