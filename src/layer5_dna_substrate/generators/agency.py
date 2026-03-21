import random

def generate_agency_dna():
    """Generates a DNA string for a Government Agency."""
    agency_type = random.randint(1, 6)
    spec = random.randint(1, 12)
    reputation = random.choice(["Trusted", "Feared", "Incompetent", "Secretive", "Respected", "Corrupt"])
    return f"AGENCY[TYPE:{agency_type};SPEC:{spec};REP:{reputation}]"
