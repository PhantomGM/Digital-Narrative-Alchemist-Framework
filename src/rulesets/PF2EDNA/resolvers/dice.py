import random
import re
from typing import TypedDict, List

class RollResult(TypedDict):
    total: int
    rolls: List[int]
    notation: str

def parse_and_roll(notation: str) -> RollResult:
    """Parses standard PF2E dice notation (e.g. 1d20+5, 2d8kh) and rolls it."""
    notation = notation.replace(" ", "").lower()
    match = re.match(r"^(\d*)d(\d+)(kh|kl)?([+-]\d+)?$", notation)
    if not match:
        # Check if it's just a flat number
        if re.match(r"^[+-]?\d+$", notation):
            val = int(notation)
            return {"total": val, "rolls": [val], "notation": notation}
        raise ValueError(f"Invalid dice notation: {notation}")
        
    num_dice_str, sides_str, keep, modifier_str = match.groups()
    num_dice = int(num_dice_str) if num_dice_str else 1
    sides = int(sides_str)
    modifier = int(modifier_str) if modifier_str else 0
    
    rolls = [random.randint(1, sides) for _ in range(num_dice)]
    
    if keep == "kh":
        kept = [max(rolls)]
    elif keep == "kl":
        kept = [min(rolls)]
    else:
        kept = rolls
        
    total = sum(kept) + modifier
    return {"total": total, "rolls": rolls, "notation": notation}

# --- SMOKE TEST ---
if __name__ == "__main__":
    res1 = parse_and_roll("1d20+7")
    print(f"1d20+7: {res1}")
    res2 = parse_and_roll("2d20kh+3")
    print(f"2d20kh+3 (Advantage equivalent): {res2}")
    res3 = parse_and_roll("2d8")
    print(f"2d8: {res3}")
    assert isinstance(res1["total"], int)
    assert 1 <= res3["total"] <= 16
    print("Smoke tests passed.")
