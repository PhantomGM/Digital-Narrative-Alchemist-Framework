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
        # Draft by default: a freshly generated profile is not canon until the
        # author promotes it, and that is the state most of these test.
        reg.register_element("linguistic", "LING{}", PROFILE,
                             name="Throat-Speak Resonance", tags=["expanded"],
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


def test_a_draft_profile_still_steers_generation():
    """
    Waiting for canonization would mean every page generated in the meantime
    uses the model's default names — the exact problem this fixes.
    """
    reg, _ = build()          # registered without the 'canonized' tag
    text = package(reg).for_decoder()

    assert "Kharr-Vel" in text
    assert "draft, not yet approved as canon" in text


def test_a_draft_profile_is_kept_out_of_the_audit_baseline():
    """
    The slice is what canon pages are judged against. An unapproved proposal in
    it would let a draft generate contradictions in approved canon — the exact
    boundary the canon model exists to hold.
    """
    reg, _ = build()
    pkg = package(reg)

    assert "[LANGUAGE" in pkg.for_decoder()
    assert "[LANGUAGE" not in pkg.canon_slice()
    assert pkg.naming_is_canon is False


def test_a_canonized_profile_is_marked_canon_and_enters_the_slice():
    reg, world = build(with_profile=False)
    reg.register_element("linguistic", "LING{}", PROFILE,
                         name="Throat-Speak Resonance", tags=["canonized"])
    pkg = package(reg)

    assert pkg.naming_is_canon is True
    assert "LANGUAGE - canon" in pkg.for_decoder()
    assert "Kharr-Vel" in pkg.canon_slice()


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

    assert "[LANGUAGE" not in text


def test_no_linguistic_profile_is_not_an_error():
    reg = DNARegistry()
    reg.register_element("world", "W{}", "A world.", name="Skarn")

    assert "[LANGUAGE" not in package(reg).for_decoder()


def test_idioms_and_taboos_are_carried_too():
    """
    Naming alone was too little. A live run confirmed no idiom or taboo reached
    any of five decodes, because only the Naming Conventions section was
    extracted — and Skarn's taboo against speaking the pre-Collapse architects'
    names is the in-world reason nobody can identify them, which is a
    canon-safety rule, not flavour.
    """
    reg, _ = build()
    text = package(reg).for_decoder()

    assert "salt on the seal" in text


def test_phonetics_and_register_are_still_left_out():
    """
    The naming rules and idioms demonstrate the sound concretely; an abstract
    description of it costs budget that locale and lineage use better.
    """
    reg, _ = build()

    assert "guttural stops" not in package(reg).naming


def test_conventions_are_not_duplicated_into_the_frame():
    reg, _ = build()
    text = package(reg).for_decoder()

    assert text.count("[LANGUAGE") == 1


def test_conventions_are_not_capped_away():
    """
    They are held outside world_frame precisely so the budget cannot reach them;
    inside it they sat behind a World Overview that already overflows the cap.
    """
    reg, _ = build()
    pkg = package(reg, budget=40)

    assert pkg.world_frame == "" or len(pkg.naming) > len(pkg.world_frame)
    assert "doubled consonant" in pkg.naming


def test_a_taboo_is_never_delivered_half_finished():
    """
    Skarn's profile needed 3037 chars and the cap was 3000, which cut its last
    taboo mid-sentence. That is worse than dropping it: the surviving half reads
    as the prohibition and the severed half named the euphemisms that satisfy
    it, so the decoder got the rule without the way to obey it.
    """
    long_profile = PROFILE.replace(
        '* Sayings: "salt on the seal" means a bargain nobody intends to keep.',
        '* Sayings: "salt on the seal" means a bargain nobody intends to keep.\n'
        + "* Filler line to push the section past the old ceiling.\n" * 40
        + '* Taboo: the drowned king\'s name is never spoken; say "the Wet Crown".')
    reg = DNARegistry()
    reg.register_element("world", "W{}", "A hard world.", name="Skarn")
    reg.register_element("linguistic", "LING{}", long_profile,
                         name="Throat-Speak Resonance", tags=["canonized"])
    naming = package(reg).naming

    for line in naming.splitlines():
        assert line == "" or line in long_profile or line.startswith("[LANGUAGE") \
            or line.startswith("("), f"partial line delivered: {line[-40:]!r}"


def test_over_budget_drops_sayings_before_taboos():
    """
    A taboo is a canon-safety rule; a saying is flavour. When the profile will
    not fit, the flavour goes and the rule stays -- and both go whole.
    """
    from layer5_dna_substrate.context_assembler import _fit_language_block

    section = ("**Naming Conventions:**\n"
               "*   **NPC Names:** " + "n" * 300 + "\n"
               "*   **Sayings:** " + "s" * 300 + "\n"
               "*   **Linguistic Taboos:** " + "t" * 300 + "\n")
    fitted = _fit_language_block(section, 700)

    assert "Linguistic Taboos" in fitted, "the canon-safety rule must survive"
    assert "NPC Names" in fitted
    assert "Sayings" not in fitted, "flavour is dropped first"
    assert "s" * 300 not in fitted


def test_a_profile_that_fits_is_untouched():
    from layer5_dna_substrate.context_assembler import _fit_language_block

    section = "**Naming Conventions:**\n*   **NPC Names:** short\n"

    assert _fit_language_block(section, 4000) == section


def test_the_example_names_are_marked_as_illustrative():
    """
    A text decode adopted "Scribe Veris Thal" -- one of the profile's worked
    example names -- as an actual forger in Skarn's history. The examples are
    stylistically perfect, which is exactly why they get taken as a name pool;
    left unlabelled they would recur across every generation and become their
    own convergence.
    """
    reg, _ = build()
    naming = package(reg).naming

    assert "demonstrate the RULES" in naming
    assert "do not reuse the examples themselves" in naming
