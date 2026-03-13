import random

def generate_quest_dna():
    """Generates a detailed, multi-line DNA string for a Quest."""
    difficulty, complexity, reward = random.randint(1, 9), random.randint(1, 9), random.randint(1, 9)
    quest_type = random.choice(["fetch", "rescue", "escort", "eliminate", "explore", "deliver", "investigate", "protect", "infiltrate"])
    
    goal = {k: random.randint(10, 99) for k in "CRESTPLH"}
    obs = {k: random.randint(10, 99) for k in "CMETPSGN"}
    rew = {k: random.randint(10, 99) for k in "MIKRSPLA"}
    narr = {k: random.randint(10, 99) for k in "TCPMHRIA"}
    motiv = {k: random.randint(10, 99) for k in "GRDSPVFJ"}
    engage = {k: random.randint(10, 99) for k in ["COMBAT", "SOCIAL", "EXPLORE", "PUZZLE"]}
    
    chains = {"OBS": "P>M>G", "REWARD": "K>I>A", "MOTIV": "D>J>P"}
    evo_types = ["RISING", "STABLE", "ACCELERATING", "DESCENDING", "FLUCTUATING", "CLIMACTIC"]
    
    evo = {
        'D': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'C': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}",
        'R': f"{random.choice(evo_types)}{sorted([random.randint(50, 99) for _ in range(4)])}"
    }

    return (f"QUEST{{v1.0[{difficulty}/{complexity}/{reward}]}}"
            f"<DI:{round(random.uniform(0.1, 2.0), 1)},CR:{round(random.uniform(0.1, 2.0), 1)},DR:{round(random.uniform(0.1, 2.0), 1)}>#{quest_type}\n"
            f"GOAL{{{','.join([k+str(v) for k, v in goal.items()])}}}\n"
            f"OBS{{{','.join([k+str(v) for k, v in obs.items()])}}}\n"
            f"REWARD{{{','.join([k+str(v) for k, v in rew.items()])}}}\n"
            f"NARR{{{','.join([k+str(v) for k, v in narr.items()])}}}\n"
            f"MOTIV{{{','.join([k+str(v) for k, v in motiv.items()])}}}\n"
            f"CHAIN{{OBS:{chains['OBS']};REWARD:{chains['REWARD']};MOTIV:{chains['MOTIV']}}}\n"
            f"ENGAGE{{{','.join([k+':'+str(v) for k, v in engage.items()])}}}\n"
            f"EVO{{D:{evo['D']};C:{evo['C']};R:{evo['R']}}}")
