import random

# The paired axis: each entry offers two opposed expressions of one trait.
LNC_TRAITS = [
    ("B", "C"), ("R", "O"), ("L", "T"), ("F", "I"), ("S", "X"),
    ("P", "M"), ("D", "U"), ("G", "H"), ("Y", "W"), ("E", "A"),
    ("N", "V"), ("K", "Q"), ("Z", "B"), ("O", "P"), ("C", "H"),
    ("R", "L"), ("A", "S"), ("D", "A"), ("A", "H"), ("I", "C")
]
GNE_TRAITS = "HCKGLJMFBUSIRTADVYX"

# The decoder reads the headline scores as bands of three
# (decoders/npc.md): 9-7 Lawful, 6-4 Neutral, 3-1 Chaotic, and the same
# split for Good/Neutral/Evil. Choosing the band first and the score
# within it second is what makes all nine alignments equally likely.
LNC_BANDS = {"L": (7, 8, 9), "N": (4, 5, 6), "C": (1, 2, 3)}
GNE_BANDS = {"G": (7, 8, 9), "N": (4, 5, 6), "E": (1, 2, 3)}


def _resolve_axis(rng, bands, axis, letter, score, name):
    """Pin by letter, pin by exact score, or roll band-then-score."""
    if letter is not None and score is not None:
        raise ValueError(
            f"Pin '{name}' and '{name}_score' together are contradictory; "
            f"give one.")
    if score is not None:
        # bool is an int subclass: True would pass 1 <= v <= 9 and land in
        # the DNA literally, e.g. (True/5).
        if isinstance(score, bool) or not (isinstance(score, int)
                                           and 1 <= score <= 9):
            raise ValueError(f"Pin '{name}_score' must be an int 1-9, "
                             f"got {score!r}")
        return score
    if letter is not None:
        key = str(letter).upper()
        if key not in bands:
            raise ValueError(f"Pin '{name}'={letter!r} must be one of "
                             f"{sorted(bands)}")
        return rng.choice(bands[key])
    return rng.choice(bands[rng.choice(sorted(bands))])


def generate_npc_dna(seed=None, **pins):
    """
    Generates a detailed Personality DNA code for an NPC.

    The two headline scores used to be the ROUNDED MEAN of the 20 paired and
    19 unpaired trait scores. That quietly destroyed the 81-point alignment
    grid. Each trait score is a fair 1-9, but the mean of twenty of them has a
    standard error near 0.58, so rounding put it on 5 about 59% of the time:
    over 20,000 rolls, 35% of NPCs came out exactly (5/5), 98% fell inside the
    3x3 Neutral core, only 25 of the 81 points ever appeared, and a 1 or a 9
    never appeared at all. Adding traits made it worse, not better, because
    more samples cluster harder.

    So the headline is now drawn the way the decoder already reads it: pick the
    alignment, then pick one of the three scores in its band. Every alignment
    is 1/9, every point 1/81, and True Neutral is 1.2% rather than 35%.

    The 39 trait scores stay independently random. That is deliberate — it is
    what makes two Lawful Good NPCs behave differently, and the decoder is told
    to read traits *through* the alignment rather than expecting them to agree.

    Pins: `lnc`/`gne` take a letter (L/N/C, G/N/E) to fix the alignment while
    leaving the exact score and every trait free; `lnc_score`/`gne_score` take
    an int 1-9 to fix the point exactly. Individual traits are not pinnable by
    letter because the pair letters are not unique — 'B' appears in both
    ("B","C") and ("Z","B"), 'A' in four pairs — so a letter does not identify
    an axis. Pass a `seed` to reproduce a whole NPC.
    """
    rng = random.Random(seed)

    valid = {"lnc", "gne", "lnc_score", "gne_score"}
    unknown = set(pins) - valid
    if unknown:
        raise ValueError(f"Unknown npc pin(s) {sorted(unknown)}. "
                         f"Valid: {sorted(valid)}")

    lnc_headline = _resolve_axis(rng, LNC_BANDS, "lnc", pins.get("lnc"),
                                 pins.get("lnc_score"), "lnc")
    gne_headline = _resolve_axis(rng, GNE_BANDS, "gne", pins.get("gne"),
                                 pins.get("gne_score"), "gne")

    lnc_dna_parts = []
    for pair in LNC_TRAITS:
        chosen_trait = rng.choice(pair)
        lnc_score = rng.randint(1, 9)
        intensity = rng.randint(1, 5)
        lnc_dna_parts.append(f"{lnc_score}{chosen_trait[0]}{intensity}")

    gne_dna_parts = []
    for trait in GNE_TRAITS:
        gne_dna_parts.append(f"{trait[0]}{rng.randint(1, 9)}")

    return (f"({lnc_headline}/{gne_headline}) {','.join(lnc_dna_parts)}"
            f" - {','.join(gne_dna_parts)}")
