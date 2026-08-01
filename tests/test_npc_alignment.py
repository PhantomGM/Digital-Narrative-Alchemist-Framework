"""
Tests for the NPC and faction genomes, and for the alignment distribution.

The headline LNC/GNE scores used to be the rounded mean of the 39 trait scores.
Each trait was a fair 1-9, but averaging twenty of them has a standard error
near 0.58, so the mean landed on 5 about 59% of the time. The measured effect
on 20,000 rolls: 35% of NPCs were exactly (5/5), 98% sat inside the 3x3 Neutral
core, 25 of the 81 points ever appeared, and a 1 or a 9 never did. The 81-point
system was functionally a 5-point one.

The distribution test below is the regression guard. It is the only test here
that would have caught the bug, because nothing about the old code looked wrong
— it was arithmetically correct and statistically fatal.
"""

import collections
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.generators.faction import (  # noqa: E402
    FACTION_AXES, generate_faction_dna,
)
from layer5_dna_substrate.generators.npc import (  # noqa: E402
    GNE_BANDS, LNC_BANDS, generate_npc_dna,
)

HEADLINE = re.compile(r"^\((\d)/(\d)\)")


def headline(dna):
    match = HEADLINE.match(dna)
    assert match, f"no headline in {dna[:40]!r}"
    return int(match.group(1)), int(match.group(2))


def band(score, bands):
    return next(k for k, v in bands.items() if score in v)


# --- the regression guard -------------------------------------------------

@pytest.fixture(scope="module")
def rolls():
    return [headline(generate_npc_dna()) for _ in range(4000)]


def test_all_nine_alignments_are_roughly_equally_likely(rolls):
    """
    The bug this file exists for. Averaging put 35% on True Neutral; a fair
    draw puts 1/9 (11.1%) on each of the nine. Tolerance is wide enough that
    4,000 samples will not flake, and far tighter than the old behaviour.
    """
    seen = collections.Counter(
        (band(l, LNC_BANDS), band(g, GNE_BANDS)) for l, g in rolls)

    assert len(seen) == 9, f"only {len(seen)} alignments produced: {sorted(seen)}"
    for alignment, count in seen.items():
        share = count / len(rolls)
        assert 0.07 < share < 0.16, \
            f"{alignment} is {share:.1%} of rolls, expected about 11.1%"


def test_true_neutral_does_not_dominate(rolls):
    """(5/5) alone was 35% of every NPC ever generated."""
    share = sum(1 for l, g in rolls if (l, g) == (5, 5)) / len(rolls)

    assert share < 0.04, f"(5/5) is {share:.1%} of rolls"


def test_the_extremes_are_reachable(rolls):
    """A 1 or a 9 never appeared once in 20,000 rolls of the old generator."""
    scores = {s for pair in rolls for s in pair}

    assert 1 in scores and 9 in scores


def test_the_whole_grid_is_reachable(rolls):
    """25 of 81 points under averaging; all 81 should now occur."""
    points = {pair for pair in rolls}

    assert len(points) == 81, f"only {len(points)} of 81 points produced"


def test_headline_is_not_derivable_from_the_trait_scores(rolls):
    """
    Independence is the design: it is what makes two Lawful Good NPCs read
    differently. If the headline ever tracks the trait mean again, the grid
    collapses back to the Neutral core.
    """
    means, headlines = [], []
    for _ in range(400):
        dna = generate_npc_dna()
        lnc, _gne = headline(dna)
        paired = dna.split(") ", 1)[1].split(" - ")[0].split(",")
        means.append(sum(int(p[0]) for p in paired) / len(paired))
        headlines.append(lnc)

    # Correlation, not spread: under the old code the headline WAS the mean, so
    # r was 1.0 by construction. Independent draws give r near 0, and the
    # standard error at n=400 is 0.05, so 0.25 is ~5 sigma from a fluke.
    n = len(means)
    mx, my = sum(headlines) / n, sum(means) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(headlines, means))
    vx = sum((a - mx) ** 2 for a in headlines) ** 0.5
    vy = sum((b - my) ** 2 for b in means) ** 0.5
    r = cov / (vx * vy)

    assert abs(r) < 0.25, f"headline correlates with the trait mean (r={r:.2f})"
    assert max(headlines) - min(headlines) >= 6, "headline barely moves"


# --- seeding and pinning --------------------------------------------------

def test_a_seed_reproduces_the_whole_npc():
    assert generate_npc_dna(seed=7) == generate_npc_dna(seed=7)
    assert generate_npc_dna(seed=7) != generate_npc_dna(seed=8)


def test_pinning_the_alignment_letter_fixes_the_band_only():
    scores = {headline(generate_npc_dna(lnc="L", gne="E"))
              for _ in range(60)}

    for lnc, gne in scores:
        assert lnc in LNC_BANDS["L"], "should be Lawful"
        assert gne in GNE_BANDS["E"], "should be Evil"
    assert len({l for l, _ in scores}) > 1, "the exact score should still vary"


def test_pinning_an_exact_score_fixes_the_point():
    for _ in range(20):
        assert headline(generate_npc_dna(lnc_score=9, gne_score=1)) == (9, 1)


def test_pins_leave_the_traits_free():
    a = generate_npc_dna(lnc="L", gne="G")
    b = generate_npc_dna(lnc="L", gne="G")

    assert a != b, "only the alignment was pinned"


@pytest.mark.parametrize("pins,match", [
    ({"lnc": "Q"}, "must be one of"),
    ({"gne": "X"}, "must be one of"),
    ({"lnc_score": 0}, "int 1-9"),
    ({"lnc_score": 10}, "int 1-9"),
    ({"lnc_score": True}, "int 1-9"),
    ({"alignment": "LG"}, "Unknown npc pin"),
    ({"lnc": "L", "lnc_score": 8}, "contradictory"),
])
def test_bad_pins_are_rejected(pins, match):
    with pytest.raises(ValueError, match=match):
        generate_npc_dna(**pins)


def test_a_bool_score_cannot_reach_the_dna():
    """bool is an int subclass: True would write '(True/5)' into the genome."""
    with pytest.raises(ValueError):
        generate_npc_dna(gne_score=True)


# --- faction --------------------------------------------------------------

def test_faction_seed_reproduces():
    assert generate_faction_dna(seed=3) == generate_faction_dna(seed=3)
    assert generate_faction_dna(seed=3) != generate_faction_dna(seed=4)


def test_faction_dna_shape_is_unchanged():
    segments = generate_faction_dna(seed=1).split("-")

    assert len(segments) == len(FACTION_AXES)
    for segment, options in zip(segments, FACTION_AXES.values()):
        assert segment in options


@pytest.mark.parametrize("value", ["T3", "3", 3])
def test_faction_pins_accept_bare_or_prefixed_values(value):
    assert generate_faction_dna(T=value, seed=1).split("-")[0] == "T3"


def test_faction_pins_handle_zero_padded_axes():
    """G and L pad to two digits; a caller passing 5 should still work."""
    dna = generate_faction_dna(G=5, L=9, seed=1).split("-")

    assert "G05" in dna and "L09" in dna


def test_faction_pin_is_case_insensitive():
    assert generate_faction_dna(sc=2, seed=1).split("-")[11] == "SC2"


def test_unknown_or_invalid_faction_pins_are_rejected():
    with pytest.raises(ValueError, match="Unknown faction pin"):
        generate_faction_dna(ZZ=1)
    with pytest.raises(ValueError, match="not in"):
        generate_faction_dna(T=99)


def test_pinned_faction_axes_do_not_disturb_the_others():
    a = generate_faction_dna(T=1)
    b = generate_faction_dna(T=1)

    assert a.startswith("T1-") and b.startswith("T1-")
    assert a != b
