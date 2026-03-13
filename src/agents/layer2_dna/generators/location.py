import random

def generate_location_dna():
    """Generates a detailed, multi-line DNA string for a Location/Settlement."""
    size, population, importance = random.randint(1, 9), random.randint(1, 9), random.randint(1, 9)
    settlement_type = random.choice(["village", "town", "city", "outpost", "port-city", "fortress", "capital", "hamlet", "metropolis"])
    
    struct = {k: random.randint(10, 99) for k in "SDWAFUPQ"}
    pop = {k: random.randint(10, 99) for k in "SDACLHCM"}
    econ = {k: random.randint(10, 99) for k in "MTRPSGIL"}
    pol = {k: random.randint(10, 99) for k in "GCRFSCLI"}
    poi = {k: random.randint(10, 99) for k in "ISRDHAMC"}
    proxi = {k: random.randint(10, 99) for k in ["WILD", "TOWN", "CITY", "RUIN"]}
    
    arch = {'MAT': random.randint(1, 8), 'ROOF': random.randint(1, 8), 'CONST': random.randint(1, 4), 'DECOR': random.randint(1, 6)}
    culture = {'CUSTOM': random.randint(1, 20), 'LAW': random.randint(1, 20), 'PUNISH': random.randint(1, 20), 'CUISINE': random.randint(1, 100)}
    
    chains = {"POP": "D>A>H", "ECON": "R>T>G", "POL": "G>R>S"}
    evo_types = ["STABLE", "RISING", "DECLINING", "FLUCTUATING", "TRANSFORMING", "STAGNANT"]

    evo = {
        'S': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'P': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'I': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}"
    }

    return (f"SETTLEMENT{{v1.1[{size}/{population}/{importance}]}}"
            f"<SP:{round(random.uniform(0.1, 2.0), 1)},PI:{round(random.uniform(0.1, 2.0), 1)},SI:{round(random.uniform(0.1, 2.0), 1)}>#{settlement_type}\n"
            f"STRUCT{{{','.join([k+str(v) for k, v in struct.items()])}}}\n"
            f"POP{{{','.join([k+str(v) for k, v in pop.items()])}}}\n"
            f"ECON{{{','.join([k+str(v) for k, v in econ.items()])}}}\n"
            f"POL{{{','.join([k+str(v) for k, v in pol.items()])}}}\n"
            f"POI{{{','.join([k+str(v) for k, v in poi.items()])}}}\n"
            f"ARCH{{{';'.join([f'{k}:{v}' for k,v in arch.items()])}}}\n"
            f"CULTURE{{{';'.join([f'{k}:{v}' for k,v in culture.items()])}}}\n"
            f"CHAIN{{POP:{chains['POP']};ECON:{chains['ECON']};POL:{chains['POL']}}}\n"
            f"PROXI{{{','.join([k+':'+str(v) for k, v in proxi.items()])}}}\n"
            f"EVO{{S:{evo['S']};P:{evo['P']};I:{evo['I']}}}")
