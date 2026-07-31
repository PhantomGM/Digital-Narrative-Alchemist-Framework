import random

# ── Trait vocabularies (also the legal pin values per axis) ─────────────────
_SUBSISTENCE = ["scavenger", "forager", "herder", "farmer", "trader", "raider",
                "crafter", "servitor", "nomad", "miner", "salvager"]
_KINSHIP = ["family", "clan", "covenant", "caste", "commune", "lineage",
            "warband", "guild-bond", "none"]

_DWELLING = ["ruins", "crawl-wagons", "warrens", "tents", "stilt-houses", "caves",
             "hulks", "towers", "underground", "migratory-camps"]
_DRESS = ["masks", "tattoos", "robes", "scarification", "veils", "uniforms",
          "salvage-armor", "body-paint", "plain-cloth", "ceremonial-metal"]
_CRAFT = ["salvage-tech", "textiles", "weapons", "medicine", "glasswork",
          "husbandry", "cartography", "poisons", "music", "none-notable"]
_RESOURCE = ["water", "scrap", "aetherium", "food", "knowledge", "labor",
             "livestock", "relics"]

_AGE_RITE = ["trial", "pilgrimage", "first-kill", "first-salvage", "vigil",
             "scarring", "apprenticeship", "naming-rite", "none"]
_UNION = ["arranged", "chosen", "contract", "communal", "forbidden",
          "temporary", "dynastic", "none"]
_DEATH_RITE = ["reclaim-the-body", "sky-burial", "cremation", "entombment",
               "abandonment", "memory-keeping", "dissolution", "consumed-by-kin"]
_TABOO = ["the-bare-face", "waste", "naming-the-dead", "unsanctioned-magic",
          "leaving-the-clan", "iron", "spilling-water", "questioning-elders",
          "the-outsider's-touch"]

_PAST_VIEW = ["revered", "cursed", "forgotten", "exploited", "mourned", "denied"]
_MAGIC_VIEW = ["divine", "hazard", "tool", "taboo", "sickness", "gift"]
_AUTHORITY = ["elders", "merit", "strength", "ritual", "wealth", "inheritance",
              "wisdom", "none"]
_CREED = ["the-dead-watch", "waste-is-sin", "magic-is-breath", "outsiders-carry-rot",
          "the-old-world-returns", "names-hold-power", "the-land-remembers"]

_OUTSIDERS = ["hunted", "traded-with", "shunned", "adopted", "feared", "courted"]
_TONGUE = ["own-cant", "shared-trade-tongue", "secret-argot", "dying-language",
           "borrowed-speech", "sign-language"]
_FEUD = ["neighboring-clans", "a-faction", "the-terrain", "a-taboo-breach",
         "resource-scarcity", "an-old-betrayal", "none"]

_NAMING = ["trade-byname", "patronymic", "earned-name", "place-name", "clan-tag",
           "single-name", "omen-name", "deed-name"]
_TENSION = ["generational-rift", "purity-vs-adaptation", "orthodoxy-vs-reform",
            "assimilation-pressure", "resource-split", "succession-dispute",
            "faith-vs-survival"]

# Value ORIENTATIONS as paired oppositions — texture without a good/evil axis.
_VALUE_PAIRS = [
    ("Honor-bound", "Pragmatic"), ("Frugal", "Lavish"), ("Stoic", "Expressive"),
    ("Reverent", "Irreverent"), ("Hospitable", "Wary"), ("Egalitarian", "Hierarchical"),
    ("Traditional", "Adaptive"), ("Communal", "Individualist"),
    ("Merciful", "Hardened"), ("Devout", "Secular"),
]

_PINS = {
    "population": ("score", None), "cohesion": ("score", None), "openness": ("score", None),
    "subsistence": ("pick", _SUBSISTENCE), "kinship": ("pick", _KINSHIP),
    "dwelling": ("pick", _DWELLING), "dress": ("pick", _DRESS),
    "craft": ("pick", _CRAFT), "resource": ("pick", _RESOURCE),
    "age_rite": ("pick", _AGE_RITE), "union": ("pick", _UNION),
    "death_rite": ("pick", _DEATH_RITE), "taboo": ("pick", _TABOO),
    "past_view": ("pick", _PAST_VIEW), "magic_view": ("pick", _MAGIC_VIEW),
    "authority": ("pick", _AUTHORITY), "creed": ("pick", _CREED),
    "outsiders": ("pick", _OUTSIDERS), "territory": ("score", None),
    "tongue": ("pick", _TONGUE), "feud": ("pick", _FEUD),
    "naming": ("pick", _NAMING), "tension": ("pick", _TENSION),
}


def generate_culture_dna(seed=None, **pins):
    """
    Generates a DNA string for a CULTURE — a people and a way of life.

    A culture is not a faction: it has no single leader, no unified agenda, and no
    moral alignment. Decoding faction DNA as a people (the old workaround) leaked
    exactly those — a whole people stamped "True Neutral". This genome instead
    encodes the axes that define a way of living: values and taboos, kinship,
    subsistence, rites, beliefs, relations with outsiders, and naming.

    The near-keystone is Cohesion: at low cohesion, a people is fractured and
    internally various (never "the culture believes X"); at high cohesion, it is
    uniform. The decoder is told, either way, that a culture is shared and argued
    over by many, not an organisation with goals.

    Random by default; seedable and axis-pinnable like the creature generator,
    for reproducing a KNOWN people while letting the rest vary. Established
    context/canon overrides the DNA at decode time (see decoders/culture.md).
    """
    rng = random.Random(seed)

    for key, value in pins.items():
        if key not in _PINS:
            raise ValueError(f"Unknown culture pin '{key}'. Valid: {sorted(_PINS)}")
        kind, options = _PINS[key]
        if kind == "score":
            if not (isinstance(value, int) and 1 <= value <= 9):
                raise ValueError(f"Pin '{key}' must be an int 1-9, got {value!r}")
        elif value not in options:
            raise ValueError(f"Pin '{key}'={value!r} not in {options}")

    def pick(key, options):
        return pins[key] if key in pins else rng.choice(options)

    def score(key):
        return pins[key] if key in pins else rng.randint(1, 9)

    population = score("population")
    cohesion = score("cohesion")
    openness = score("openness")
    subsistence = pick("subsistence", _SUBSISTENCE)
    kinship = pick("kinship", _KINSHIP)

    values = []
    for a, b in _VALUE_PAIRS:
        values.append(f"{rng.choice((a, b))}{rng.randint(1, 5)}")

    life = {"DWL": pick("dwelling", _DWELLING), "DRS": pick("dress", _DRESS),
            "CRAFT": pick("craft", _CRAFT), "RES": pick("resource", _RESOURCE)}
    rite = {"AGE": pick("age_rite", _AGE_RITE), "UNI": pick("union", _UNION),
            "DTH": pick("death_rite", _DEATH_RITE), "TABOO": pick("taboo", _TABOO)}
    belief = {"PAST": pick("past_view", _PAST_VIEW), "MAGIC": pick("magic_view", _MAGIC_VIEW),
              "POWER": pick("authority", _AUTHORITY), "CREED": pick("creed", _CREED)}
    world = {"OUT": pick("outsiders", _OUTSIDERS), "TER": score("territory"),
             "TONGUE": pick("tongue", _TONGUE), "FEUD": pick("feud", _FEUD)}

    def block(name, d):
        return f"{name}{{{';'.join(f'{k}:{v}' for k, v in d.items())}}}"

    return (
        f"CULTURE{{v1.0[{population}/{cohesion}/{openness}]}} #{subsistence} #{kinship}\n"
        f"VALUES{{{','.join(values)}}}\n"
        f"{block('LIFE', life)}\n"
        f"{block('RITE', rite)}\n"
        f"{block('BELIEF', belief)}\n"
        f"{block('WORLD', world)}\n"
        f"NAME{{{pick('naming', _NAMING)}}}\n"
        f"TENSION{{{pick('tension', _TENSION)}}}"
    )
