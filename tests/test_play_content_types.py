"""
Tests for the play-content types: trap and quest.

`trap` had a generator and a decoder but was missing from VALID_STUB_TYPES, the
fuzzy map and TYPE_FOLDER_MAP. The folder gap merely misfiled pages; the type gap
was worse. _resolve_stub_type falls back to "npc" for anything it does not
recognise, so every "[Trap] ..." stub a decoder wrote was silently registered as
a person and filed under Characters — the same failure that once turned
Moss-Hulks and Thorn-Stalkers into NPCs.

Both types are play material rather than world facts, so they file under
Encounters/ rather than into a folder that answers "what is true about the world".
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402
from layer5_dna_substrate.expansion_manager import (  # noqa: E402
    ExpansionManager, _resolve_stub_type)
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.obsidian_sync import ObsidianSync  # noqa: E402
from layer5_dna_substrate.phenotype_meta import VALID_STUB_TYPES  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402


# --- the mis-resolution, which was the actual damage -------------------------

@pytest.mark.parametrize("label", ["trap", "snare", "hazard", "pitfall", "deadfall"])
def test_trap_labels_no_longer_resolve_to_npc(label):
    assert _resolve_stub_type(label) == "trap", \
        f"{label!r} still falls through to the npc default"


@pytest.mark.parametrize("label", ["quest", "adventure", "mission", "contract", "errand"])
def test_quest_labels_resolve(label):
    assert _resolve_stub_type(label) == "quest"


def test_a_trap_stub_is_registered_as_a_trap():
    """The end-to-end path a decoder's "[Trap] ..." line actually takes."""
    registry = DNARegistry()
    source = registry.register_element("location", "LOC{}", "body", name="A Vault")
    manager = ExpansionManager(registry, None, None, None)

    stub_id = manager._register_stub(
        source, "Trap", "The Sighing Floor", "A pressure plate that whistles.")

    assert registry.get_element(stub_id)["type"] == "trap"


def test_both_types_are_valid_stub_types():
    assert "trap" in VALID_STUB_TYPES
    assert "quest" in VALID_STUB_TYPES


# --- a home of their own ----------------------------------------------------

def test_neither_type_lands_in_drafts():
    """Drafts is the vault's holding pen for the not-yet-canon, not a home."""
    for t in ("trap", "quest"):
        folder = ObsidianSync.TYPE_FOLDER_MAP.get(t)
        assert folder, f"{t} is missing from TYPE_FOLDER_MAP"
        assert folder != ObsidianSync.DEFAULT_FOLDER
        assert not folder.startswith("Drafts")


def test_play_content_files_under_encounters():
    assert ObsidianSync.TYPE_FOLDER_MAP["trap"] == "Encounters/Traps"
    assert ObsidianSync.TYPE_FOLDER_MAP["quest"] == "Encounters/Quests"


def test_play_content_is_separate_from_world_folders():
    """It must not share a folder with anything that states world fact."""
    world_folders = {v for k, v in ObsidianSync.TYPE_FOLDER_MAP.items()
                     if k not in ("trap", "quest")}
    for t in ("trap", "quest"):
        assert ObsidianSync.TYPE_FOLDER_MAP[t] not in world_folders


@pytest.mark.parametrize("etype,expected", [
    ("trap", os.path.join("Encounters", "Traps")),
    ("quest", os.path.join("Encounters", "Quests")),
])
def test_a_completed_page_is_written_to_its_folder(etype, expected):
    registry = DNARegistry()
    registry.register_element(etype, f"{etype.upper()}{{}}",
                             "### **The Sighing Floor**\n\nA plate.",
                             name="The Sighing Floor", tags=["expanded"])
    out = tempfile.mkdtemp(prefix="play_content_")
    ObsidianSync(registry, out).sync()

    assert os.path.isfile(os.path.join(out, expected, "The Sighing Floor.md"))


# --- the rest of the wiring -------------------------------------------------

def test_both_types_have_a_generator_and_a_decoder():
    forge, decoders = ProceduralForge().generators, DNADecoder().prompts
    for t in ("trap", "quest"):
        assert t in forge, f"{t} has no generator"
        assert t in decoders, f"{t} has no decoder"


def test_existing_labels_were_not_hijacked():
    """
    Fuzzy matching is by substring in insertion order, so new keys can capture
    labels that already resolved elsewhere.
    """
    for label, expected in [("scripture", "lore"), ("scroll", "item"),
                            ("book", "item"), ("text", "text"),
                            ("doctrine", "lore"), ("creature", "creature"),
                            ("codex", "text"), ("location", "location"),
                            ("faction", "faction"), ("culture", "culture")]:
        assert _resolve_stub_type(label) == expected, label
