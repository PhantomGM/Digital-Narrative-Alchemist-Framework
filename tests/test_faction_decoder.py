"""
Tests for the faction decoder's refinement pass.

The faction decoder had no decoding instructions at all. Not thin ones — none.
Its generator emits fourteen hyphen-separated axes and the prompt defined zero
of them, so every faction in the world was decoded from a string the decoder
could not read. No specification exists anywhere in the repo either; the
routing doc names the fourteen tags and points at a prompt_decode_faction.txt
that was never brought over.

Rather than invent a vocabulary — which would contradict whatever the author
eventually defines, and would be indistinguishable from it in the output — the
decoder now states the shape, says the vocabulary is undefined, and constrains
the model to relational use only.

The rest matches the NPC pass: contradictions framed as the payload with a lens
of their own, the default answer named and demoted, a trajectory, and the
canon-safety rule that only four of twenty-one decoders carried.
"""

import os
import re

import pytest

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "faction.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_the_dna_shape_matches_the_generator(decoder):
    """The npc pass found two keys that had drifted from their generator."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from layer5_dna_substrate.generators.faction import FACTION_AXES

    order = re.search(r"`([A-Z· ]+)`", decoder.split("DNA shape")[1]).group(1)
    listed = [a.strip() for a in order.split("·")]

    assert listed == list(FACTION_AXES), f"decoder lists {listed}"
    for axis, options in FACTION_AXES.items():
        assert options[0] in decoder or options[0].lstrip(axis) in decoder, \
            f"axis {axis} range not documented"


def test_it_admits_the_vocabulary_is_undefined(decoder):
    """
    A confident guess is worse than none: it will contradict the next faction
    generated from a neighbouring value, and nothing would catch that.
    """
    section = decoder.split("DECODING INSTRUCTIONS")[1].split("STRUCTURED OUTPUT")[0]

    assert "not yet defined" in section
    assert "Do not invent a meaning for an axis" in section
    assert "fingerprint, not a sentence" in section


def test_canon_outranks_the_dna(decoder):
    assert "Established canon overrides the DNA" in decoder


def test_it_carries_the_canon_safety_rule(decoder):
    """Only 4 of 21 decoders had this; it is what protects an open question."""
    assert "Never resolve a question the setting leaves open" in decoder
    assert "stays** unresolved" in decoder or "stays unresolved" in decoder


def test_contradictions_are_framed_as_the_payload(decoder):
    """The decoder previously said nothing about them at all."""
    section = decoder.split("**Internal Contradictions:**")[1]

    assert "These are not errors" in section
    assert "institutional history and competing interest" in section
    assert "Never resolve a contradiction by softening one side" in section


def test_the_secret_has_a_palette_and_the_default_is_demoted(decoder):
    """
    An outside review of the world found every faction page ran the same
    formula: "the faction's darkest secret is a forbidden ritual or pact".
    """
    section = decoder.split("Secrets & Shadows")[1].split("**Internal Contradictions")[0]

    for shape in ("founding compromise", "Tiered knowledge", "inverted secret",
                  "banal ruin", "already losing", "enemy is right"):
        assert shape in section, f"missing secret shape: {shape}"
    assert "do not default to one" in section
    # Compare list positions, not first mentions: the reflex answer is named up
    # front as the thing to avoid, which is a different appearance from its
    # entry in the palette.
    assert section.index("**A founding compromise**") < \
        section.index("**A forbidden ritual or corrupt deal**"), \
        "the reflex answer must be last in the palette, not first"


def test_the_secret_must_cost_something(decoder):
    section = decoder.split("Secrets & Shadows")[1].split("**Internal Contradictions")[0]

    assert "not a secret, it is a detail" in section


def test_a_trajectory_is_required(decoder):
    """Evolution over time: present in 10 of 21 decoders, absent from this one."""
    section = decoder.split("**Trajectory:**")[1].split("**Adventure Hooks")[0]

    for beat in ("Pressure", "If they win", "If they break", "The tell"):
        assert beat in section
    assert "scenery" in section


def test_no_scaffolding_rule_sits_with_the_output_template(decoder):
    tail = decoder.split("STRUCTURED OUTPUT FORMAT")[1]

    assert "No scaffolding below this line" in tail


def test_palette_labels_are_marked_internal(decoder):
    """
    A live run printed them straight onto the page -- "**A banal ruin:** the
    Guild's reputation relies on no ancient prophecy..." -- in all three
    decodes. A decision aid rendered as an output header is the same class of
    leak as printing the DNA: it shows the reader the machinery.
    """
    secrets = decoder.split("Secrets & Shadows")[1].split("**Internal Contradictions")[0]
    contradictions = decoder.split("**Internal Contradictions:**")[1].split("**Resources")[0]

    assert "Choose the shape silently" in secrets
    assert "Never print one on the page" in secrets
    assert "A banal ruin:" in secrets, "name the observed failure so it is unambiguous"
    assert "for choosing, never for printing" in contradictions
