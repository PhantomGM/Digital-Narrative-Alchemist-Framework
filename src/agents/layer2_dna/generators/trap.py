import random

def generate_trap_dna():
    """Generates a detailed, multi-line DNA string for a Trap."""
    difficulty, complexity, severity = random.randint(1, 9), random.randint(1, 9), random.randint(1, 9)
    trap_type = random.choice(["mechanical", "magical", "environmental", "puzzle", "natural", "psychological"])
    
    mods = {
        'D_M': round(random.uniform(0.1, 2.0), 1),
        'C_M': round(random.uniform(0.1, 2.0), 1),
        'T_M': round(random.uniform(0.1, 2.0), 1)
    }

    mech_traits = {"TRG": random.randint(1, 8), "RST": random.randint(1, 5), "DIS": random.randint(1, 6), "BYP": random.randint(1, 7)}
    eff_traits = {"DAM": random.randint(1, 13), "CON": random.randint(1, 13), "DUR": random.randint(1, 7), "TAR": random.randint(1, 6)}
    cont_traits = {"LOC": random.randint(1, 10), "CRE": random.randint(1, 10), "PUR": random.randint(1, 9)}
    
    chains = {"MECH": "TRG>RST>DIS", "EFF": "DAM>CON>DUR", "CONT": "LOC>CRE>PUR"}
    evo_types = ["RISING", "STABLE", "ACCELERATING", "DESCENDING", "FLUCTUATING", "CLIMACTIC"]

    evo = {
        'D': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'E': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'C': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}"
    }

    return (f"TRAP{{v1.0[{difficulty}/{complexity}/{severity}]}}"
            f"<D_M:{mods['D_M']},C_M:{mods['C_M']},T_M:{mods['T_M']}>#{trap_type}\n"
            f"MECH{{{';'.join([f'{k}:{v}' for k, v in mech_traits.items()])}}}\n"
            f"EFF{{{';'.join([f'{k}:{v}' for k, v in eff_traits.items()])}}}\n"
            f"CONT{{{';'.join([f'{k}:{v}' for k, v in cont_traits.items()])}}}\n"
            f"CHAIN{{MECH:{chains['MECH']};EFF:{chains['EFF']};CONT:{chains['CONT']}}}\n"
            f"EVO{{D:{evo['D']};E:{evo['E']};C:{evo['C']}}}")
