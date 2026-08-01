"""
Tests that the world's naming conventions reach the decoder.

The linguistic decoder describes itself as a "Root Truth ... to ensure
consistency across all future NPCs, Locations, and Factions", and the assembler
did look one up — but it appended the result inside _build_world_frame, which is
then capped to a fraction of the budget. The World Overview alone overflows that
fraction, so the conventions were trimmed off every prompt that ever ran. The
same failure the standing rulings had, in the same function, one layer down.

The visible symptom: one DNA string decoded against five worlds produced three
characters surnamed Vane and two named Lyra. Nothing in the genome governs
names, so the model used its own defaults.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.context_assembler import (  # noqa: E402
    AssemblyRequest, ContextAssembler,
)
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

PROFILE = """### **Throat-Speak Resonance**

**Phonetic Patterns:**
* **Consonant Tone:** Hard, guttural stops.

**Naming Conventions:**
* **NPC Names:** Kharr-Vel, Ussoth, Dremmen-Ka, Yarrik, Vosh-Tal.
  Rules: every personal name carries a doubled consonant, and anyone of rank
  takes a hyphenated suffix naming their trade.
* **Location Names:** Gharn-Deep, Ussol Reach, The Vosh.
  Rules: places are named for what was taken out of them.
* **Faction Names:** The Unbroken Ledger, Sons of the Grate.

**Common Idioms & Taboos:**
* Sayings: "salt on the seal" means a bargain nobody intends to keep.
"""


def build(with_profile=True, stub_too=False):
    reg = DNARegistry()
    world = reg.register_element("world", "W{}", "A hard world.", name="Skarn",
                                 tags=["canonized"])
    if stub_too:
        stub = reg.register_element("linguistic", "", "", name=None, tags=["stub"])
        reg.get_element(stub)["stub_metadata"] = {
            "name": "The Breath-Chants", "description": "Sung liturgy.",
            "source_id": world}
    if with_profile:
        reg.register_element("linguistic", "LING{}", PROFILE,
                             name="Throat-Speak Resonance", tags=["canonized"],
                             gist="The world's tongue.")
    return reg, world


def package(reg, anchor=None, budget=1200):
    assembler = ContextAssembler(reg)
    return assembler.assemble(AssemblyRequest(element_type="npc",
                                              anchor_id=anchor,
                                              budget_tokens=budget))


def test_naming_conventions_reach_the_decoder():
    reg, _ = build()
    text = package(reg).for_decoder()

    assert "Kharr-Vel" in text, "the worked example names must survive"
    assert "doubled consonant" in text, "the rule behind them must survive too"


def test_they_survive_a_budget_far_too_small_to_hold_them():
    """
    The bug: appended before the cap, behind a World Overview that already
    overflows it. A tiny budget is the regression test.
    """
    reg, _ = build()
    text = package(reg, budget=40).for_decoder()

    assert "Kharr-Vel" in text
    assert "doubled consonant" in text


def test_the_block_is_marked_canon():
    reg, _ = build()
    text = package(reg).for_decoder()

    assert "NAMING CONVENTIONS" in text
    assert "must obey" in text


def test_a_stub_never_shadows_a_written_profile():
    """
    Skarn's only two linguistic records are stubs. Anchoring to one supplies no
    conventions while still looking like a hit.
    """
    reg, _ = build(with_profile=True, stub_too=True)
    text = package(reg).for_decoder()

    assert "Kharr-Vel" in text
    assert "Breath-Chants" not in text


def test_a_registry_with_only_stubs_adds_nothing_rather_than_noise():
    reg, _ = build(with_profile=False, stub_too=True)
    text = package(reg).for_decoder()

    assert "NAMING CONVENTIONS" not in text


def test_no_linguistic_profile_is_not_an_error():
    reg = DNARegistry()
    reg.register_element("world", "W{}", "A world.", name="Skarn")

    assert "NAMING CONVENTIONS" not in package(reg).for_decoder()


def test_the_idioms_section_is_not_carried():
    """Only what is needed to name things; the rest is budget spent for nothing."""
    reg, _ = build()
    text = package(reg).for_decoder()

    assert "salt on the seal" not in text


def test_conventions_are_not_duplicated_into_the_frame():
    reg, _ = build()
    text = package(reg).for_decoder()

    assert text.count("NAMING CONVENTIONS") == 1


def test_the_canon_slice_carries_them_too():
    """
    Deliberate. The conventions ride in the world frame, which the audit slice
    includes, and that is the right outcome: how this world forms names is a
    fact about the world, so a page whose names contradict it is a genuine
    inconsistency. The header is worded as canon rather than as an instruction
    so it reads correctly in both places.
    """
    reg, _ = build()
    slice_text = package(reg).canon_slice()

    assert "NAMING CONVENTIONS" in slice_text
    assert "Names in this world are formed by these rules" in slice_text
