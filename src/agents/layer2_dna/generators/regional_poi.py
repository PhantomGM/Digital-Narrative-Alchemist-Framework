import random

def generate_regional_poi_dna():
    """Generates an enhanced, detailed DNA string for a Regionally Significant POI."""
    size, complexity, significance = random.randint(1, 9), random.randint(1, 9), random.randint(1, 9)
    poi_type = random.choice(["dungeon", "ruin", "tower", "anomaly", "landmark", "lair"])

    ntr = {
        "TYP": random.randint(1, 5),    # Nature Type
        "FRM": random.randint(1, 8),    # Form
        "CON": random.randint(1, 6),    # Condition
        "VIS": random.randint(1, 4),    # Visibility
        "MAT": random.randint(1, 8)     # Material
    }
    org = {
        "CRT": random.randint(1, 7),    # Creator
        "AGE": random.randint(1, 4),    # Age
        "PUR": random.randint(1, 8),    # Original Purpose
        "LGC": random.randint(1, 5)     # Legacy
    }
    eff = {
        "ENV": random.randint(1, 6),    # Environmental Effect
        "REP": random.randint(1, 6),    # Reputation
        "ACC": random.randint(1, 4)     # Accessibility
    }
    intr = {
        "INH": random.randint(1, 7),    # Inhabitants
        "THR": random.randint(1, 6),    # Primary Threat
        "TRS": random.randint(1, 6),    # Treasure/Reward
        "IC": random.randint(1, 10)     # Internal Conflict
    }
    sec = {
        "KND": random.randint(1, 6)     # Kind of Secret
    }
    evo = {
        "TRT": random.randint(1, 5),    # Evolving Trait
        "PTN": random.randint(1, 4)     # Pattern
    }

    return (f"REG_POI{{v1.1[{size}/{complexity}/{significance}]}}#{poi_type}\n"
            f"NTR{{{','.join([k+str(v) for k, v in ntr.items()])}}}\n"
            f"ORG{{{','.join([k+str(v) for k, v in org.items()])}}}\n"
            f"EFF{{{','.join([k+str(v) for k, v in eff.items()])}}}\n"
            f"INTR{{{','.join([k+str(v) for k, v in intr.items()])}}}\n"
            f"SEC{{{','.join([k+str(v) for k, v in sec.items()])}}}\n"
            f"EVO{{{','.join([k+str(v) for k, v in evo.items()])}}}")
