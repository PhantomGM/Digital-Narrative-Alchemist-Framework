import random

def generate_realm_dna():
    """Generates a DNA string for a political Realm."""
    conf = random.randint(1, 10)
    country_counts = {1: 6, 2: 6, 3: 10, 4: 4, 5: 6, 6: 5, 7: 8, 8: 1, 9: 5, 10: 5}
    num_countries = country_counts.get(conf, 6)
    status = [random.randint(1, 6) for _ in range(num_countries)]
    conflict = random.randint(1, 6)
    return f"REALM[CONF:{conf};STATUS:[{','.join(map(str, status))}];CONFLICT:{conflict}]"
