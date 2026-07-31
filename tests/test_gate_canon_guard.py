"""
The gate must audit a canon page but never rewrite it.

Two reasons. Canon prose is the author's, and the vault's own rules reserve it to
them. And mechanically, ObsidianSync refuses to overwrite a canon page — so a
patch applied to the registry would never reach the vault, leaving the registry
claiming "patched" while the page kept text the auditor had judged wrong. A
silent divergence between the two records of the same world is worse than an
unfixed sentence.
"""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.canonize_gate import CanonizeGate  # noqa: E402
from layer5_dna_substrate.context_assembler import ContextAssembler  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

PROSE = "### **A Page**\n\nA sentence the auditor will dislike.\n"


class Auditor:
    """Always finds a fault, and always offers a patch."""

    def __init__(self):
        self.audits = 0
        self.patches = 0

    async def audit(self, prose, world_state, fail_open=False):
        self.audits += 1
        return {"status": "invalid",
                "correction_note": "contradicts a ruling",
                "offending_text": "A sentence the auditor will dislike."}

    async def patch(self, prose, result, current_state=""):
        self.patches += 1
        return "### **A Page**\n\nA sentence the auditor rewrote.\n"


def build(canonized: bool):
    registry = DNARegistry()
    tags = ["expanded"] + (["canonized"] if canonized else [])
    entity_id = registry.register_element("lore", "LORE{}", PROSE, name="A Page", tags=tags)
    auditor = Auditor()
    gate = CanonizeGate(registry, ContextAssembler(registry, None), auditor)
    return registry, gate, auditor, entity_id


def test_canon_page_is_audited(setup=None):
    """The point is to check it, so the audit must still run."""
    registry, gate, auditor, entity_id = build(canonized=True)
    asyncio.run(gate.review_entity(entity_id))
    assert auditor.audits == 1


def test_canon_page_is_never_patched():
    registry, gate, auditor, entity_id = build(canonized=True)
    asyncio.run(gate.review_entity(entity_id))
    assert auditor.patches == 0, "the patcher must not even be called"


def test_canon_prose_is_left_untouched():
    registry, gate, auditor, entity_id = build(canonized=True)
    asyncio.run(gate.review_entity(entity_id))
    assert registry.get_element(entity_id)["phenotype"] == PROSE


def test_canon_page_is_flagged_for_the_author():
    registry, gate, auditor, entity_id = build(canonized=True)
    report = asyncio.run(gate.review_entity(entity_id))
    assert report["status"] == "flagged"
    assert any("author edits canon" in note for note in report["notes"])
    assert any("contradicts a ruling" in note for note in report["notes"])


def test_a_draft_is_still_patched():
    """The guard must not disable the gate's whole purpose for drafts."""

    class Fixable(Auditor):
        """Invalid until the patch lands, then satisfied — the real loop shape."""

        async def audit(self, prose, world_state, fail_open=False):
            self.audits += 1
            if "rewrote" in prose:
                return {"status": "valid"}
            return await super().audit(prose, world_state, fail_open)

    registry = DNARegistry()
    entity_id = registry.register_element(
        "lore", "LORE{}", PROSE, name="A Page", tags=["expanded"])
    auditor = Fixable()
    gate = CanonizeGate(registry, ContextAssembler(registry, None), auditor)

    report = asyncio.run(gate.review_entity(entity_id))
    assert auditor.patches == 1
    assert report["status"] == "patched"
    assert "auditor rewrote" in registry.get_element(entity_id)["phenotype"]


def test_a_clean_canon_page_passes_normally():
    class Clean(Auditor):
        async def audit(self, prose, world_state, fail_open=False):
            self.audits += 1
            return {"status": "valid"}

    registry = DNARegistry()
    entity_id = registry.register_element(
        "lore", "LORE{}", PROSE, name="A Page", tags=["expanded", "canonized"])
    auditor = Clean()
    gate = CanonizeGate(registry, ContextAssembler(registry, None), auditor)

    report = asyncio.run(gate.review_entity(entity_id))
    assert report["status"] == "consistent"
    assert registry.get_element(entity_id)["phenotype"] == PROSE
