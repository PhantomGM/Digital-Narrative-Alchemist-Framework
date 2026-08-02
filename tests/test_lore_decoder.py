"""
Tests for the lore decoder's refinement pass.

Same no-answer failure as creature and culture, plus one that is worse in kind:
PROOF and RESOLVE are rolled independently, so 4.0% of lore arrives claiming
both that no evidence survives and that the matter is *resolvable* -- "the truth
can be established by someone who finds the proof" when there is no proof. That
sits inside RESOLVE, which is the field the canon-safety rule leans on, and the
obvious way for a model to relieve the tension is to invent surviving evidence.

Three absences were undocumented besides: RIVAL:none-openly at 14.7%,
PROOF:none-remaining at 12.0%, KEEPER:no-one-now at 11.1%.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "lore.md")


@pytest.fixture(scope="module")
def decoder():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_every_block_the_generator_emits_is_documented(decoder):
    from layer5_dna_substrate.generators.lore import generate_lore_dna

    for block in set(re.findall(r"([A-Z]+)\{", generate_lore_dna(seed=42))):
        assert re.search(rf"`{block}" + r"\{", decoder) or block == "LORE", \
            f"{block} emitted but never documented"


def test_all_three_resolve_states_are_defined(decoder):
    """RESOLVE is what stops a generated page settling an open question."""
    for state in ("resolvable", "contested", "unknowable"):
        assert f"**{state}**" in decoder


def test_no_proof_is_read_against_each_resolve_state(decoder):
    """
    The cross-field case. Independently rolled, so 4.0% of lore says the matter
    is settleable and that nothing survives to settle it with.
    """
    section = decoder.split("`PROOF:none-remaining` read against RESOLVE")[1]
    section = section.split("**4. `KEEP")[0]

    for state in ("resolvable", "contested", "unknowable"):
        assert f"**{state}**" in section, f"no reading given for {state}"
    assert "not a contradiction" in section
    assert "do not invent evidence" in decoder.lower()


def test_the_settleable_case_becomes_a_hook_not_a_fudge(decoder):
    section = decoder.split("`PROOF:none-remaining` read against RESOLVE")[1]

    assert "strongest hook" in section
    assert "who destroyed it" in section


@pytest.mark.parametrize("value", ["KEEPER:no-one-now", "RIVAL:none-openly",
                                   "SANCTION:none", "PROOF:none-remaining"])
def test_each_absence_is_addressed(decoder, value):
    section = decoder.split("ABSENCES")[1].split("CONTRADICTIONS")[0]

    assert f"`{value}`" in section, f"unhandled absence: {value}"


def test_absences_say_what_to_write_instead(decoder):
    """Telling a model only what to omit leaves a hole it will fill anyway."""
    section = decoder.split("ABSENCES")[1].split("CONTRADICTIONS")[0]

    assert "never invent the thing the dna says is missing" in section.lower()
    assert "who *used* to keep it" in section        # KEEPER
    assert "what happened to the losers" in section  # RIVAL
    assert "opposite from within" in section         # SANCTION


def test_an_orphaned_belief_cannot_still_be_enforcing(decoder):
    """KEEPER:no-one-now interacts with SANCTION and ZEAL, which stay populated."""
    section = decoder.split("`KEEPER:no-one-now`")[1][:600]

    assert "cannot enforce" in section
    assert "once" in section


def test_contradictions_keep_their_transmission_lens(decoder):
    assert "transmission and interest" in decoder


def test_canon_outranks_the_resolve_field(decoder):
    assert "Rule 7 outranks this field" in decoder
