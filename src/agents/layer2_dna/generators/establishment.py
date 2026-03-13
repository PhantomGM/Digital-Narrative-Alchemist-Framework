import random

def generate_establishment_dna(seed=None, compact=False):
    """Generates a DNA string for an Establishment (Tavern, Shop, etc.)."""
    rng = random.Random(seed)
    r = rng.randint

    atmosphere = {"ATM": r(1, 8), "SND": r(1, 4), "CRO": r(1, 6)}
    offerings = {"GDS": r(1, 6), "SRV": r(1, 6), "LGL": r(1, 4), "CST": r(1, 4)}
    personnel = {"STA": r(1, 6), "OWN": r(1, 6), "CLT": r(1, 6), "POW": r(1, 6)}
    secrets = {"HID": r(1, 6), "SEC": r(1, 6), "TRP": r(0, 5), "BLK": r(1, 4)}
    evolution = {"HIS": r(1, 4), "EVO": r(1, 6), "INT": r(1, 4)}
    chain = {"CH1": r(0, 4), "CH2": r(0, 4), "CH3": r(0, 4)}

    blocks = [
        f"ATMOS{{{','.join(k+str(v) for k,v in atmosphere.items())}}}",
        f"OFFERINGS{{{','.join(k+str(v) for k,v in offerings.items())}}}",
        f"PERSONNEL{{{','.join(k+str(v) for k,v in personnel.items())}}}",
        f"SECRETS{{{','.join(k+str(v) for k,v in secrets.items())}}}",
        f"EVO{{{','.join(k+str(v) for k,v in evolution.items())}}}",
        f"CHAIN{{{','.join(k+str(v) for k,v in chain.items())}}}"
    ]
    dna = "\n".join(blocks)
    return dna.replace("\n", ";") if compact else dna
