import random

def generate_faction_dna():
    """Generates a DNA string for a Faction."""
    dna_traits = {
        "T": [f"T{i}" for i in range(1, 8)],
        "G": [f"G{i:02}" for i in range(1, 13)],
        "M": [f"M{i}" for i in range(1, 9)],
        "P": [f"P{i}" for i in range(1, 9)],
        "S": [f"S{i}" for i in range(1, 7)],
        "O": [f"O{i}" for i in range(1, 8)],
        "N": ["N74", "N78", "N84", "N90", "N92", "N99"],
        "L": [f"L{i:02}" for i in range(1, 11)],
        "F": [f"F{i}" for i in range(1, 7)],
        "D": [f"D{i}" for i in range(1, 7)],
        "A": [f"A{i}" for i in range(1, 10)],
        "SC": [f"SC{i}" for i in range(1, 6)],
        "MZ": [f"MZ{i}" for i in range(1, 7)],
        "X": [f"X{i}" for i in range(1, 7)]
    }
    dna_segments = [random.choice(dna_traits[key]) for key in dna_traits]
    return "-".join(dna_segments)
