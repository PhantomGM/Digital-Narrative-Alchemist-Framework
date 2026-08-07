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


def alignment_section(decoder):
    return decoder.split("HEADLINE ALIGNMENT")[1].split("**2. PAIRED TRAITS")[0]


def test_every_distance_from_centre_has_a_reading(decoder):
    """
    A band boundary is not a reading: the original decoder gave only
    9-7/6-4/3-1, so L7 and L9 were the same character to it. Every distance
    from the centre must say something different, which covers all nine values
    since each distance names its pair.
    """
    section = alignment_section(decoder)
    for distance in range(0, 5):
        assert re.search(rf"Dist {distance}\b", section), \
            f"distance {distance} has no reading"
    for score in range(1, 10):
        assert re.search(rf"\b{score}\b", section), f"score {score} unreachable"


def test_commitment_is_measured_as_distance_from_the_centre(decoder):
    """The organising idea: 5 is the null point, and 1 and 9 are the poles."""
    section = alignment_section(decoder)

    assert "distance" in section.lower()
    assert re.search(r"Dist 4 \(9 or 1\)", section), "the poles must be the extreme"
    assert re.search(r"Dist 0 \(5\)", section), "5 must be the null point"


def test_the_bands_are_ordered_from_absolute_to_detached(decoder):
    """
    Apex -> Anchor -> Fringe -> Lean -> Void is a gradient. If two adjacent
    bands read the same the scale has collapsed back to three flat bands.
    """
    section = alignment_section(decoder)
    order = [section.index(name) for name in
             ("The Apex", "The Anchor", "The Fringe", "The Lean", "The Void")]

    assert order == sorted(order), "bands are out of order"
    assert "Cannot yield" in section          # Apex
    assert "Easily discarded" in section      # Lean
    assert "detachment" in section            # Void


def test_a_lean_does_not_cross_the_line(decoder):
    """
    6 is not Good and 4 is not Evil. Rendering a lean as the alignment itself
    silently converts a third of the Neutral band into its neighbour.
    """
    section = alignment_section(decoder)

    assert re.search(r"Dist 1 \(6 or 4\)", section)
    assert "Preference-based" in section


def test_the_conflict_rule_says_which_axis_yields(decoder):
    """
    Two characters can share an alignment and be opposites depending on which
    commitment is harder. Reading each axis alone cannot express that.
    """
    section = alignment_section(decoder)

    assert "Yielding Axiom" in section
    assert "lower Distance to 5 yields" in section


def test_equal_commitments_have_named_outcomes(decoder):
    """
    Equal distances are the interesting case: at the poles nothing gives and
    the character breaks; at the fringe both give and they adapt.
    """
    section = alignment_section(decoder)

    assert "Systemic Paralysis" in section and "Freeze" in section
    assert "Fluid Triage" in section and "Pivot" in section
    assert "break rather than bend" in section


def test_each_quadrant_subdivides(decoder):
    """
    The 81-point grid has to mean something below the nine alignments, or the
    extra resolution is decorative.
    """
    section = alignment_section(decoder)

    assert "Fractal Sub-Grid" in section
    assert re.search(r"`\d/\d`", section), "no sub-archetype coordinates given"


def test_the_headline_is_not_described_as_an_average(decoder):
    """It was drawn from an average until the distribution fix; it is not now."""
    head = decoder.split("**2. PAIRED TRAITS")[0]

    assert "ALIGNMENT AVERAGES" not in head
    assert "not average them from the traits" in head or "not averaged" in head


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


def test_contradictions_are_framed_as_the_point_not_as_errors(decoder):
    """
    The 39 traits are rolled independently precisely so they collide. If the
    decoder reads as an instruction to tidy that up, the genome's main source
    of depth is sanded off on the way to the page.
    """
    section = decoder.split("**4. CONTRADICTIONS")[1].split("---")[0]

    assert "not bad rolls" in section.lower() or "not errors" in section.lower()
    assert "never by averaging" in section
    assert "flattened" in section


def test_contradiction_section_names_its_lens(decoder):
    """Every other decoder names one -- ecology, transmission, circumstance."""
    section = decoder.split("**4. CONTRADICTIONS")[1].split("---")[0]

    assert "lived history" in section
    assert "Biography is this decoder's lens" in section


def test_reconcile_is_disambiguated_from_settle(decoder):
    """
    'Resolve' carries both senses across the decoder set: make believable, and
    answer an open question. The second is forbidden by a standing rule, so the
    creative sense must not be spelled the same way.
    """
    section = decoder.split("**4. CONTRADICTIONS")[1].split("---")[0]

    assert "Reconcile contradictions" in section
    assert "It never means settle" in section
    assert "Resolve contradictions through:" not in decoder


def test_backstory_is_where_the_contradiction_gets_its_origin(decoder):
    section = decoder.split("**Backstory**")[1][:900]

    assert "contradiction" in section.lower()


def test_paired_key_matches_the_generator_slot_for_slot(decoder):
    """
    A live decode read slot 15 ('2C5', Calm) as Hot-headed, slot 7 ('9U3',
    Impulsive) as methodical, and slot 18 ('3A4', Apathetic) as driven. Letters
    repeat across slots -- C is Cowardly in slot 1 and Calm in slot 15 -- so the
    key is only usable if it is positional and matches the generator exactly.
    """
    from layer5_dna_substrate.generators.npc import LNC_TRAITS

    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([A-Z])\s*/\s*([A-Z])\s*\|",
                      decoder, re.M)
    by_slot = {int(n): (a, b) for n, a, b in rows}

    assert len(by_slot) == len(LNC_TRAITS) == 20
    for index, pair in enumerate(LNC_TRAITS, start=1):
        assert by_slot[index] == pair, \
            f"slot {index}: decoder says {by_slot[index]}, generator emits {pair}"


def test_unpaired_key_matches_the_generator_slot_for_slot(decoder):
    """
    The key listed E=Empathetic at slot 9, which the generator never emits, so
    every slot from 9 on was shifted by one against the genome. Harmless while
    the model matched by letter; corrupting the moment it reads by position.
    """
    from layer5_dna_substrate.generators.npc import GNE_TRAITS

    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([A-Z])\s*\|\s*[A-Z][a-z]", decoder, re.M)
    by_slot = {int(n): letter for n, letter in rows}

    assert len(by_slot) == len(GNE_TRAITS) == 19
    for index, letter in enumerate(GNE_TRAITS, start=1):
        assert by_slot[index] == letter, \
            f"slot {index}: decoder says {by_slot[index]}, generator emits {letter}"
    assert "Empathetic" not in decoder, "not in the genome; would shift every later slot"


def test_positional_reading_is_stated_for_both_trait_blocks(decoder):
    assert decoder.count("READ THESE BY POSITION") == 2
    assert "Letters repeat across slots" in decoder
    assert "count to the slot, then read the letter" in decoder


def test_the_paired_score_is_told_not_to_flip_the_trait(decoder):
    """The observed failure: a low score on C read as its opposite."""
    section = decoder.split("**2. PAIRED TRAITS")[1].split("**3.")[0]

    assert "the score never overrides it" in section
    assert "It does not flip to Brave" in section
    assert "do not carry that rule over here" in section


def test_no_scaffolding_rule_sits_with_the_output_template(decoder):
    """One decode printed '(2C5)' into its backstory; the rule was 120 lines up."""
    tail = decoder.split("STRUCTURED OUTPUT FORMAT")[1]

    assert "No scaffolding below this line" in tail


def test_the_tell_is_derived_from_magnitude_not_chosen(decoder):
    """
    Five decodes of one DNA string produced a handled fidget object in four --
    puzzle cube, glass marble, aetherium shard, salvage lens. Nothing in the
    genome asked for that; it was the model's favourite answer to an open
    question.

    The earlier fix offered a menu of seven modalities and forbade the trope by
    name, which worked but left the choice free. This is stronger: the DNA fixes
    the SEVERITY of the reaction and context supplies only its form, so the
    genome decides the part a model would otherwise default on.
    """
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    assert "Magnitude" in section
    assert "distance from 5" in section
    for state in ("Freeze", "Leak", "Pivot", "Drift", "Flatline"):
        assert state in section, f"no tell for the {state} band"


def test_every_magnitude_band_has_its_own_tell(decoder):
    """If two bands share a tell the severity scale is decorative."""
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    for band in ("Apex", "Anchor", "Fringe", "Lean", "Void"):
        assert band in section, f"band {band} has no row"
    assert "9/1" in section and "6/4" in section


def test_the_form_still_comes_from_the_world(decoder):
    """
    Severity is the genome's; the costume is the setting's. Without this the
    same DNA would render identically in five different worlds, which is the
    convergence the whole fix exists to break.
    """
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    assert "trade" in section and "environment" in section
    assert "dress it in the setting" in section


def test_the_severity_may_not_be_overridden_by_flavour(decoder):
    """A 9/1 fanatic does not fidget; a 6/4 does not boom dogma."""
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    assert "Commit to the Magnitude" in section


def test_backstory_arcs_are_offered_as_peers(decoder):
    """Trauma -> secret violation -> duplicitous authority in 5 of 5 decodes."""
    section = decoder.split("CHOOSE THE ARC")[1].split("---")[0]

    for arc in ("Inheritance", "Slow ideological corruption", "Forced oath",
                "Sudden unwanted elevation", "Quiet complicity",
                "Trauma and secret violation"):
        assert arc in section, f"arc missing: {arc}"
    assert "It is one of six, not the default" in section


def test_the_band_boundaries_still_agree_with_the_generator(decoder):
    """The generator's bands and the decoder's bands must not drift apart."""
    from layer5_dna_substrate.generators.npc import GNE_BANDS, LNC_BANDS

    assert LNC_BANDS == {"L": (7, 8, 9), "N": (4, 5, 6), "C": (1, 2, 3)}
    assert GNE_BANDS == {"G": (7, 8, 9), "N": (4, 5, 6), "E": (1, 2, 3)}
    assert "9–7 = Lawful, 6–4 = Neutral, 3–1 = Chaotic" in decoder
    assert "9–7 = Good, 6–4 = Neutral, 3–1 = Evil" in decoder
