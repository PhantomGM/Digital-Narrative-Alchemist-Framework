"""
Tests for the Atlas subfolder taxonomy and the stray-page guard.

Eight spatial types shared one Atlas folder, which put a tavern (establishment)
and a continent (realm) side by side. Each now files into its own subfolder.

Changing TYPE_FOLDER_MAP is exactly the operation that could corrupt a vault:
the sync checks for an existing page only at the mapped path, so a remap would
have found nothing at the new location and written a fresh copy — leaving two
pages for one entity, and where the old one was canon, a canon page and a draft
of the same thing. Hence _find_page_elsewhere.
"""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.obsidian_sync import ObsidianSync  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

ATLAS_TYPES = {"realm", "region", "settlement", "location", "regional_poi",
               "establishment", "wonder", "travel"}


# --- the taxonomy -----------------------------------------------------------

def test_every_spatial_type_has_its_own_subfolder():
    folders = {t: ObsidianSync.TYPE_FOLDER_MAP[t] for t in ATLAS_TYPES}
    assert len(set(folders.values())) == len(ATLAS_TYPES), \
        f"two types share a folder: {folders}"


def test_all_spatial_types_stay_under_atlas():
    for t in ATLAS_TYPES:
        assert ObsidianSync.TYPE_FOLDER_MAP[t].startswith("Atlas/"), t


def test_no_type_maps_to_the_bare_atlas_folder():
    """The root is for the hub; content belongs in a subfolder."""
    assert "Atlas" not in ObsidianSync.TYPE_FOLDER_MAP.values()


def test_non_spatial_types_are_untouched():
    """The reorganisation must not have moved anything else."""
    assert ObsidianSync.TYPE_FOLDER_MAP["npc"] == "Characters"
    assert ObsidianSync.TYPE_FOLDER_MAP["faction"] == "Factions"
    assert ObsidianSync.TYPE_FOLDER_MAP["lore"] == "Lore"
    assert ObsidianSync.TYPE_FOLDER_MAP["text"] == "Lore"
    assert ObsidianSync.TYPE_FOLDER_MAP["creature"] == "Bestiary"


# --- nested paths -----------------------------------------------------------

def write_page(root, relpath, status="draft", ptype="location"):
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        f"---\ntype: {ptype}\nstatus: {status}\ncreated: 2026-01-01\n"
        f"updated: 2026-01-01\ntags:\n  - x\n---\n\n# Page\n\nBody.\n")
    return path


@pytest.fixture
def synced(tmp_path):
    registry = DNARegistry()
    registry.register_element("location", "LOC{}", "### **Deep Vault**\n\nA place.",
                              name="Deep Vault", tags=["expanded"])
    return registry, str(tmp_path)


def test_sync_creates_nested_directories(synced):
    registry, vault = synced
    ObsidianSync(registry, vault).sync()
    assert os.path.isfile(os.path.join(vault, "Atlas", "Locations", "Deep Vault.md"))


# --- the stray-page guard ---------------------------------------------------

def test_a_page_at_the_old_path_is_not_duplicated(synced):
    """The remap case: the page still sits in the bare Atlas folder."""
    registry, vault = synced
    write_page(vault, os.path.join("Atlas", "Deep Vault.md"))

    counts = ObsidianSync(registry, vault).sync()

    assert not os.path.exists(os.path.join(vault, "Atlas", "Locations", "Deep Vault.md")), \
        "sync wrote a second copy instead of noticing the existing page"
    assert counts.get("skipped_moved") == 1


def test_a_canon_page_at_the_old_path_survives_untouched(synced):
    """The dangerous version: the stray page is canon."""
    registry, vault = synced
    stray = write_page(vault, os.path.join("Atlas", "Deep Vault.md"), status="canon")
    before = io.open(stray, encoding="utf-8").read()

    ObsidianSync(registry, vault).sync()

    assert io.open(stray, encoding="utf-8").read() == before
    assert not os.path.exists(os.path.join(vault, "Atlas", "Locations", "Deep Vault.md"))


def test_the_guard_reports_where_the_page_actually_is(synced, capsys):
    registry, vault = synced
    write_page(vault, os.path.join("Atlas", "Deep Vault.md"))
    ObsidianSync(registry, vault).sync()

    out = capsys.readouterr().out
    assert "already at another path" in out
    assert "Deep Vault.md" in out


def test_a_page_at_the_correct_path_is_updated_normally(synced):
    """The guard must not block the ordinary case."""
    registry, vault = synced
    correct = write_page(vault, os.path.join("Atlas", "Locations", "Deep Vault.md"))
    before = io.open(correct, encoding="utf-8").read()

    counts = ObsidianSync(registry, vault).sync()

    assert counts["written"] == 1
    assert io.open(correct, encoding="utf-8").read() != before
    assert not counts.get("skipped_moved")


def test_hidden_directories_are_not_searched(synced):
    """A copy inside .obsidian or .trash must not count as the page."""
    registry, vault = synced
    write_page(vault, os.path.join(".trash", "Deep Vault.md"))

    counts = ObsidianSync(registry, vault).sync()

    assert counts["written"] == 1
    assert os.path.isfile(os.path.join(vault, "Atlas", "Locations", "Deep Vault.md"))
