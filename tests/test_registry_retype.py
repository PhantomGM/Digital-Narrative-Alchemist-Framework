"""
Tests for DNARegistry.retype_element and deterministic persistence.

Retyping exists because a stub's type is guessed by fuzzy-matching the label a
decoder wrote ("[Chronicle] The Divine Breath"), so entities regularly land under
the wrong type and need correcting once a better type exists. It is not
cosmetic: ObsidianSync files pages by type, so a retype changes where a page is
written — which is why canonized entities are refused by default.

The persistence test guards a churn bug: the tag index holds sets, and
serialising them unsorted made every save rewrite most of the file, so a
three-field change produced a 128-line diff of shuffled ids.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.registry import DNARegistry  # noqa: E402


@pytest.fixture
def registry():
    reg = DNARegistry()
    reg.register_element("chronicle", "DNA{}", "body", name="The Divine Breath",
                         tags=["stub", "belief"])
    reg.register_element("chronicle", "DNA{}", "body", name="The Collapse",
                         tags=["canonized", "event"])
    return reg


def uid_of(registry, name):
    return registry.find_by_name(name)["id"]


# --- retyping ---------------------------------------------------------------

def test_retype_changes_the_type(registry):
    entity_id = uid_of(registry, "The Divine Breath")
    registry.retype_element(entity_id, "lore")
    assert registry.get_element(entity_id)["type"] == "lore"


def test_retype_returns_the_previous_type(registry):
    entity_id = uid_of(registry, "The Divine Breath")
    assert registry.retype_element(entity_id, "lore") == "chronicle"


def test_retype_to_the_same_type_is_a_no_op(registry):
    entity_id = uid_of(registry, "The Divine Breath")
    assert registry.retype_element(entity_id, "chronicle") == "chronicle"
    assert registry.get_element(entity_id)["type"] == "chronicle"


def test_retype_normalizes_case_and_whitespace(registry):
    entity_id = uid_of(registry, "The Divine Breath")
    registry.retype_element(entity_id, "  LORE  ")
    assert registry.get_element(entity_id)["type"] == "lore"


def test_retype_keeps_everything_else_intact(registry):
    entity_id = uid_of(registry, "The Divine Breath")
    before = dict(registry.get_element(entity_id))
    registry.retype_element(entity_id, "lore")
    after = registry.get_element(entity_id)
    for key in ("id", "name", "dna", "phenotype", "tags"):
        assert after[key] == before[key]


def test_retype_is_findable_by_the_new_type(registry):
    registry.retype_element(uid_of(registry, "The Divine Breath"), "lore")
    assert [r["name"] for r in registry.get_all_by_type("lore")] == ["The Divine Breath"]
    assert "The Divine Breath" not in [
        r["name"] for r in registry.get_all_by_type("chronicle")]


# --- guards -----------------------------------------------------------------

def test_unknown_id_raises(registry):
    with pytest.raises(KeyError):
        registry.retype_element("no-such-id", "lore")


@pytest.mark.parametrize("bad", ["", "   ", None, 5, ["lore"]])
def test_invalid_new_type_raises(registry, bad):
    entity_id = uid_of(registry, "The Divine Breath")
    with pytest.raises(ValueError):
        registry.retype_element(entity_id, bad)


def test_canonized_entity_is_refused_by_default(registry):
    """
    Its page is already canon and sync will not overwrite it, so retyping would
    leave the canon page orphaned in the old folder.
    """
    entity_id = uid_of(registry, "The Collapse")
    with pytest.raises(ValueError, match="canonized"):
        registry.retype_element(entity_id, "lore")
    assert registry.get_element(entity_id)["type"] == "chronicle"


def test_canonized_entity_can_be_retyped_with_force(registry):
    entity_id = uid_of(registry, "The Collapse")
    assert registry.retype_element(entity_id, "lore", force=True) == "chronicle"
    assert registry.get_element(entity_id)["type"] == "lore"


def test_no_op_on_canonized_does_not_raise(registry):
    """Refusing a change that isn't a change would be noise."""
    entity_id = uid_of(registry, "The Collapse")
    assert registry.retype_element(entity_id, "chronicle") == "chronicle"


# --- persistence ------------------------------------------------------------

def test_retype_survives_a_save_and_load(registry, tmp_path):
    registry.retype_element(uid_of(registry, "The Divine Breath"), "lore")
    path = str(tmp_path / "reg.json")
    registry.save_to_json(path)

    reloaded = DNARegistry()
    reloaded.load_from_json(path)
    assert reloaded.find_by_name("The Divine Breath")["type"] == "lore"


def test_tag_index_is_serialized_sorted(registry, tmp_path):
    path = str(tmp_path / "reg.json")
    registry.save_to_json(path)
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    assert list(data["tag_index"]) == sorted(data["tag_index"])
    for tag, ids in data["tag_index"].items():
        assert ids == sorted(ids), f"tag {tag!r} not sorted"


def test_saves_are_byte_identical_across_processes(registry, tmp_path):
    """
    Set iteration order varies with the per-process hash seed, so identical
    content must be checked in separate interpreters, not just twice in one.
    """
    source = str(tmp_path / "source.json")
    registry.save_to_json(source)

    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    script = (
        "import sys; sys.path.insert(0, sys.argv[3]);"
        "from layer5_dna_substrate.registry import DNARegistry;"
        "r = DNARegistry(); r.load_from_json(sys.argv[1]); r.save_to_json(sys.argv[2])"
    )

    outputs = []
    for index in range(2):
        target = str(tmp_path / f"out{index}.json")
        subprocess.run([sys.executable, "-c", script, source, target, src_dir],
                       check=True, capture_output=True)
        with open(target, "rb") as handle:
            outputs.append(handle.read())

    assert outputs[0] == outputs[1], "save output varies between processes"
