import random

def generate_chronicle_dna():
    """Generates a detailed Chronicle DNA code for a historical era or event."""
    # Traits for Chronicle: Impact, Duration, Scale, Tragedy, Mystery, Magic, Political, Economic
    traits = [
        ("I", "D"), ("S", "T"), ("M", "A"), ("P", "E"), ("G", "L"),
        ("B", "C"), ("R", "O"), ("U", "V"), ("H", "F"), ("K", "Q")
    ]
    
    dna_parts = []
    scores = []
    for pair in traits:
        chosen_trait = random.choice(pair)
        score = random.randint(1, 9)
        intensity = random.randint(1, 5)
        scores.append(score)
        dna_parts.append(f"{score}{chosen_trait[0]}{intensity}")

    average = round(sum(scores) / len(scores)) if scores else 5
    
    return f"(CHRON/{average}) {','.join(dna_parts)}"
