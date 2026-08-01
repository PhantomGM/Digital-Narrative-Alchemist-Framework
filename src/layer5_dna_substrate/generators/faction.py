import random

# Each axis and the values it can take. Order matters: it is the order the
# segments appear in the DNA string, and existing decoders read positionally.
FACTION_AXES = {
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
    "X": [f"X{i}" for i in range(1, 7)],
}


def generate_faction_dna(seed=None, **pins):
    """
    Generates a DNA string for a Faction.

    Every axis is an independent uniform pick, so unlike the NPC genome this one
    never had a distribution problem — there is nothing here being averaged.

    Seedable and axis-pinnable, matching the newer generators. A pin names an
    axis and gives one of its values, either bare or prefixed: T=3, T="T3" and
    t=3 all pin the same thing. That is what lets a caller fix what is already
    known about a faction and leave the rest to vary.
    """
    rng = random.Random(seed)

    resolved = {}
    for key, value in pins.items():
        axis = key.upper()
        if axis not in FACTION_AXES:
            raise ValueError(f"Unknown faction pin '{key}'. "
                             f"Valid: {sorted(FACTION_AXES)}")
        options = FACTION_AXES[axis]
        # Accept "T3", "3" or 3 -- the prefix is noise the caller should not
        # have to repeat, and G/L/SC pad their numbers, which is easy to miss.
        candidate = str(value)
        if candidate not in options:
            bare = candidate[len(axis):] if candidate.upper().startswith(axis) \
                else candidate
            matches = [o for o in options if o[len(axis):].lstrip("0") ==
                       bare.lstrip("0") and bare != ""]
            if len(matches) != 1:
                raise ValueError(f"Pin '{key}'={value!r} not in {options}")
            candidate = matches[0]
        resolved[axis] = candidate

    segments = [resolved.get(axis) or rng.choice(options)
                for axis, options in FACTION_AXES.items()]
    return "-".join(segments)
