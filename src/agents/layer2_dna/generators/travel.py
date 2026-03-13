import random

def generate_travel_dna():
    """Generates a simple DNA string for a Travel Scenario."""
    return f"TRAVEL{{{random.randint(1, 5)}-{random.randint(1, 6)}-{random.randint(0, 5)}}}"
