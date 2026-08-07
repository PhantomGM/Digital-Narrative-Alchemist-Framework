"""
The correspondence between what the forge can make and what a stub can name.

This bug has now been found three times: creatures becoming NPCs, then traps
becoming NPCs, then six more types at once. The mechanism is always the same.
`_resolve_stub_type` falls back to "npc" for any label it does not recognise,
so a type missing from VALID_STUB_TYPES or FUZZY_TYPE_MAP is not merely
unroutable — every stub naming it is silently registered as a person and filed
under Characters. Nothing raises, nothing warns, and the page looks fine.

The measured cost of the third instance: `agency`, `establishment`, `realm`,
`regional_poi`, `travel` and `wonder` each had a generator, a decoder and a
folder in TYPE_FOLDER_MAP, and the live world contained 112 records with not
one entity of any of those six types.

So the tests below are deliberately structural rather than a list of labels.
They derive their expectations from ProceduralForge.generators, which means a
twenty-second type added tomorrow fails them until it is wired up everywhere.
That is the point: this file is here to make the fourth instance impossible,
not to record the third.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402
from layer5_dna_substrate.expansion_manager import (  # noqa: E402
    FUZZY_TYPE_MAP, ExpansionManager, _resolve_stub_type)
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.obsidian_sync import ObsidianSync  # noqa: E402
from layer5_dna_substrate.phenotype_meta import (  # noqa: E402
    TAIL_INSTRUCTION, VALID_STUB_TYPES)
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

GENERATOR_TYPES = sorted(ProceduralForge().generators)


# --- the correspondence itself ----------------------------------------------

@pytest.mark.parametrize("etype", GENERATOR_TYPES)
def test_every_generated_type_can_be_named_by_a_stub(etype):
    assert etype in VALID_STUB_TYPES, (
        f"{etype!r} can be generated but not named: a '[{etype}]' stub will be "
        f"registered as an npc and filed under Characters")


@pytest.mark.parametrize("etype", GENERATOR_TYPES)
def test_every_generated_type_round_trips_through_resolution(etype):
    """The end-to-end property, not just set membership."""
    assert _resolve_stub_type(etype) == etype


@pytest.mark.parametrize("etype", GENERATOR_TYPES)
def test_every_generated_type_has_a_decoder(etype):
    assert etype in DNADecoder().prompts


@pytest.mark.parametrize("etype", GENERATOR_TYPES)
def test_every_generated_type_has_a_home(etype):
    folder = ObsidianSync.TYPE_FOLDER_MAP.get(etype)
    assert folder, f"{etype} is missing from TYPE_FOLDER_MAP"
    assert folder != ObsidianSync.DEFAULT_FOLDER, \
        f"{etype} falls into the Drafts holding pen rather than a folder"


def test_no_stub_type_is_ungeneratable():
    """The reverse direction: a type a stub can name but nothing can make."""
    orphans = VALID_STUB_TYPES - set(GENERATOR_TYPES)
    assert not orphans, f"stub types with no generator: {sorted(orphans)}"


# --- the prompt is derived, so it cannot drift ------------------------------

def test_the_prompt_offers_exactly_the_valid_types():
    """
    The list in TAIL_INSTRUCTION and the set in VALID_STUB_TYPES were kept in
    step by hand and drifted: the set reached fifteen while the prompt still
    offered ten. A decoder cannot use a type it was never told about, so the
    drift was upstream of every mis-routed stub.
    """
    for etype in VALID_STUB_TYPES:
        assert etype in TAIL_INSTRUCTION, \
            f"decoders are never told that {etype!r} is a legal stub type"


def test_the_prompt_type_list_is_stable_across_processes():
    """Set iteration order is not stable; an unstable prompt defeats caching."""
    line = next(ln for ln in TAIL_INSTRUCTION.splitlines()
                if ln.startswith("- Allowed stub types:"))
    listed = [t.strip() for t in
              line.split(":", 1)[1].strip().rstrip(".").split(",")]
    assert listed == sorted(VALID_STUB_TYPES)


# --- the labels a decoder actually writes -----------------------------------

@pytest.mark.parametrize("label,expected", [
    # The words that produced people. Each of these resolved to "npc" before.
    ("tavern", "establishment"), ("inn", "establishment"),
    ("shop", "establishment"), ("apothecary", "establishment"),
    ("smithy", "establishment"), ("market", "establishment"),
    ("shrine", "establishment"),
    ("dungeon", "regional_poi"), ("ruin", "regional_poi"),
    ("ruins", "regional_poi"), ("tower", "regional_poi"),
    ("lair", "regional_poi"), ("landmark", "regional_poi"),
    ("point of interest", "regional_poi"),
    ("city", "settlement"), ("town", "settlement"), ("village", "settlement"),
    ("outpost", "settlement"),
    ("kingdom", "realm"), ("empire", "realm"), ("dominion", "realm"),
    ("agency", "agency"), ("bureau", "agency"), ("ministry", "agency"),
    ("route", "travel"), ("journey", "travel"), ("voyage", "travel"),
    ("wonder", "wonder"),
    ("cult", "faction"), ("syndicate", "faction"),
])
def test_natural_labels_resolve(label, expected):
    assert _resolve_stub_type(label) == expected, \
        f"{label!r} still falls through to the npc default"


def test_realm_no_longer_resolves_to_location():
    """
    The one mis-route rather than an omission: realm has its own decoder, so
    routing it to location gave it the wrong prompt as well as the wrong shelf.
    """
    assert _resolve_stub_type("realm") == "realm"
    assert ObsidianSync.TYPE_FOLDER_MAP["realm"] == "Atlas/Realms"


# --- the collisions the new keys create -------------------------------------

@pytest.mark.parametrize("label,expected", [
    # Substring matching in insertion order is sharp in both directions. Each
    # of these is a word an earlier or later key contains.
    ("bishop", "npc"),          # contains "shop"
    ("priest", "npc"),
    ("culture", "culture"),     # contains "cult"
    ("subculture", "culture"),
    ("watchtower", "regional_poi"),
    ("workshop", "establishment"),
])
def test_substring_collisions_resolve_the_right_way(label, expected):
    assert _resolve_stub_type(label) == expected


def test_no_existing_label_was_hijacked():
    """
    New keys are appended rather than interleaved, which is what makes them
    safe: a key at the end can only capture labels that previously fell through
    to the npc default. This asserts that property for the labels most at risk.
    """
    for label, expected in [
            ("scripture", "lore"), ("scroll", "item"), ("book", "item"),
            # "logbook" contains "book", so it has always resolved to item and
            # the "logbook": "text" key beneath it never fired. That dead key is
            # now removed; this asserts the behaviour is unchanged.
            ("logbook", "item"),
            ("text", "text"), ("doctrine", "lore"),
            ("creature", "creature"), ("codex", "text"), ("temple", "location"),
            ("location", "location"), ("faction", "faction"),
            ("guild", "faction"), ("quest", "quest"), ("trap", "trap"),
            ("journal", "text"), ("chronicle", "chronicle")]:
        assert _resolve_stub_type(label) == expected, label


def test_fuzzy_keys_do_not_shadow_a_later_key_of_another_type():
    """
    A key that is a substring of a later key of a different type silently wins
    every label containing the later key. This walks the map in its real order
    and reports any such pair rather than waiting for a stub to find one.
    """
    keys = list(FUZZY_TYPE_MAP)
    collisions = [
        (early, late) for i, early in enumerate(keys)
        for late in keys[i + 1:]
        if early in late and FUZZY_TYPE_MAP[early] != FUZZY_TYPE_MAP[late]
    ]
    assert not collisions, (
        f"earlier key shadows a later key of a different type: {collisions}")


# --- end to end -------------------------------------------------------------

@pytest.mark.parametrize("label,expected", [
    ("Tavern", "establishment"),
    ("Dungeon", "regional_poi"),
    ("Kingdom", "realm"),
])
def test_a_stub_is_registered_as_the_type_it_names(label, expected):
    """The path a decoder's Unmade Connections line actually takes."""
    registry = DNARegistry()
    source = registry.register_element("npc", "NPC{}", "body", name="A Person")
    manager = ExpansionManager(registry, None, None, None)

    stub_id = manager._register_stub(
        source, label, f"The {label} of Testing", "Somewhere mentioned in passing.")

    assert registry.get_element(stub_id)["type"] == expected
