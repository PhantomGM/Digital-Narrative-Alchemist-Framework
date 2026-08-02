"""
Tests for the creature decoder's refinement pass.

This decoder was already the strongest of the set: a keystone axis (Sapience)
with explicit bands and the instruction to let it govern everything, a PWR gate
with its own anti-pattern warning, canon override, and contradictions read
through ecology. The pass found three narrower faults instead.

The generator emits special values that mean "no answer" -- and the decoder had
been written as if they never occur. Measured over 4000 rolls: SRC:unknown at
14.7%, RPR:does-not-reproduce at 12.4%, WKN:none-known at 8.0%. Only PWK:none
(8.6%) had been thought about. Two of the three actively contradicted the
surrounding instruction, so roughly a third of creatures hit a case where the
decoder told the model to do something the DNA forbade.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "creature.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_every_dna_block_the_generator_emits_is_documented(decoder):
    from layer5_dna_substrate.generators.creature import generate_creature_dna

    dna = generate_creature_dna(seed=7)
    for block in set(re.findall(r"([A-Z]+)\{", dna)):
        assert re.search(rf"`{block}" + r"\{", decoder) or block == "CREATURE", \
            f"block {block} is emitted but never documented"


def test_the_no_answer_values_are_all_addressed(decoder):
    """
    A value meaning "there is no answer" is exactly where a model will invent
    one, because the surrounding instruction asks for content.
    """
    for value in ("PWK is `none`", "WKN is `none-known`",
                  "SRC is `unknown`", "RPR is `does-not-reproduce`"):
        assert value in decoder, f"unhandled: {value}"


def test_a_creature_with_no_known_weakness_is_not_given_one(decoder):
    """The old text said ALWAYS give the GM something, which overwrote the DNA."""
    section = decoder.split("WKN is `none-known`")[1][:600]

    assert "do **not** invent one" in decoder.split("WKN —")[1][:400]
    assert "survive it" in section or "way to survive" in section


def test_an_unknown_origin_stays_unknown(decoder):
    """SRC:unknown is 14.7% of rolls and is a canon-safety case."""
    section = decoder.split("SRC is `unknown`")[1][:500]

    assert "must** not** supply one" in section or "not** supply one" in section
    assert "Leave it open" in section


def test_a_creature_that_cannot_breed_has_no_infestation(decoder):
    section = decoder.split("RPR is `does-not-reproduce`")[1][:600]

    assert "no infestation" in section
    assert "finite" in section
    assert "Do not write population growth" in section


def test_it_carries_the_canon_safety_rule(decoder):
    """Only 4 of 21 decoders had this; creature was not one of them."""
    assert "Never resolve a question the setting leaves open" in decoder
    assert "stays** unresolved" in decoder or "stays unresolved" in decoder


def test_the_keystone_still_governs(decoder):
    """Sapience is the axis that stops a beast being written as a villain."""
    section = decoder.split("SAP (Sapience")[1].split("**#origin")[0]

    assert "THE KEYSTONE" in decoder
    assert "NO Beliefs/Desires" in section
    assert "never as a human moral alignment" in section


def test_contradictions_keep_their_ecological_lens(decoder):
    assert "biology and ecology" in decoder
    assert "never through psychology or motive" in decoder


def test_the_no_scaffolding_rule_covers_paraphrases(decoder):
    """
    A live decode wrote "Because their reproduction score is zero" -- the field
    name laundered into prose. Rule 1 already forbade referencing the codes, but
    it sits 60 lines above the output template and says nothing about
    paraphrase, which is the form the leak actually takes.
    """
    tail = decoder.split("STRUCTURED OUTPUT FORMAT")[1]

    assert "No scaffolding below this line" in tail
    assert "reproduction score is zero" in tail, "name the observed failure"
    assert "same leak wearing prose" in tail
