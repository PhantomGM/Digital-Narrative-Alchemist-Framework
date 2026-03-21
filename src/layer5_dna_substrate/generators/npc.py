import random

def generate_npc_dna():
    """Generates a detailed Personality DNA code for an NPC."""
    lnc_traits = [
        ("B", "C"), ("R", "O"), ("L", "T"), ("F", "I"), ("S", "X"),
        ("P", "M"), ("D", "U"), ("G", "H"), ("Y", "W"), ("E", "A"),
        ("N", "V"), ("K", "Q"), ("Z", "B"), ("O", "P"), ("C", "H"),
        ("R", "L"), ("A", "S"), ("D", "A"), ("A", "H"), ("I", "C")
    ]
    gne_traits = "HCKGLJMFBUSIRTADVYX"
    
    lnc_dna_parts = []
    lnc_scores = []
    for pair in lnc_traits:
        chosen_trait = random.choice(pair)
        lnc_score = random.randint(1, 9)
        intensity = random.randint(1, 5)
        lnc_scores.append(lnc_score)
        lnc_dna_parts.append(f"{lnc_score}{chosen_trait[0]}{intensity}")

    gne_dna_parts = []
    gne_scores = []
    for trait in gne_traits:
        gne_score = random.randint(1, 9)
        gne_scores.append(gne_score)
        gne_dna_parts.append(f"{trait[0]}{gne_score}")

    lnc_average = round(sum(lnc_scores) / len(lnc_scores)) if lnc_scores else 5
    gne_average = round(sum(gne_scores) / len(gne_scores)) if gne_scores else 5
    
    return f"({lnc_average}/{gne_average}) {','.join(lnc_dna_parts)} - {','.join(gne_dna_parts)}"
