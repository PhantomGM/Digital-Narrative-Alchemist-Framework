import random

def generate_item_dna():
    """Generates a detailed, multi-line DNA string for a Magic Item."""
    power, complexity, rarity = random.randint(1, 9), random.randint(1, 9), random.randint(1, 9)
    item_type = random.choice(["weapon", "armor", "wand", "staff", "ring", "amulet", "potion", "scroll", "book", "relic"])
    
    phy = {k: random.randint(10, 99) for k in "MSADCWFT"}
    mag = {k: random.randint(10, 99) for k in "PEDCSART"}
    his = {k: random.randint(10, 99) for k in "OCARLFDS"}
    lor = {k: random.randint(10, 99) for k in "KFNCREIS"}
    attune = {k: random.randint(10, 99) for k in "UWCMSVPR"}
    
    chains = {"USE": "P>E>C", "MAG": "D>S>R", "ATT": "S>C>W"}
    evo_types = ["STABLE", "UNSTABLE", "ACCELERATING", "DECAYING", "FLUCTUATING", "DORMANT"]
    
    evo = {
        'P': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'M': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}"
    }

    return (f"ITEM{{v1.0[{power}/{complexity}/{rarity}]}}"
            f"<AP:{round(random.uniform(0.1, 2.0), 1)},MR:{round(random.uniform(0.1, 2.0), 1)},RE:{round(random.uniform(0.1, 2.0), 1)}>#{item_type}\n"
            f"PHY{{{','.join([k+str(v) for k, v in phy.items()])}}}\n"
            f"MAG{{{','.join([k+str(v) for k, v in mag.items()])}}}\n"
            f"HIS{{{','.join([k+str(v) for k, v in his.items()])}}}\n"
            f"LOR{{{','.join([k+str(v) for k, v in lor.items()])}}}\n"
            f"ATTUNE{{{','.join([k+str(v) for k, v in attune.items()])}}}\n"
            f"CHAIN{{USE:{chains['USE']};MAG:{chains['MAG']};ATT:{chains['ATT']}}}\n"
            f"EVO{{P:{evo['P']};M:{evo['M']}}}")
