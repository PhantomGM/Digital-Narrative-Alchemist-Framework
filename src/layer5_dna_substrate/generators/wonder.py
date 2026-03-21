import random

def generate_world_wonder_dna(seed=None, compact=False):
    """Generates a DNA string for a World Wonder."""
    rng = random.Random(seed)
    r = rng.randint
    
    size, age, impact = r(1, 9), r(1, 9), r(1, 9)
    wonder_type = rng.choice(["natural", "structure", "magical", "ruin", "celestial", "living"])

    nature = {"TYP": r(1, 6), "FRM": r(1, 8), "CON": r(1, 6), "VIS": r(1, 4)}
    origin = {"ERA": r(1, 5), "CRT": r(1, 6), "DSC": r(1, 4), "LEG": r(1, 6)}
    effect = {"ENV": r(1, 6), "MAG": r(1, 6), "CUL": r(1, 6), "POL": r(1, 4), "ACC": r(1, 4), "SYNC": r(1, 4)}
    secret = {"KND": r(1, 8), "IMP": r(1, 6), "PRX": r(1, 4), "GDN": r(0, 5)}

    blocks = [
        f"WONDER{{v1.1[{size}/{age}/{impact}]}}#{wonder_type}",
        f"NTR{{{','.join(k+str(v) for k,v in nature.items())}}}",
        f"ORG{{{','.join(k+str(v) for k,v in origin.items())}}}",
        f"EFF{{{','.join(k+str(v) for k,v in effect.items())}}}",
        f"SCR{{{','.join(k+str(v) for k,v in secret.items())}}}"
    ]
    dna = "\n".join(blocks)
    return dna.replace("\n", ";") if compact else dna
