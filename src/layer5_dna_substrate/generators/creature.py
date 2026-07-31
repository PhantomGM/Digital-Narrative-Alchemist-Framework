import random

# ── Trait vocabularies (also the set of legal pin values per axis) ──────────
_FORMS = ["beast", "swarm", "ooze", "construct", "plant", "spirit",
          "undead", "aberrant", "hybrid", "colossus", "vermin", "avian"]
_ORIGINS = ["natural", "mutated", "magical", "aetherium-touched",
            "nanite-born", "pre-collapse-construct", "aberrant", "cursed"]
_LOCOMOTION = ["burrow", "crawl", "walk", "climb", "leap", "swim",
               "fly", "glide", "phase", "drift", "slither"]
_SENSES = ["sight", "scent", "vibration", "heat", "magic-sense",
           "echolocation", "electroreception", "none"]
_TRIGGERS = ["movement", "warmth", "sound", "blood", "magic-use",
             "light", "intrusion", "starvation", "unprovoked"]
_METHODS = ["ambush", "pursuit", "constrict", "venom", "swarm",
            "drain", "trample", "snare", "corrode", "possess", "lure"]
_DIETS = ["carnivore", "scavenger", "parasite", "grazer",
          "mineral", "magic", "flesh-and-metal", "none"]
_CYCLES = ["diurnal", "nocturnal", "crepuscular", "dormant-then-surge",
           "seasonal", "constant"]
_REPRODUCTION = ["live-birth", "eggs", "spores", "budding", "spawn-swarm",
                 "infection", "assembled", "does-not-reproduce"]
_NICHES = ["apex", "pack-predator", "ambush-predator", "scavenger",
           "parasite", "grazer", "decomposer", "invasive"]
_ANOM_SOURCES = ["none", "wild-magic", "aetherium", "nanite-slurry",
                 "golden-age-tech", "the-collapse", "unknown"]
_ABILITIES = ["none", "phasing", "regeneration", "fear-aura", "mimicry",
              "corrosion", "psychic", "swarm-mind", "energy-drain",
              "petrifaction", "invisibility", "reality-warp"]
_WEAKNESSES = ["fire", "cold", "sound", "water", "salt", "light",
               "specific-frequency", "its-own-hunger", "disruption-of-cohesion",
               "sunlight", "silence", "none-known"]
_SALVAGE = ["hide", "venom", "glands", "charged-motes", "bone",
            "none", "reactive-tissue", "core", "essence"]

_DESCRIPTOR_PAIRS = [
    ("Armored", "Fragile"), ("Silent", "Cacophonous"), ("Camouflaged", "Conspicuous"),
    ("Ambusher", "Pursuer"), ("Territorial", "Roaming"), ("Patient", "Frenzied"),
    ("Solitary", "Gregarious"), ("Sluggish", "Fleet"), ("Blind", "Keen-Sensed"),
    ("Fecund", "Barren"),
]

# Pin name -> (kind, options). "score" pins are 1-9 ints; "pick" pins are enums.
_PINS = {
    "threat": ("score", None), "prevalence": ("score", None), "sapience": ("score", None),
    "form": ("pick", _FORMS), "origin": ("pick", _ORIGINS),
    "size": ("score", None), "resilience": ("score", None),
    "locomotion": ("pick", _LOCOMOTION), "sense": ("pick", _SENSES),
    "aggression": ("score", None), "trigger": ("pick", _TRIGGERS),
    "method": ("pick", _METHODS), "diet": ("pick", _DIETS), "cycle": ("pick", _CYCLES),
    "social": ("score", None), "territory": ("score", None),
    "reproduction": ("pick", _REPRODUCTION), "niche": ("pick", _NICHES),
    "anomaly_source": ("pick", _ANOM_SOURCES), "power": ("score", None),
    "ability": ("pick", _ABILITIES), "weakness": ("pick", _WEAKNESSES),
    "salvage": ("pick", _SALVAGE),
}


def generate_creature_dna(seed=None, **pins):
    """
    Generates a Bestiary DNA string for a creature or monster.

    Unlike the NPC genome (which encodes personality on moral axes and therefore
    forces personhood onto whatever it decodes), this genome encodes ECOLOGY and
    THREAT. Its keystone is the Sapience score: at low sapience a creature has no
    goals, no morality and no inner life — only behaviour. Structure mirrors the
    Trap genome (grouped, prefixed blocks + chains + evolution): a monster is a
    hazard with a life cycle.

    Random by default. Two forms of control, for reproducing KNOWN creatures or
    steering generation:

      seed:  int for a reproducible roll (as establishment.py / wonder.py do).
      pins:  keyword overrides for any axis; the rest still rolls. Pin values are
             validated against each axis's vocabulary. Example — regenerating a
             canon mindless nanite swarm while letting its body/tactics vary:

                 generate_creature_dna(sapience=2, form="swarm",
                                       origin="nanite-born", diet="flesh-and-metal",
                                       method="swarm", aggression=8,
                                       ability="swarm-mind", weakness="specific-frequency")

    Anything the context/decoder establishes as canon overrides the DNA at decode
    time (see decoders/creature.md), so pins are for shaping, not for guaranteeing.
    """
    rng = random.Random(seed)

    # Validate pin names and values up front so typos fail loudly.
    for key, value in pins.items():
        if key not in _PINS:
            raise ValueError(f"Unknown creature pin '{key}'. Valid: {sorted(_PINS)}")
        kind, options = _PINS[key]
        if kind == "score":
            # bool is an int subclass: True would pass 1 <= v <= 9 and be
            # written into the DNA literally, e.g. [True/3/2].
            in_range = isinstance(value, int) and 1 <= value <= 9
            if isinstance(value, bool) or not in_range:
                raise ValueError(f"Pin '{key}' must be an int 1-9, got {value!r}")
        elif value not in options:
            raise ValueError(f"Pin '{key}'={value!r} not in {options}")

    def pick(key, options):
        return pins[key] if key in pins else rng.choice(options)

    def score(key, lo=1, hi=9):
        return pins[key] if key in pins else rng.randint(lo, hi)

    threat = score("threat")
    prevalence = score("prevalence")
    sapience = score("sapience")
    form = pick("form", _FORMS)
    origin = pick("origin", _ORIGINS)

    descriptors = []
    for a, b in _DESCRIPTOR_PAIRS:
        chosen = rng.choice((a, b))
        descriptors.append(f"{chosen}{rng.randint(1, 5)}")

    body = {
        "SIZ": score("size"),
        "RES": score("resilience"),
        "LOC": pick("locomotion", _LOCOMOTION),
        "SEN": pick("sense", _SENSES),
    }
    hunt = {
        "AGG": score("aggression"),
        "TRG": pick("trigger", _TRIGGERS),
        "MTH": pick("method", _METHODS),
        "DIET": pick("diet", _DIETS),
        "CYC": pick("cycle", _CYCLES),
    }
    eco = {
        "SOC": score("social"),
        "TER": score("territory"),
        "RPR": pick("reproduction", _REPRODUCTION),
        "NCH": pick("niche", _NICHES),
    }
    anomaly = {
        "SRC": pick("anomaly_source", _ANOM_SOURCES),
        "PWR": score("power"),
        "PWK": pick("ability", _ABILITIES),
        "WKN": pick("weakness", _WEAKNESSES),
        "USE": pick("salvage", _SALVAGE),
    }

    chains = "BODY:SIZ>RES>LOC;HUNT:AGG>TRG>MTH;ECO:SOC>NCH>TER"
    evo_types = ["STABLE", "SPREADING", "DWINDLING", "MUTATING", "SWARMING", "DORMANT"]
    evo = {"POP": rng.choice(evo_types), "THR": rng.choice(evo_types)}

    def block(name, d):
        return f"{name}{{{';'.join(f'{k}:{v}' for k, v in d.items())}}}"

    return (
        f"CREATURE{{v1.0[{threat}/{prevalence}/{sapience}]}} #{origin} #{form}\n"
        f"DESC{{{','.join(descriptors)}}}\n"
        f"{block('BODY', body)}\n"
        f"{block('HUNT', hunt)}\n"
        f"{block('ECO', eco)}\n"
        f"{block('ANOM', anomaly)}\n"
        f"CHAIN{{{chains}}}\n"
        f"EVO{{POP:{evo['POP']};THR:{evo['THR']}}}"
    )
