import random

def generate_linguistic_dna():
    """
    Generates DNA for the world's language, phonetics, and naming conventions.
    Format: LING{P:X; V:X; S:X; T:X}
    P: Phonetic Pattern (1-99)
    V: Vowel Dominance (1-99)
    S: Syllabic Complexity (1-99)
    T: Tone/Atmosphere (1-99)
    """
    p = random.randint(1, 99)
    v = random.randint(1, 99)
    s = random.randint(1, 99)
    t = random.randint(1, 99)
    return f"LING{{P:{p}; V:{v}; S:{s}; T:{t}}}"
