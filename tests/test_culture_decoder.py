"""
Tests for the culture decoder's refinement pass.

Same failure mode the creature decoder had, and larger. Six fields can return a
value meaning "there is nothing here", every one of them sat under an
instruction demanding exactly the content that value denies, and **55% of
cultures roll at least one**:

    PAST:forgotten     15.9%   under "how they regard the Golden Age"
    FEUD:none          13.8%   under "a traditional source of friction"
    UNI:none           12.5%   under "union/pairing custom"
    POWER:none         12.4%   under "how authority is held"
    AGE:none           11.5%   under "make this concrete and memorable"
    CRAFT:none-notable  9.4%   under "what they are known for making"

Inventing a coming-of-age rite for a people who have none was the compliant
reading of the prompt.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "culture.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_every_block_the_generator_emits_is_documented(decoder):
    from layer5_dna_substrate.generators.culture import generate_culture_dna

    dna = generate_culture_dna(seed=5)
    for block in set(re.findall(r"([A-Z]+)\{", dna)):
        assert re.search(rf"`{block}" + r"\{", decoder) or block == "CULTURE", \
            f"{block} is emitted but never documented"


@pytest.mark.parametrize("value", ["AGE:none", "UNI:none", "POWER:none",
                                   "FEUD:none", "CRAFT:none-notable",
                                   "PAST:forgotten"])
def test_each_absence_is_addressed(decoder, value):
    section = decoder.split("ABSENCES")[1].split("CONTRADICTIONS")[0]

    assert f"`{value}`" in section, f"unhandled absence: {value}"


def test_absences_are_framed_as_design_not_gaps(decoder):
    section = decoder.split("ABSENCES")[1].split("CONTRADICTIONS")[0]

    assert "Never invent the thing the DNA says they do not have" in section
    assert "not a gap for you to fill" in section


def test_the_absence_guidance_gives_something_to_write_instead(decoder):
    """
    Telling a model only what not to do leaves it with a hole. Each absence
    names the question that replaces the missing content.
    """
    section = decoder.split("ABSENCES")[1].split("CONTRADICTIONS")[0]

    assert "something must" in section          # UNI
    assert "describe *how*" in section          # POWER
    assert "someone else's account" in section  # PAST


def test_it_carries_the_canon_safety_rule(decoder):
    assert "Never resolve a question the setting leaves open" in decoder
    assert "stays** unresolved" in decoder or "stays unresolved" in decoder


def test_culture_naming_defers_to_the_world_language(decoder):
    """
    The context assembler now injects the world's naming conventions, so a
    culture's own NAME{} convention is a second authority on the same question.
    """
    section = decoder.split("**7. `NAME{}`")[1].split("**8.")[0]

    assert "variation inside" in section
    assert "not a replacement" in section
    assert "already belonging to someone" in section


def test_no_scaffolding_rule_sits_with_the_output_template(decoder):
    tail = decoder.split("STRUCTURED OUTPUT FORMAT")[1]

    assert "No scaffolding below this line" in tail
    assert "The axis names themselves are scaffolding" in tail
    # Name the exact sentence that got through, so the rule cannot be softened
    # back into an abstraction that a model reads past.
    assert "cohesion is** naturally loose" in tail
    assert "still make sense with a number after it" in tail


def test_the_keystone_still_governs(decoder):
    """Cohesion is what stops a people being written as a monolith."""
    section = decoder.split("COH (Cohesion")[1].split("**OPN")[0]

    assert "fractured and various" in section
    assert "tightly uniform" in section


def test_contradictions_keep_their_historical_lens(decoder):
    assert "history and circumstance" in decoder
    assert "never by flattening the people into a single motive" in decoder
