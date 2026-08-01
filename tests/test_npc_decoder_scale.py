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


def test_the_axis_conflict_rule_is_stated(decoder):
    """
    Two characters can share an alignment and be opposites depending on which
    axis is the harder commitment. The per-score table cannot say that, because
    it reads each axis on its own.
    """
    assert "AXIS CONFLICT" in decoder
    assert "the axis closer to 5 is the one that yields" in decoder.lower() \
        or "axis closer to 5 is the one that yields" in decoder


def test_equal_extremes_break_rather_than_bend(decoder):
    """L9/G9 is the lawful-stupid paladin as a mechanic, not a reputation."""
    section = decoder.split("AXIS CONFLICT")[1].split("**2.")[0]

    assert "L9/G9" in section
    assert "break" in section


def test_both_asymmetric_paladins_are_distinguished(decoder):
    section = decoder.split("AXIS CONFLICT")[1].split("**2.")[0]

    assert "L8/G7" in section and "L7/G8" in section
    assert section.index("L8/G7") != section.index("L7/G8")


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


def test_expression_modality_is_chosen_from_context_not_habit(decoder):
    """
    Five decodes of one DNA string produced a handled fidget object in four --
    puzzle cube, glass marble, aetherium shard, salvage lens. Nothing in the
    genome asks for that; it is the model's favourite answer. The one that broke
    the pattern (unnatural stillness) came from the most constrained context,
    so the cure is to make the modality a context question.
    """
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    for modality in ("stillness", "Breath", "Gaze", "Posture",
                     "Environmental", "Ritualised", "handled object"):
        assert modality in section, f"modality missing: {modality}"
    assert "Do not default to the handled object" in section
    assert "must come from their trade, environment and role" in section


def test_the_trope_modality_is_not_listed_first(decoder):
    """A menu's first item becomes the new default; the trope must not hold it."""
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    assert section.index("Conspicuous stillness") < section.index("A handled object")


def test_only_one_modality_is_requested(decoder):
    """Hedging across several tells reads as a list, not a person."""
    section = decoder.split("HOW THE TENSION SHOWS")[1].split("**Backstory**")[0]

    assert "One modality" in section


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
