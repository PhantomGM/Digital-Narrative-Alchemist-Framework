"""
Every generatable type either has a ghost shape or is excluded on purpose.

Derived from ProceduralForge.generators rather than listing types, for the same
reason test_stub_type_coverage.py is: a twenty-second type must fail the suite
until somebody decides what a placeholder for it looks like, rather than
silently falling through to DEFER and leaving a frontier emptier than it needs
to be.

The shapes themselves also have to keep their promise. A ghost may state what a
TYPE guarantees and repeat what the world has already said; it may not answer
anything about the specific entity. These tests assert that structurally --
every shape must offer both halves, and the rendered page must say outright that
it invented nothing.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.ghost_registry import (  # noqa: E402
    NO_GHOST_BY_DESIGN, SHAPES, GhostRegistry)

TYPES = sorted(ProceduralForge().generators)


# --- coverage ---------------------------------------------------------------

@pytest.mark.parametrize("etype", TYPES)
def test_every_type_is_either_shaped_or_excluded(etype):
    assert etype in SHAPES or etype in NO_GHOST_BY_DESIGN, (
        f"{etype} has no ghost shape and is not in NO_GHOST_BY_DESIGN, so a "
        f"stub of that type silently defers where it could have been useful")


def test_the_exclusions_are_exactly_what_they_claim():
    """A stale exclusion list hides the gap it was written to record."""
    unshaped = {t for t in TYPES if t not in SHAPES}
    assert unshaped == NO_GHOST_BY_DESIGN, (
        f"NO_GHOST_BY_DESIGN is stale: unshaped types are {sorted(unshaped)}, "
        f"the set says {sorted(NO_GHOST_BY_DESIGN)}")


def test_no_shape_exists_for_a_type_nothing_can_generate():
    assert not set(SHAPES) - set(TYPES)


@pytest.mark.parametrize("etype", sorted(NO_GHOST_BY_DESIGN))
def test_excluded_types_really_cannot_be_ghosted(etype):
    assert not GhostRegistry().can_ghost(etype)


# --- the shapes keep their promise ------------------------------------------

@pytest.mark.parametrize("etype", sorted(SHAPES))
def test_a_shape_offers_both_halves(etype):
    """
    Guarantees without open questions is a shape pretending to know things.
    Open questions without guarantees is a stub with extra words.
    """
    shape = SHAPES[etype]
    assert shape.what_it_is.strip()
    assert len(shape.guaranteed) >= 2, etype
    assert len(shape.open_questions) >= 2, etype


@pytest.mark.parametrize("etype", sorted(SHAPES))
def test_a_ghost_page_declares_itself(etype):
    stub = {"type": etype, "name": "Placeholder", "gist": "mentioned once"}
    body = GhostRegistry().ghost(stub)
    assert "not authored, not canon" in body
    assert "Open — nothing below has been decided" in body
    assert "Placeholder" in body


@pytest.mark.parametrize("etype", sorted(SHAPES))
def test_a_ghost_page_never_names_a_specific(etype):
    """
    A shape must not smuggle in a proper noun. Anything capitalised mid-sentence
    that is not the entity's own name would be an invention the world never
    agreed to.
    """
    shape = SHAPES[etype]
    text = " ".join([shape.what_it_is] + shape.guaranteed + shape.open_questions)
    for sentence in text.split(". "):
        words = sentence.split()
        for word in words[1:]:
            assert not (word[:1].isupper() and word.lower() not in
                        ("i", "a")), f"{etype} shape names something: {word!r}"


def test_the_new_shapes_are_about_their_type_not_a_world():
    """Spot-check the three added last: realm, region and wonder."""
    reg = GhostRegistry()
    for etype, expected in [("realm", "border"), ("region", "terrain"),
                            ("wonder", "measure")]:
        body = reg.ghost({"type": etype, "name": "X", "gist": ""})
        assert expected in body.lower(), etype
