import random

# ── Trait vocabularies (also the legal pin values per axis) ─────────────────

# The physical thing. A text is an object before it is a message: it can be
# burned, stolen, dropped down a shaft, or rendered unreadable by damp.
_FORM = ["vellum-codex", "bound-paper", "scroll", "stone-tablet", "clay-tablet",
         "data-slate", "punch-card-deck", "etched-metal-plate", "woven-cloth",
         "wax-cylinder", "tattooed-skin", "carved-pillar", "memorised-only"]

# What kind of document it is, which is not the same as what it is taken for.
_GENRE = ["scripture", "technical-manual", "ledger", "letter", "law-code", "map",
          "poem", "census", "contract", "diary", "treatise", "hymnal",
          "warning-notice", "inventory", "medical-record", "operating-log"]

# What people take it for, and what it actually is. The pairing is the point.
_PURPORT = ["holy-writ", "a-history", "a-prophecy", "a-royal-charter",
            "a-founder's-testament", "a-map-to-something", "a-list-of-the-dead",
            "a-cure", "a-law", "a-love-letter", "a-confession", "nothing-special"]
_ACTUAL = ["machine-operating-instructions", "a-maintenance-schedule",
           "an-inventory", "a-forgery", "a-transcription-error-repeated",
           "exactly-what-it-claims", "a-fragment-of-something-larger",
           "a-cover-for-something-else", "a-child's-copybook",
           "a-warning-nobody-heeded", "a-legal-record", "an-evacuation-notice"]
# How the mismatch survives. Usually because nobody can actually read it.
_GAP = ["no-one-can-read-it", "the-readers-lie", "it-is-never-opened",
        "the-translation-is-old-and-trusted", "only-excerpts-circulate",
        "the-original-is-sealed", "the-question-is-forbidden",
        "everyone-assumes-someone-checked"]

_AUTHOR = ["a-named-founder", "a-committee", "an-anonymous-clerk", "a-machine",
           "a-later-forger", "a-captive", "many-hands-over-centuries",
           "a-child", "a-condemned-prisoner", "a-functionary-doing-their-job"]
# The canon-safety hook, mirroring lore's RESOLVE.
_ATTRIB = ["known", "disputed", "falsely-attributed", "unknown"]

_HOLDER = ["a-priesthood", "a-guild", "a-single-keeper", "a-ruling-house",
           "an-archive", "a-scavenger-who-cannot-read", "a-secret-cell",
           "no-one-knows", "a-machine-that-still-guards-it"]
_PLACE = ["a-sealed-vault", "an-altar", "a-working-archive", "a-ruin",
          "carried-on-a-person", "walled-into-a-building", "many-places-at-once",
          "a-place-no-one-will-name", "beneath-water"]
_ACCESS = ["anyone", "the-literate", "initiates-only", "the-highest-rank-only",
           "by-payment", "forbidden-to-all", "only-the-blind-may-hear-it-read",
           "one-person-at-a-time"]

_CONDITION = ["pristine", "worn-but-sound", "water-damaged", "burned-at-the-edges",
              "actively-crumbling", "overwritten", "deliberately-defaced",
              "repaired-badly", "sealed-and-unexamined"]
_SCRIPT = ["the-common-tongue", "a-dead-language", "a-technical-notation",
           "a-cipher", "pictograms", "machine-code", "a-sacred-alphabet",
           "two-scripts-interleaved", "a-shorthand-no-one-uses"]
_DECAY = ["ink-fading", "medium-rotting", "power-source-failing",
          "each-copy-drifts-further", "the-last-reader-is-dying",
          "pages-removed-one-by-one", "stable-for-now", "corrupted-by-magic"]

_FUNCTION = ["recited-aloud", "consulted-for-rulings", "sworn-upon",
             "never-opened", "copied-as-devotion", "carried-as-a-charm",
             "used-to-settle-disputes", "taught-to-children",
             "followed-as-instructions", "hidden-and-denied"]
_RITUAL = ["a-daily-reading", "an-annual-unsealing", "a-pilgrimage-to-see-it",
           "a-recitation-from-memory", "washing-before-touching",
           "a-question-put-to-it", "burning-a-copy-yearly", "none"]

_HAZARD = ["it-is-illegal-to-read", "the-cipher-drives-readers-to-obsession",
           "it-names-people-still-living", "reading-it-triggers-a-machine",
           "it-is-physically-fragile", "possession-marks-you-as-heretic",
           "its-instructions-are-dangerous-if-followed", "none"]
_SANCTION = ["death", "exile", "blinding", "loss-of-name", "confiscation",
             "re-education", "quiet-disappearance", "a-fine", "none"]

_TENSION = ["a-second-copy-has-surfaced", "someone-can-read-it-now",
            "decay-is-reaching-a-key-passage", "a-holder-wants-to-sell-it",
            "a-translation-is-being-disputed", "it-has-been-stolen",
            "a-passage-has-begun-to-be-questioned", "the-machine-it-instructs-has-woken"]

_PINS = {
    "legibility": ("score", None), "copies": ("score", None),
    "completeness": ("score", None), "age": ("score", None),
    "form": ("pick", _FORM), "genre": ("pick", _GENRE),
    "purport": ("pick", _PURPORT), "actual": ("pick", _ACTUAL), "gap": ("pick", _GAP),
    "author": ("pick", _AUTHOR), "attrib": ("pick", _ATTRIB),
    "holder": ("pick", _HOLDER), "place": ("pick", _PLACE), "access": ("pick", _ACCESS),
    "condition": ("pick", _CONDITION), "script": ("pick", _SCRIPT),
    "decay": ("pick", _DECAY),
    "function": ("pick", _FUNCTION), "ritual": ("pick", _RITUAL),
    "hazard": ("pick", _HAZARD), "sanction": ("pick", _SANCTION),
    "tension": ("pick", _TENSION),
}


def generate_text_dna(seed=None, **pins):
    """
    Generates a DNA string for a TEXT — an in-world document as an object.

    A text is not lore. Lore is a claim; a text is the physical thing that
    carries one, and it has properties a belief does not: a form that can burn,
    a script that may be unreadable, a number of surviving copies, a custodian,
    and a condition that worsens. Decoding a document with the lore decoder
    produces a page about what it teaches and says nothing about what it is —
    yet whether a scripture exists as one sealed original or ten thousand
    recited copies decides every story you can tell with it.

    The keystone is Legibility, and its force comes from being paired with
    PURPORT vs ACTUAL. A document can be universally revered and completely
    unread: the Litany of the Unbroken Thread is held as divine scripture and is
    in fact machine operating instructions, a gap that survives precisely
    because almost no one can read it. GAP records how such a mismatch is
    maintained, so the contradiction is explained rather than merely asserted.

    ATTRIB is the canon-safety hook, mirroring lore's RESOLVE: authorship marked
    "unknown" or "disputed" must stay that way, so a generated page cannot
    quietly reveal who wrote a text the author has left unattributed.

    Random by default; seedable and axis-pinnable like the lore, creature and
    culture generators. Established canon overrides the DNA at decode time
    (see decoders/text.md).
    """
    rng = random.Random(seed)

    for key, value in pins.items():
        if key not in _PINS:
            raise ValueError(f"Unknown text pin '{key}'. Valid: {sorted(_PINS)}")
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

    def score(key):
        return pins[key] if key in pins else rng.randint(1, 9)

    legibility = score("legibility")
    copies = score("copies")
    completeness = score("completeness")

    purport = {"BELIEVED": pick("purport", _PURPORT), "ACTUAL": pick("actual", _ACTUAL),
               "GAP": pick("gap", _GAP)}
    origin = {"AUTHOR": pick("author", _AUTHOR), "ATTRIB": pick("attrib", _ATTRIB),
              "AGE": score("age")}
    custody = {"HOLDER": pick("holder", _HOLDER), "PLACE": pick("place", _PLACE),
               "ACCESS": pick("access", _ACCESS)}
    state = {"COND": pick("condition", _CONDITION), "SCRIPT": pick("script", _SCRIPT),
             "DECAY": pick("decay", _DECAY)}
    use = {"FUNC": pick("function", _FUNCTION), "RITE": pick("ritual", _RITUAL)}
    peril = {"HAZARD": pick("hazard", _HAZARD), "SANCTION": pick("sanction", _SANCTION)}

    def block(name, d):
        return f"{name}{{{';'.join(f'{k}:{v}' for k, v in d.items())}}}"

    return (
        f"TEXT{{v1.0[{legibility}/{copies}/{completeness}]}} "
        f"#{pick('form', _FORM)} #{pick('genre', _GENRE)}\n"
        f"{block('PURPORT', purport)}\n"
        f"{block('ORIGIN', origin)}\n"
        f"{block('CUSTODY', custody)}\n"
        f"{block('STATE', state)}\n"
        f"{block('USE', use)}\n"
        f"{block('PERIL', peril)}\n"
        f"TENSION{{{pick('tension', _TENSION)}}}"
    )
