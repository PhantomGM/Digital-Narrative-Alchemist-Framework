"""
Regression tests for relationship direction.

Registry edge semantics: link_elements(A, B, "parent") means A is the parent
OF B, stored as edges[A]["parent"]=[B] and edges[B]["child"]=[A]. So for any
entity X, get_link_ids(X)["parent"] returns X's CHILDREN and
get_link_ids(X)["child"] returns X's PARENTS.

These tests pin the two consumers that previously read the edges backwards:
InheritanceEngine.compile_constraints and ObsidianSync._format_note.
"""

import sys
import os
import re
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.inheritance import InheritanceEngine
from layer5_dna_substrate.obsidian_sync import ObsidianSync


def build_pair():
    """Region 'Cindermarch' is the parent of settlement 'Blackspire Keep'."""
    reg = DNARegistry()
    region = reg.register_element("region", "DNA_R", "The burned lands.", name="Cindermarch",
                                  gist="A region of ash.")
    settlement = reg.register_element("settlement", "DNA_S", "A soot-stained town.", name="Blackspire Keep",
                                      gist="Fortress town in Cindermarch.")
    reg.link_elements(region, settlement, "parent")  # no label: the default-label case
    return reg, region, settlement


def _section(text: str, heading: str) -> str:
    """Returns the constraint-block section under `heading` (up to the next '->')."""
    match = re.search(re.escape(heading) + r"(.*?)(?=\n  ->|\Z)", text, re.DOTALL)
    return match.group(1) if match else ""


def test_inheritance_constraints_direction():
    reg, region, settlement = build_pair()
    engine = InheritanceEngine(reg)

    # From the settlement's point of view, Cindermarch is a PARENT
    constraints = engine.compile_constraints([settlement])
    parent_section = _section(constraints, "Inheriting from PARENT Entities:")
    child_section = _section(constraints, "Must incorporate lore from CHILD Entities:")
    assert "Cindermarch" in parent_section
    assert "Cindermarch" not in child_section

    # From the region's point of view, Blackspire Keep is a CHILD
    constraints = engine.compile_constraints([region])
    parent_section = _section(constraints, "Inheriting from PARENT Entities:")
    child_section = _section(constraints, "Must incorporate lore from CHILD Entities:")
    assert "Blackspire Keep" in child_section
    assert "Blackspire Keep" not in parent_section
    print("✓ test_inheritance_constraints_direction passed")


def test_obsidian_sync_relations_direction():
    reg, region, settlement = build_pair()
    out_dir = tempfile.mkdtemp(prefix="test_sync_")
    try:
        sync = ObsidianSync(reg, out_dir)
        sync.sync()

        atlas = os.path.join(out_dir, "Atlas")
        with open(os.path.join(atlas, "Blackspire Keep.md"), encoding="utf-8") as f:
            settlement_note = f.read()
        with open(os.path.join(atlas, "Cindermarch.md"), encoding="utf-8") as f:
            region_note = f.read()

        # The settlement's container renders as its Parent, not its Child
        assert "- **Parent**: [[Cindermarch]]" in settlement_note
        assert "- **Child**: [[Cindermarch]]" not in settlement_note

        # The region's settlement renders as its Child, not its Parent
        assert "- **Child**: [[Blackspire Keep]]" in region_note
        assert "- **Parent**: [[Blackspire Keep]]" not in region_note
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    print("✓ test_obsidian_sync_relations_direction passed")


def test_obsidian_sync_inverts_containment_labels():
    """A custom label written from the source's view must not read backwards on the target."""
    reg = DNARegistry()
    world = reg.register_element("world", "DNA_W", "The world.", name="Skarn", gist="g")
    region = reg.register_element("region", "DNA_R", "A region.", name="The Verdant Scars", gist="g")
    reg.link_elements(world, region, "parent", "contains")   # Skarn contains the region

    out_dir = tempfile.mkdtemp(prefix="test_sync_inv_")
    try:
        ObsidianSync(reg, out_dir).sync()
        with open(os.path.join(out_dir, "Atlas", "The Verdant Scars.md"), encoding="utf-8") as f:
            region_note = f.read()
        with open(os.path.join(out_dir, "Cosmology", "Skarn.md"), encoding="utf-8") as f:
            world_note = f.read()

        # On the region's page the world is its container, not its contents
        assert "- **Within**: [[Skarn]]" in region_note
        assert "- **Contains**: [[Skarn]]" not in region_note
        # On the world's page the label reads correctly as written
        assert "- **Contains**: [[The Verdant Scars]]" in world_note
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    print("✓ test_obsidian_sync_inverts_containment_labels passed")


def test_obsidian_sync_custom_labels_untouched():
    reg = DNARegistry()
    a = reg.register_element("faction", "DNA_A", "A guild.", name="Iron Guild", gist="g")
    b = reg.register_element("npc", "DNA_B", "A smith.", name="Kael", gist="g")
    reg.link_elements(a, b, "parent", label="employs")
    out_dir = tempfile.mkdtemp(prefix="test_sync_lbl_")
    try:
        sync = ObsidianSync(reg, out_dir)
        sync.sync()
        with open(os.path.join(out_dir, "Factions", "Iron Guild.md"), encoding="utf-8") as f:
            note = f.read()
        assert "- **Employs**: [[Kael]]" in note  # custom labels render as before
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    print("✓ test_obsidian_sync_custom_labels_untouched passed")


if __name__ == "__main__":
    test_inheritance_constraints_direction()
    test_obsidian_sync_relations_direction()
    test_obsidian_sync_custom_labels_untouched()
    print("\nAll relationship-direction tests passed.")
