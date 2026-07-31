"""
ExpansionManager.expand_stub must forward seed and axis pins to the generator.

Without this, expansion always rolled every axis at random, so an entity canon
already describes got DNA contradicting the established world — the failure that
softened a canon-fast predator into a scavenger earlier in this project. The
decoder is told canon outranks the DNA, but it is better not to hand it a
conflict at all: pin what canon states and let the rest vary.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.expansion_manager import ExpansionManager  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402


class RecordingForge:
    """Stands in for ProceduralForge, capturing what it was asked for."""

    def __init__(self):
        self.calls = []

    def synthesize_element(self, element_type, constraint_package="", **gen_kwargs):
        self.calls.append({"type": element_type, "kwargs": gen_kwargs})
        return {"type": element_type, "dna": f"{element_type.upper()}{{v1.0[1/1/1]}}",
                "constraints": constraint_package}


class StubDecoder:
    def decode_element(self, dna_data, context=None):
        return "### **A Page**\n\nBody text.\n"


class NullInheritance:
    def compile_constraints(self, parent_ids):
        return ""


@pytest.fixture
def setup():
    registry = DNARegistry()
    source_id = registry.register_element(
        "lore", "LORE{}", "source body", name="The First Truth", tags=["canonized"])
    stub_id = registry.register_element(
        "text", "", "", name=None, tags=["stub"])
    registry.get_element(stub_id)["stub_metadata"] = {
        "name": "The Litany", "description": "A sacred text.", "source_id": source_id,
    }
    forge = RecordingForge()
    manager = ExpansionManager(registry, forge, NullInheritance(), StubDecoder())
    return registry, forge, manager, stub_id


def test_pins_reach_the_generator(setup):
    registry, forge, manager, stub_id = setup
    manager.expand_stub(stub_id, legibility=2, attrib="unknown", copies=8)

    assert forge.calls[0]["type"] == "text"
    assert forge.calls[0]["kwargs"] == {
        "legibility": 2, "attrib": "unknown", "copies": 8}


def test_seed_reaches_the_generator(setup):
    registry, forge, manager, stub_id = setup
    manager.expand_stub(stub_id, seed=312)
    assert forge.calls[0]["kwargs"] == {"seed": 312}


def test_no_pins_means_no_kwargs(setup):
    """Unpinned expansion must stay fully random, as before."""
    registry, forge, manager, stub_id = setup
    manager.expand_stub(stub_id)
    assert forge.calls[0]["kwargs"] == {}


def test_extra_context_is_not_passed_as_a_pin(setup):
    """
    extra_context is a decoder directive, not a genome axis; leaking it into
    gen_kwargs would make the generator reject the call.
    """
    registry, forge, manager, stub_id = setup
    manager.expand_stub(stub_id, extra_context="Treat this as a document.",
                        legibility=2)
    assert forge.calls[0]["kwargs"] == {"legibility": 2}


def test_expansion_still_updates_the_record(setup):
    """The pin passthrough must not disturb the rest of expansion."""
    registry, forge, manager, stub_id = setup
    manager.expand_stub(stub_id, legibility=2)

    record = registry.get_element(stub_id)
    assert "stub" not in record["tags"]
    assert "expanded" in record["tags"]
    assert record["phenotype"].startswith("### **A Page**")
    assert record["dna"] == "TEXT{v1.0[1/1/1]}"


def test_name_fallback_works_at_all(setup):
    """
    _extract_name raised PatternError for every input: its first pattern wrote
    \\\\[? — an escaped backslash then a class-opening "[" — which swallowed the
    capture group's "(" and left the trailing ")" unbalanced. The whole fallback
    was dead, so expansion crashed rather than degrading whenever a decoder
    omitted the structured tail. This exercises exactly that path, since the
    stub decoder here emits no tail.
    """
    _, _, manager, _ = setup
    assert manager._extract_name("### **A Page**\n\nBody.") == "A Page"
    assert manager._extract_name("### **[The Litany]**\n\nBody.") == "The Litany"
    assert manager._extract_name("## Plain Heading\n\nBody.") == "Plain Heading"


def test_sync_shares_the_repaired_pattern():
    """ObsidianSync carried an identical broken copy in its own name extraction."""
    import re

    from layer5_dna_substrate.obsidian_sync import ObsidianSync
    source = __import__("inspect").getsource(ObsidianSync)
    for literal in re.findall(r'r"(###[^"]*)"', source):
        re.compile(literal)  # must not raise


def test_non_stub_is_rejected(setup):
    registry, forge, manager, stub_id = setup
    manager.expand_stub(stub_id, legibility=2)
    with pytest.raises(ValueError):
        manager.expand_stub(stub_id, legibility=2)  # no longer a stub
