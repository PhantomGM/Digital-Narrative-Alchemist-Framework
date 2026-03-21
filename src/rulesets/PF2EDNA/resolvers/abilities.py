from typing import Literal

def calc_modifier(score: int) -> int:
    """Calculates PF2E ability modifier: floor((score - 10) / 2)."""
    return (score - 10) // 2

ProficiencyRank = Literal["untrained", "trained", "expert", "master", "legendary"]

def calc_proficiency_bonus(level: int, rank: ProficiencyRank) -> int:
    """Calculates PF2E TEML proficiency bonus. Untrained is +0."""
    bonuses = {
        "untrained": 0,
        "trained": 2,
        "expert": 4,
        "master": 6,
        "legendary": 8
    }
    base = bonuses.get(rank.lower(), 0)
    if base == 0:
        return 0
    return base + level

# --- SMOKE TEST ---
if __name__ == "__main__":
    assert calc_modifier(10) == 0
    assert calc_modifier(14) == 2
    assert calc_modifier(15) == 2
    assert calc_modifier(8) == -1
    
    assert calc_proficiency_bonus(5, "trained") == 7
    assert calc_proficiency_bonus(10, "untrained") == 0
    assert calc_proficiency_bonus(20, "legendary") == 28
    print("Smoke tests passed.")
