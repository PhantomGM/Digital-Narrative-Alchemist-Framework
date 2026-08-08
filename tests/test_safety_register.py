"""
Lines and Veils: a structure that can hold what players actually said, and a
path that reaches generation rather than only filtering.

Every distinction tested here came out of one Session 0 interview
(testing/session_zero/01_round1_transcript.md), and the previous structure --
one flat list of strings per player -- could represent none of them.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer3_operations.player_profiles import PlayerProfileManager  # noqa: E402
from layer3_operations.safety_register import (  # noqa: E402
    LINE, SCENE, SETTING, VEIL, SafetyConstraint, SafetyRegister)
from layer5_dna_substrate.context_assembler import ContextPackage  # noqa: E402


def register(*constraints):
    return SafetyRegister(list(constraints))


# --- a Line is not a Veil ---------------------------------------------------

def test_lines_and_veils_are_rendered_apart():
    text = register(
        SafetyConstraint("sexual violence", kind=LINE),
        SafetyConstraint("graphic torture", kind=VEIL),
    ).render()
    assert "LINES" in text and "VEILS" in text
    assert text.index("sexual violence") < text.index("VEILS")
    assert text.index("graphic torture") > text.index("VEILS")


def test_a_veil_says_refer_not_depict():
    text = register(SafetyConstraint("graphic torture", kind=VEIL)).render()
    assert "never depicted" in text or "cut away" in text


def test_a_line_says_never_in_any_form():
    text = register(SafetyConstraint("sexual violence", kind=LINE)).render()
    assert "never appear" in text


# --- scope: the constraint an output filter cannot catch --------------------

def test_setting_scope_says_so_explicitly():
    """
    One player's bigotry Line bound the SETTING: "even if no one's PC ever
    encounters it directly". A culture page carrying it reads fine alone, so
    only a generation-time constraint can prevent it.
    """
    text = register(SafetyConstraint(
        "real-world bigotry", kind=LINE, scope=SETTING)).render()
    assert "binds the SETTING" in text
    assert "background flavour" in text


def test_scene_scope_stays_quiet():
    text = register(SafetyConstraint("sexual violence", scope=SCENE)).render()
    assert "binds the SETTING" not in text


def test_a_players_qualification_survives():
    """Marcus: the animal Line is about on-screen death, not about animals."""
    text = register(SafetyConstraint(
        "animal cruelty", kind=LINE,
        note="No pet or companion dies on screen")).render()
    assert "on screen" in text


# --- merging must never weaken ----------------------------------------------

def test_a_line_beats_a_veil_when_two_players_disagree():
    merged = register(
        SafetyConstraint("torture", kind=VEIL),
        SafetyConstraint("Torture", kind=LINE),
    ).merged()
    assert [c.kind for c in merged.constraints] == [LINE]


def test_setting_scope_beats_scene_scope():
    merged = register(
        SafetyConstraint("bigotry", scope=SCENE),
        SafetyConstraint("bigotry", scope=SETTING),
    ).merged()
    assert merged.constraints[0].scope == SETTING


def test_shared_boundaries_collapse_to_one_entry():
    """Three of four trial players listed sexual violence."""
    merged = register(*[SafetyConstraint("sexual violence", holders=(p,))
                        for p in ("elias", "sarah", "chloe")]).merged()
    assert len(merged.constraints) == 1
    assert set(merged.constraints[0].holders) == {"elias", "sarah", "chloe"}


def test_notes_accumulate_rather_than_overwrite():
    merged = register(
        SafetyConstraint("animal cruelty", note="Not on screen"),
        SafetyConstraint("animal cruelty", note="No familiars either"),
    ).merged()
    assert "Not on screen" in merged.constraints[0].note
    assert "No familiars either" in merged.constraints[0].note


# --- privacy ----------------------------------------------------------------

def test_holders_are_never_rendered():
    """
    One trial player could not raise a Veil aloud at all. A prompt naming who
    asked for what puts it back in the room.
    """
    text = register(SafetyConstraint(
        "romance involving PCs", kind=VEIL, holders=("chloe", "marcus"))).render()
    assert "chloe" not in text.lower()
    assert "marcus" not in text.lower()


# --- shrinking drops whole items, never half a Line -------------------------

def test_fit_drops_veils_before_lines():
    reg = register(
        SafetyConstraint("a setting line", kind=LINE, scope=SETTING),
        SafetyConstraint("a scene line", kind=LINE),
        SafetyConstraint("a droppable veil", kind=VEIL),
    )
    fitted = reg.fit(len(reg.render()) - 20)
    assert "a setting line" in fitted and "a scene line" in fitted
    assert "a droppable veil" not in fitted


def test_nothing_is_ever_cut_mid_constraint():
    reg = register(SafetyConstraint("a line about a specific difficult thing"),
                   SafetyConstraint("a veil", kind=VEIL))
    for budget in range(50, len(reg.render()) + 50, 25):
        fitted = reg.fit(budget)
        for fragment in fitted.splitlines():
            if fragment.startswith("- ") and "none recorded" not in fragment:
                assert fragment.rstrip().endswith("."), \
                    f"constraint severed mid-sentence at budget {budget}: {fragment!r}"


def test_lines_survive_a_budget_that_fits_nothing():
    """
    The header and intros are a fixed ~600 chars, so a small enough budget fits
    no constraint at all. Returning an empty block would silently remove every
    Line -- the one outcome worse than the overflow it was avoiding. Overspending
    a budget is recoverable; a prompt with no Lines in it is not.
    """
    reg = register(SafetyConstraint("sexual violence", kind=LINE),
                   SafetyConstraint("graphic torture", kind=VEIL))
    fitted = reg.fit(10)
    assert "sexual violence" in fitted
    assert "graphic torture" not in fitted


def test_fit_is_a_noop_when_it_fits():
    reg = register(SafetyConstraint("sexual violence"))
    assert reg.fit(10_000) == reg.render()


# --- validation -------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    {"kind": "maybe"}, {"scope": "sometimes"}, {"text": "  "},
])
def test_a_malformed_constraint_is_refused(bad):
    kwargs = {"text": "x", **bad}
    with pytest.raises(ValueError):
        SafetyConstraint(**kwargs)


# --- the path into generation AND audit -------------------------------------

def test_safety_reaches_both_surfaces():
    """
    The whole architectural point. canon_slice() excludes `directives`, so a
    constraint placed there would steer generation and never be verified.
    """
    block = register(SafetyConstraint("sexual violence")).render()
    package = ContextPackage(safety=block, world_frame="A world.",
                             directives="some guidance")
    assert "sexual violence" in package.for_decoder()
    assert "sexual violence" in package.canon_slice()
    assert "some guidance" not in package.canon_slice()  # directives still excluded


def test_safety_is_emitted_before_everything_else():
    package = ContextPackage(safety="SAFETY BLOCK", world_frame="WORLD FRAME")
    text = package.for_decoder()
    assert text.index("SAFETY BLOCK") < text.index("WORLD FRAME")


def test_an_empty_register_adds_nothing():
    assert SafetyRegister().render() == ""
    assert ContextPackage(world_frame="A world.").for_decoder().startswith("## WORLD")


# --- the manager ------------------------------------------------------------

def test_the_manager_builds_a_block_without_naming_players():
    mgr = PlayerProfileManager()
    mgr.register_profile("chloe", [
        SafetyConstraint("animal cruelty", kind=LINE),
        SafetyConstraint("romance involving PCs", kind=VEIL)])
    mgr.register_profile("sarah", [
        SafetyConstraint("real-world bigotry", kind=LINE, scope=SETTING)])

    block = mgr.safety_block()
    assert "animal cruelty" in block and "real-world bigotry" in block
    assert "binds the SETTING" in block
    assert "chloe" not in block.lower() and "sarah" not in block.lower()


def test_the_legacy_flat_list_still_works_and_reads_strictly():
    """
    Callers passing an undifferentiated list must keep working, and an
    unlabelled boundary must be read as a Line -- the strictest available
    reading. Guessing softer is the wrong error to make.
    """
    mgr = PlayerProfileManager()
    mgr.register_player("old", ["sexual violence", "torture"])
    block = mgr.aggregate_safety_boundaries(["old"])
    assert "sexual violence" in block
    assert block.index("sexual violence") < block.index("VEILS")


def test_the_governor_gets_a_usable_default_when_nobody_registered():
    mgr = PlayerProfileManager()
    assert "PG-13" in mgr.aggregate_safety_boundaries([])
