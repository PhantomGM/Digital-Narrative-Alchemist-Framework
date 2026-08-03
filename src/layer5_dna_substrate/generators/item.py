import random

# The three governing scales are the only part of this genome whose meaning is
# recorded anywhere — they are named here because the original code named its
# own local variables. The eight keys inside each block below are undocumented;
# decoders/item.md reads those at block level rather than guessing at letters.
ITEM_SCALES = ("power", "complexity", "rarity")
ITEM_TYPES = ["weapon", "armor", "wand", "staff", "ring", "amulet", "potion",
              "scroll", "book", "relic"]
ITEM_BLOCKS = {"PHY": "MSADCWFT", "MAG": "PEDCSART", "HIS": "OCARLFDS",
               "LOR": "KFNCREIS", "ATTUNE": "UWCMSVPR"}
EVO_PATTERNS = ["STABLE", "UNSTABLE", "ACCELERATING", "DECAYING",
                "FLUCTUATING", "DORMANT"]


def generate_item_dna(seed=None, **pins):
    """
    Generates a detailed, multi-line DNA string for a Magic Item.

    Seedable and axis-pinnable, matching the other generators. The pinnable
    axes are the three governing scales and the item type -- `power`,
    `complexity`, `rarity` (1-9) and `type` -- because those are the parts whose
    meaning is actually recorded. The eight keys inside PHY, MAG, HIS, LOR and
    ATTUNE are deliberately not pinnable: nothing documents what they name, so
    a pin on one would be a pin on nothing.

    That distinction matters for the co-author path, where an author already
    knows something about an object ("a famous sword that does very little")
    and the genome should fill in the rest rather than argue with it.
    """
    rng = random.Random(seed)

    valid = set(ITEM_SCALES) | {"type"}
    unknown = set(pins) - valid
    if unknown:
        raise ValueError(f"Unknown item pin(s) {sorted(unknown)}. "
                         f"Valid: {sorted(valid)}")

    scales = {}
    for name in ITEM_SCALES:
        value = pins.get(name)
        if value is None:
            scales[name] = rng.randint(1, 9)
            continue
        # bool is an int subclass: True would pass 1 <= v <= 9 and be written
        # into the DNA literally, e.g. [True/4/7].
        if isinstance(value, bool) or not (isinstance(value, int)
                                           and 1 <= value <= 9):
            raise ValueError(f"Pin '{name}' must be an int 1-9, got {value!r}")
        scales[name] = value

    item_type = pins.get("type")
    if item_type is None:
        item_type = rng.choice(ITEM_TYPES)
    elif item_type not in ITEM_TYPES:
        raise ValueError(f"Pin 'type'={item_type!r} not in {ITEM_TYPES}")

    blocks = {name: {k: rng.randint(10, 99) for k in keys}
              for name, keys in ITEM_BLOCKS.items()}
    evo = {track: f"{rng.choice(EVO_PATTERNS)}"
                  f"{sorted(rng.randint(50, 99) for _ in range(4))}"
           for track in ("P", "M")}

    lines = [
        f"ITEM{{v1.0[{scales['power']}/{scales['complexity']}/"
        f"{scales['rarity']}]}}"
        f"<AP:{round(rng.uniform(0.1, 2.0), 1)},"
        f"MR:{round(rng.uniform(0.1, 2.0), 1)},"
        f"RE:{round(rng.uniform(0.1, 2.0), 1)}>#{item_type}"
    ]
    for name, keys in ITEM_BLOCKS.items():
        body = ",".join(f"{k}{blocks[name][k]}" for k in keys)
        lines.append(f"{name}{{{body}}}")
    lines.append("CHAIN{USE:P>E>C;MAG:D>S>R;ATT:S>C>W}")
    lines.append(f"EVO{{P:{evo['P']};M:{evo['M']}}}")
    return "\n".join(lines)
