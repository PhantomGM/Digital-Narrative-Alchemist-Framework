"""
The contract is the stop condition, and it is a graph.

Every test here is a defect the Session 0 trial actually produced. See
testing/session_zero/03_findings.md.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.content_contract import (  # noqa: E402
    ContentContract, ContractError, RuntimeDirectives, Slot)
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402


def slot(name, deps=(), **kw):
    kw.setdefault("brief", f"the {name}")
    return Slot(type=kw.pop("type", name), depends_on=tuple(deps), key=name, **kw)


# --- a count is not a brief -------------------------------------------------

def test_a_slot_cannot_exist_without_a_brief():
    """
    The trial's first defect: the contract was (type, count), the slot notes
    lived only in a print statement, and the regional_poi briefed as "the mine"
    generated a dimensional arch on a plateau.
    """
    with pytest.raises(ValueError, match="no brief"):
        Slot(type="regional_poi", brief="   ")


def test_the_brief_reaches_the_prompt():
    s = slot("mine", type="regional_poi", brief="THE MINE beneath the town.")
    text = ContentContract("pitch", [s]).brief_for(s)
    assert "THE MINE beneath the town." in text
    assert "the brief wins" in text


def test_multi_count_slots_are_told_they_must_differ():
    """Three factions that are variations on one idea is a coalition."""
    s = slot("faction", count=3, brief="Asymmetric in kind.")
    text = ContentContract("pitch", [s]).brief_for(s, index=1)
    assert "number 2 of 3" in text
    assert "distinct" in text


# --- the contract is a graph ------------------------------------------------

def test_dependencies_decide_the_order():
    """
    The trial generated `linguistic` sixth and `settlement` third, so the town
    was named before the naming rules existed.
    """
    contract = ContentContract("pitch", [
        slot("settlement", deps=("linguistic",)),
        slot("linguistic"),
    ])
    assert [s.name for s in contract.ordered()] == ["linguistic", "settlement"]


def test_order_is_stable_across_runs():
    """Two runs of one contract must be comparable."""
    contract = ContentContract("pitch", [
        slot("world"), slot("region", deps=("world",)),
        slot("culture", deps=("world",)), slot("linguistic", deps=("culture",)),
    ])
    assert [s.name for s in contract.ordered()] == \
           [s.name for s in contract.ordered()]


def test_a_cycle_is_refused_and_named():
    contract = ContentContract("bad", [
        slot("a", deps=("b",)), slot("b", deps=("a",))])
    with pytest.raises(ContractError, match="cycle"):
        contract.ordered()


def test_a_dependency_nothing_provides_is_refused():
    contract = ContentContract("bad", [slot("settlement", deps=("linguistic",))])
    with pytest.raises(ContractError, match="no slot provides"):
        contract.validate()


def test_duplicate_slot_names_are_refused():
    contract = ContentContract("bad", [slot("faction"), slot("faction")])
    with pytest.raises(ContractError, match="duplicate"):
        contract.validate()


def test_a_contract_cannot_require_what_the_forge_cannot_make():
    contract = ContentContract("bad", [slot("deity")])
    with pytest.raises(ContractError, match="no generator"):
        contract.validate(known_types=list(ProceduralForge().generators))


def test_a_realistic_contract_validates_against_the_real_forge():
    contract = ContentContract("pitch", [
        slot("world"),
        slot("culture", deps=("world",)),
        slot("linguistic", deps=("culture",)),
        slot("region", deps=("world",)),
        slot("settlement", deps=("region", "linguistic")),
        slot("faction", count=3, deps=("settlement",)),
    ])
    contract.validate(known_types=list(ProceduralForge().generators))
    order = [s.name for s in contract.ordered()]
    assert order.index("linguistic") < order.index("settlement")
    assert order.index("settlement") < order.index("faction")
    assert contract.total_entities() == 8


# --- tone, which a quota cannot express -------------------------------------

def test_a_tonal_mandate_reaches_the_prompt_and_outranks_the_genome():
    """
    The trial's third defect: warmth was asked for, was in the shared block,
    and every entity still came out grim.
    """
    s = slot("tavern", type="establishment", brief="Somewhere to breathe.",
             tone="Warm. Nothing is wrong here and nothing is about to be.")
    text = ContentContract("pitch", [s]).brief_for(s)
    assert "Nothing is wrong here" in text
    assert "outranks" in text


def test_tone_is_optional():
    s = slot("faction")
    assert "Tonal requirement" not in ContentContract("p", [s]).brief_for(s)


# --- invariants: constraints a slot brief must not out-argue ----------------

def test_an_invariant_rides_inside_every_brief():
    """
    Trial 5's defect. The table asked for room to breathe, which sat in the
    shared context block; the hook's brief asked for danger within the hour.
    The brief won and two of four players objected to the pace on reading the
    pitch. A brief is local and specific, a shared block global and general,
    and specific wins -- so a constraint that must not be overridden has to
    compete at the same level.
    """
    contract = ContentContract("pitch", [slot("quest"), slot("npc")],
                               invariants=["Never open on a countdown."])
    for s in contract.slots:
        text = contract.brief_for(s)
        assert "Never open on a countdown." in text


def test_an_invariant_says_it_outranks_the_brief():
    contract = ContentContract("pitch", [slot("quest")],
                               invariants=["Never open on a countdown."])
    text = contract.brief_for(contract.slots[0])
    assert "outrank the brief" in text
    assert text.index("the quest") < text.index("Never open on a countdown.")


def test_a_contract_without_invariants_adds_no_section():
    contract = ContentContract("pitch", [slot("quest")])
    assert "STANDING RULES" not in contract.brief_for(contract.slots[0])


def test_invariants_survive_alongside_tone_and_multi_count():
    """The three brief modifiers must not shadow one another."""
    s = slot("establishment", count=2, tone="Warm.", brief="A galley.")
    contract = ContentContract("pitch", [s], invariants=["No countdowns."])
    text = contract.brief_for(s, index=1)
    assert "A galley." in text
    assert "Warm." in text
    assert "number 2 of 2" in text
    assert "No countdowns." in text


# --- the stop condition -----------------------------------------------------

def test_unfilled_reports_what_is_still_owed():
    contract = ContentContract("pitch", [slot("npc", count=3), slot("lore")])
    assert contract.unfilled({"npc": 1}) == {"npc": 2, "lore": 1}


def test_satisfied_when_every_slot_is_filled():
    contract = ContentContract("pitch", [slot("npc", count=2), slot("lore")])
    assert not contract.is_satisfied({"npc": 2})
    assert contract.is_satisfied({"npc": 2, "lore": 1})


def test_overshooting_a_slot_still_counts_as_satisfied():
    """The contract is a floor for completion, not a cap on the author."""
    contract = ContentContract("pitch", [slot("npc", count=2)])
    assert contract.is_satisfied({"npc": 5})


# --- the other half of Session 0 --------------------------------------------

def test_runtime_directives_are_not_slots():
    """
    Nothing here is generated and nothing here is ever "filled", so a directive
    must not be able to hold the contract open.
    """
    contract = ContentContract("pitch", [slot("npc")], RuntimeDirectives(
        pacing=["Alternate town and deep."],
        signals=["Silence from a player is not a distress signal."]))
    assert contract.is_satisfied({"npc": 1})


def test_directives_render_only_what_they_have():
    d = RuntimeDirectives(spotlight=["Recognise the healer socially."])
    text = d.render()
    assert "Spotlight" in text and "Pacing" not in text
    assert not RuntimeDirectives().render()
    assert RuntimeDirectives().is_empty()
