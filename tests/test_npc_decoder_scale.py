"""
Tests that the NPC decoder documents the alignment scale as a gradient.

The decoder used to give only the three band boundaries — 9-7 Lawful, 6-4
Neutral, 3-1 Chaotic. Within a band, L7 and L9 were indistinguishable to it,
and nothing said N6 leans Lawful while N4 leans Chaotic. Eight of the nine
values on each axis carried information the decoder discarded.

That was nearly harmless while the generator averaged its trait scores, because
98% of NPCs came out 4, 5 or 6 and there was no within-band variation to lose.
Now that every one of the 81 points is reachable, the gradient is most of the
signal, so it has to survive in the file the model actually reads.

These assert the documentation, not behaviour — the same shape as
test_readme_claims. A decoder is a prompt; its text IS its implementation.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "npc.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_every_score_from_1_to_9_is_given_a_reading(decoder):
    """A band boundary is not a reading. All nine values need one."""
    table = decoder.split("magnitude, not just a label")[1].split("**3.")[0]
    for score in range(1, 10):
        assert re.search(rf"\*\*{score}\*\*", table), \
            f"score {score} has no row in the alignment gradient"


def test_the_poles_are_named_as_the_extremes(decoder):
    assert re.search(r"1 and 9 are the extremes", decoder)
    assert "intensity falls as the score moves toward 5" in decoder


def test_five_is_identified_as_the_true_centre(decoder):
    assert "True Neutral" in decoder
    assert re.search(r"\*\*5\*\*.*(?:centre|center)", decoder)


def test_six_and_four_lean_without_crossing(decoder):
    """The distinction the old three-band text could not express."""
    assert re.search(r"\*\*6\*\*.*leaning Lawful.*leaning Good", decoder)
    assert re.search(r"\*\*4\*\*.*leaning Chaotic.*leaning Evil", decoder)
    assert "A 6 is **not** Good and a 4 is **not** Evil" in decoder


def test_the_headline_is_not_described_as_an_average(decoder):
    """It was drawn from an average until the distribution fix; it is not now."""
    head = decoder.split("**2. PAIRED TRAITS")[0]

    assert "ALIGNMENT AVERAGES" not in head
    assert "not averaged" in head


def test_unpaired_traits_run_to_the_opposite_not_to_absence(decoder):
    """'weak/opposite' conflated a missing virtue with an active vice."""
    section = decoder.split("**3. UNPAIRED TRAITS")[1].split("**4.")[0]

    assert "its opposite" in section
    assert "not from \"strong\" to \"absent\"" in section
    assert "active vice, not a missing virtue" in section


def test_trait_score_and_intensity_are_distinguished(decoder):
    """Both are numbers on the same token; conflating them is the easy error."""
    section = decoder.split("**2. PAIRED TRAITS")[1].split("**3.")[0]

    assert "how loud" in section and "what shape" in section


def test_the_band_boundaries_still_agree_with_the_generator(decoder):
    """The generator's bands and the decoder's bands must not drift apart."""
    from layer5_dna_substrate.generators.npc import GNE_BANDS, LNC_BANDS

    assert LNC_BANDS == {"L": (7, 8, 9), "N": (4, 5, 6), "C": (1, 2, 3)}
    assert GNE_BANDS == {"G": (7, 8, 9), "N": (4, 5, 6), "E": (1, 2, 3)}
    assert "9–7 = Lawful, 6–4 = Neutral, 3–1 = Chaotic" in decoder
    assert "9–7 = Good, 6–4 = Neutral, 3–1 = Evil" in decoder
