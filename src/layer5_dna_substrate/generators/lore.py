import random

# ── Trait vocabularies (also the legal pin values per axis) ─────────────────

# What sort of claim this is. A doctrine is taught; a prophecy is awaited; a
# folk-belief is simply assumed. The kind sets the register of the whole entry.
_KIND = ["doctrine", "prophecy", "myth", "heresy", "folk-belief", "creation-story",
         "oath", "legend", "superstition", "cosmology", "law-of-the-dead",
         "catechism", "curse"]

# How it travels. Note this is the vehicle, not the belief: a scripture is a
# separate object from the doctrine it carries.
_MEDIUM = ["oral-telling", "written-scripture", "song", "stone-inscription",
           "ritual-performance", "relic-borne", "whispered-secret", "mural",
           "coded-text", "marked-on-the-body", "machine-voice", "children's-rhyme"]

_SUBJECT = ["the-world's-making", "the-collapse", "the-dead", "the-rising-magic",
            "a-founder", "a-place", "a-bloodline", "the-end-of-things",
            "a-forbidden-act", "a-buried-thing", "the-broken-sky", "the-machines",
            "a-vanished-people"]
_SHAPE = ["origin", "promise", "warning", "prohibition", "justification",
          "genealogy", "identification", "prediction", "explanation", "accusation"]
_STAKE = ["salvation", "a-birthright", "a-return", "protection-from-harm",
          "permission-to-rule", "absolution", "vengeance", "an-inheritance",
          "the-right-to-a-territory", "nothing-material"]

# What is actually underneath the claim. This is the truth axis's content: the
# veracity score says HOW true, this says true (or false) about what.
_KERNEL = ["a-real-event-misread", "a-real-person-mythologised",
           "a-machine-mistaken-for-divine", "a-garbled-instruction",
           "a-suppressed-crime", "a-natural-process-personified",
           "a-deliberate-fabrication", "an-accurate-record",
           "two-events-conflated", "a-warning-taken-as-a-promise"]
_PROOF = ["a-buried-relic", "a-decoded-text", "a-living-witness",
          "a-scar-on-the-land", "a-machine-record", "a-second-conflicting-copy",
          "a-sealed-archive", "none-remaining"]
# The keystone's companion. "unknowable" is what lets a claim stay open forever,
# which some canon questions require.
_RESOLVE = ["resolvable", "contested", "unknowable"]

_KEEPER = ["a-priesthood", "a-guild", "elders", "a-single-keeper", "a-whole-people",
           "a-secret-cell", "scholars", "a-ruling-house", "no-one-now"]
_RIVAL = ["a-rival-faith", "scholars", "heretics-within", "a-people-who-remember",
          "the-physical-evidence", "a-surviving-machine", "none-openly"]
_GRANTS = ["a-hierarchy's-power", "control-of-technology", "a-taboo", "a-tithe",
           "a-purge", "a-pilgrimage", "an-inheritance", "a-war", "restraint",
           "the-right-to-judge", "nothing"]

_OBSERVANCE = ["daily-recitation", "seasonal-rite", "pilgrimage", "fasting",
               "offering", "enforced-silence", "marking-the-body",
               "tending-a-machine", "burning-something", "a-vigil",
               "a-recited-genealogy", "abstaining-from-a-thing"]
_SANCTION = ["death", "exile", "mutilation", "shunning", "re-education",
             "branding", "loss-of-name", "quiet-disappearance", "ridicule", "none"]

_VARIANT = ["an-older-version", "a-heretical-reading", "a-folk-simplification",
            "a-forbidden-verse", "a-foreign-telling", "a-literalist-split",
            "a-version-told-to-children", "a-keeper's-private-doubt"]
_CORRUPTION = ["a-mistranslation", "a-lost-passage", "a-deliberate-edit",
               "two-things-conflated", "an-added-prophecy", "a-reversed-meaning",
               "a-copyist's-error", "a-name-struck-out"]

_TITLE_FORM = ["the-numbered-truth", "the-litany", "the-testament", "the-codex",
               "the-catechism", "the-N-somethings", "the-epithet-of-a-place",
               "the-named-verse", "the-question", "the-plain-saying"]

_TENSION = ["evidence-surfacing", "a-failed-prediction", "a-brewing-schism",
            "a-keeper's-doubt", "a-rival's-proof", "generational-lapse",
            "a-politically-inconvenient-passage", "a-successor-who-reads-it-differently"]

_PINS = {
    "veracity": ("score", None), "reach": ("score", None), "age": ("score", None),
    "zeal": ("score", None),
    "kind": ("pick", _KIND), "medium": ("pick", _MEDIUM),
    "subject": ("pick", _SUBJECT), "shape": ("pick", _SHAPE), "stake": ("pick", _STAKE),
    "kernel": ("pick", _KERNEL), "proof": ("pick", _PROOF), "resolve": ("pick", _RESOLVE),
    "keeper": ("pick", _KEEPER), "rival": ("pick", _RIVAL), "grants": ("pick", _GRANTS),
    "observance": ("pick", _OBSERVANCE), "sanction": ("pick", _SANCTION),
    "variant": ("pick", _VARIANT), "corruption": ("pick", _CORRUPTION),
    "title_form": ("pick", _TITLE_FORM), "tension": ("pick", _TENSION),
}


def generate_lore_dna(seed=None, **pins):
    """
    Generates a DNA string for LORE — a thing the world believes.

    Lore is not chronicle. A chronicle records what happened; lore records what
    is *claimed* to have happened, or what is held to be true. Decoding lore with
    the chronicle decoder (the previous workaround) forced beliefs into an event
    shape: the canon page for The First Truth of the Unbroken Thread carries a
    "Time Period", a "Historical Essence" and a "Turning Point" for what is
    actually a theological doctrine, and the prose visibly strains against them.

    The keystone is Veracity, and the crucial property is that it varies
    *independently of Reach*. A fabrication can be universally held; an accurate
    record can survive only as a despised heresy. Nothing in the genome ties how
    true a claim is to how many people believe it, which is where the drama lives.

    RESOLVE is Veracity's companion and exists for canon's sake: a claim marked
    "unknowable" can never be settled, so the decoder cannot quietly answer a
    question the author has chosen to leave open. Established canon overrides the
    DNA at decode time (see decoders/lore.md).

    Random by default; seedable and axis-pinnable like the creature and culture
    generators, for reproducing a KNOWN belief while letting the rest vary.
    """
    rng = random.Random(seed)

    for key, value in pins.items():
        if key not in _PINS:
            raise ValueError(f"Unknown lore pin '{key}'. Valid: {sorted(_PINS)}")
        kind_, options = _PINS[key]
        if kind_ == "score":
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

    veracity = score("veracity")
    reach = score("reach")
    age = score("age")

    claim = {"SUBJ": pick("subject", _SUBJECT), "SHAPE": pick("shape", _SHAPE),
             "STAKE": pick("stake", _STAKE)}
    truth = {"KERNEL": pick("kernel", _KERNEL), "PROOF": pick("proof", _PROOF),
             "RESOLVE": pick("resolve", _RESOLVE)}
    keep = {"KEEPER": pick("keeper", _KEEPER), "RIVAL": pick("rival", _RIVAL),
            "GRANTS": pick("grants", _GRANTS), "ZEAL": score("zeal")}
    practice = {"OBSERVE": pick("observance", _OBSERVANCE),
                "SANCTION": pick("sanction", _SANCTION)}
    drift = {"VARIANT": pick("variant", _VARIANT),
             "CORRUPT": pick("corruption", _CORRUPTION)}

    def block(name, d):
        return f"{name}{{{';'.join(f'{k}:{v}' for k, v in d.items())}}}"

    return (
        f"LORE{{v1.0[{veracity}/{reach}/{age}]}} "
        f"#{pick('kind', _KIND)} #{pick('medium', _MEDIUM)}\n"
        f"{block('CLAIM', claim)}\n"
        f"{block('TRUTH', truth)}\n"
        f"{block('KEEP', keep)}\n"
        f"{block('PRACTICE', practice)}\n"
        f"{block('DRIFT', drift)}\n"
        f"TITLE{{{pick('title_form', _TITLE_FORM)}}}\n"
        f"TENSION{{{pick('tension', _TENSION)}}}"
    )
