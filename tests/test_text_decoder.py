"""
Tests for the text decoder's refinement pass.

Two faults, both from fields rolled independently of each other.

The absences were undocumented as in creature, culture and lore:
GAP:no-one-can-read-it 12.5%, HOLDER:no-one-knows 11.6%, FUNC:never-opened 10.6%.

More interesting, the blocks contradict each other roughly one text in five:

    FUNC:never-opened beside a RITE                  9.1%
    high LEG beside GAP:no-one-can-read-it           4.4%
    FUNC:never-opened with high LEG                  3.4%
    COND:actively-crumbling with DECAY:stable-for-now 1.3%

Some of those pairings are logically impossible as written -- a daily reading
of a text nobody opens -- and the cheap fix is to drop whichever field is
inconvenient, which silently discards half the genome. Each now has a reading
that uses both.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "text.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_every_block_the_generator_emits_is_documented(decoder):
    from layer5_dna_substrate.generators.text import generate_text_dna

    for block in set(re.findall(r"([A-Z]+)\{", generate_text_dna(seed=13))):
        assert re.search(rf"`{block}" + r"\{", decoder) or block == "TEXT", \
            f"{block} emitted but never documented"


def test_all_four_attrib_states_are_defined(decoder):
    """ATTRIB is what stops a page settling who wrote something."""
    for state in ("known", "disputed", "falsely-attributed", "unknown"):
        assert state in decoder
    assert "Rule 8 applies" in decoder


@pytest.mark.parametrize("tension", [
    "`FUNC:never-opened` beside a RITE",
    "High LEG beside `GAP:no-one-can-read-it`",
    "`FUNC:never-opened` with high LEG",
    "`COND:actively-crumbling` with `DECAY:stable-for-now`",
])
def test_each_cross_field_tension_has_a_reading(decoder, tension):
    section = decoder.split("FIELDS THAT ARGUE WITH EACH OTHER")[1]
    section = section.split("ABSENCES")[0]

    assert tension in section, f"no reading for: {tension}"


def test_neither_side_of_a_tension_may_be_dropped(decoder):
    section = decoder.split("FIELDS THAT ARGUE WITH EACH OTHER")[1]

    assert "never quietly drop the field that is inconvenient" in section
    assert "better than either half alone" in section


def test_the_impossible_rites_are_named_individually(decoder):
    """
    Half the RITE pool works fine on a sealed text and half cannot. Saying only
    "reconcile them" leaves the model to guess which case it has.
    """
    section = decoder.split("FIELDS THAT ARGUE WITH EACH OTHER")[1]

    for workable in ("a-pilgrimage-to-see-it", "a-recitation-from-memory",
                     "burning-a-copy-yearly"):
        assert workable in section
    for impossible in ("a-daily-reading", "an-annual-unsealing",
                       "a-question-put-to-it"):
        assert impossible in section


@pytest.mark.parametrize("value", ["HOLDER:no-one-knows", "FUNC:never-opened",
                                   "GAP:no-one-can-read-it"])
def test_each_absence_is_addressed(decoder, value):
    section = decoder.split("ABSENCES")[1].split("CONTRADICTIONS")[0]

    assert f"`{value}`" in section, f"unhandled absence: {value}"


def test_an_unheld_text_is_unaccounted_for_not_lost(decoder):
    section = decoder.split("`HOLDER:no-one-knows`")[1][:400]

    assert "not lost" in section
    assert "someone has it" in section


def test_legibility_is_distinguished_from_comprehensibility(decoder):
    """The keystone measures the marks, not whether anyone has the language."""
    section = decoder.split("High LEG beside")[1][:500]

    assert "legible is not the same as comprehensible" in section.lower()


def test_contradictions_keep_their_object_history_lens(decoder):
    assert "the history of the object" in decoder
