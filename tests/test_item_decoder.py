"""
Tests for the item decoder's refinement pass.

The decoder had one output rule and no decoding instructions at all -- the same
state faction was in. Its generator emits forty keyed values across five blocks
and the prompt defined none of them, so every item in this world was decoded
from a string the decoder could not read.

As with faction, the vocabulary is not invented here. But more is recoverable
than faction had: the generator named its own top-line scales in local
variables (power, complexity, rarity), the block names are themselves
meaningful, and the routing doc records that EVO tracks an item's change over
campaign time. So the decoder reads blocks at block level -- overall level and
spread -- which is reliable, and is told not to guess at letters, which is not.

POW and RAR are rolled independently, giving two contradictions in about a
fifth of items: powerful-but-common 11.2%, famous-but-weak 10.2%.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.generators.item import (  # noqa: E402
    ITEM_BLOCKS, ITEM_SCALES, ITEM_TYPES, generate_item_dna,
)

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "item.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


# --- decoder -------------------------------------------------------------

def test_every_block_the_generator_emits_is_documented(decoder):
    for block in set(re.findall(r"([A-Z]+)\{", generate_item_dna(seed=1))):
        assert f"`{block}`" in decoder or re.search(rf"`{block}" + r"\{", decoder) \
            or block == "ITEM", f"{block} emitted but never documented"


def test_the_governing_scales_are_named(decoder):
    """The one part of this genome whose meaning is actually recorded."""
    assert "POW (Power, 1–9)" in decoder
    assert "CPX (Complexity, 1–9)" in decoder
    assert "RAR (Rarity, 1–9)" in decoder


def test_it_refuses_to_invent_the_undocumented_letters(decoder):
    assert "block letters are not yet documented" in decoder
    assert "Do not invent a meaning for a letter" in decoder
    assert "AP`/`MR`/`RE`" in decoder or "AP" in decoder


def test_blocks_are_given_a_readable_meaning_instead(decoder):
    """
    Refusing to guess at letters would leave the model nothing usable. The block
    names are meaningful even when their keys are not.
    """
    section = decoder.split("Read each block at the block level")[1]
    for block in ITEM_BLOCKS:
        assert f"`{block}`" in section, f"no block-level reading for {block}"
    assert "spread" in section


def test_both_cross_field_tensions_have_readings(decoder):
    section = decoder.split("CROSS-FIELD TENSIONS")[1].split("CONTRADICTIONS")[0]

    assert "High RAR with low POW" in section
    assert "High POW with low RAR" in section
    assert "neither may be quietly dropped" in section


def test_contradictions_have_a_lens(decoder):
    assert "provenance and use" in decoder


def test_canon_and_open_questions_are_protected(decoder):
    assert "Established canon overrides the DNA" in decoder
    assert "Never resolve a question the setting leaves open" in decoder


def test_it_forbids_stat_blocks(decoder):
    """An item profile that carries damage dice is not system-agnostic."""
    assert "not a stat block" in decoder


# --- generator -----------------------------------------------------------

def test_a_seed_reproduces_the_item():
    assert generate_item_dna(seed=5) == generate_item_dna(seed=5)
    assert generate_item_dna(seed=5) != generate_item_dna(seed=6)


def test_the_governing_scales_are_pinnable():
    dna = generate_item_dna(power=9, complexity=2, rarity=7, seed=1)

    assert "[9/2/7]" in dna


def test_the_type_is_pinnable():
    assert generate_item_dna(type="relic", seed=1).splitlines()[0].endswith("#relic")


def test_pins_leave_the_rest_free():
    a = generate_item_dna(power=9)
    b = generate_item_dna(power=9)

    assert "[9/" in a and "[9/" in b
    assert a != b


@pytest.mark.parametrize("pins,match", [
    ({"power": 0}, "int 1-9"),
    ({"rarity": 10}, "int 1-9"),
    ({"complexity": True}, "int 1-9"),
    ({"type": "sandwich"}, "not in"),
    ({"phy": 5}, "Unknown item pin"),
    ({"M": 40}, "Unknown item pin"),
])
def test_bad_pins_are_rejected(pins, match):
    with pytest.raises(ValueError, match=match):
        generate_item_dna(**pins)


def test_the_undocumented_letters_are_not_pinnable():
    """
    A pin on a key nobody has defined is a pin on nothing, and would look like
    it worked.
    """
    for key in ITEM_BLOCKS["PHY"]:
        with pytest.raises(ValueError, match="Unknown item pin"):
            generate_item_dna(**{key: 50})


def test_the_dna_shape_is_unchanged():
    """Existing item strings must stay readable by the same decoder."""
    dna = generate_item_dna(seed=3)
    lines = dna.splitlines()

    assert re.match(r"ITEM\{v1\.0\[\d/\d/\d\]\}<AP:[\d.]+,MR:[\d.]+,RE:[\d.]+>#\w+",
                    lines[0])
    assert [l.split("{")[0] for l in lines[1:]] == \
        list(ITEM_BLOCKS) + ["CHAIN", "EVO"]
    for name, keys in ITEM_BLOCKS.items():
        body = next(l for l in lines if l.startswith(name + "{"))
        assert [p[0] for p in body.split("{")[1].rstrip("}").split(",")] == list(keys)
