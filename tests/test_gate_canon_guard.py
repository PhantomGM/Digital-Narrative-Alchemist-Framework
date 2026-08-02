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


def test_a_failed_audit_does_not_erase_a_prior_verdict():
    """
    An audit that never ran is not evidence. Without this, one exhausted API
    quota partway through a re-audit sweep would downgrade every already-passing
    record to "unreviewed" and lose the real result.
    """

    class Broken:
        async def audit(self, prose, world_state, fail_open=False):
            return {"status": "error", "correction_note": "quota exhausted"}

        async def patch(self, prose, result, current_state=""):
            raise AssertionError("must not patch after an audit error")

    registry = DNARegistry()
    entity_id = registry.register_element(
        "lore", "LORE{}", PROSE, name="A Page", tags=["expanded", "canonized"])
    registry.get_element(entity_id)["audit"] = {
        "status": "consistent", "notes": [], "rounds": 1, "reviewed": "2026-07-26"}

    gate = CanonizeGate(registry, ContextAssembler(registry, None), Broken())
    report = asyncio.run(gate.review_entity(entity_id))

    stored = registry.get_element(entity_id)["audit"]
    assert stored["status"] == "consistent", "the real verdict must survive"
    assert stored["reviewed"] == "2026-07-26", "and keep its original date"
    assert any("could not run" in note for note in stored["notes"])
    assert report["kept_prior"] == "consistent"


def test_a_failed_audit_on_a_never_reviewed_entity_is_unreviewed():
    """The guard must not invent a verdict where none existed."""

    class Broken:
        async def audit(self, prose, world_state, fail_open=False):
            return {"status": "error", "correction_note": "quota exhausted"}

    registry = DNARegistry()
    entity_id = registry.register_element(
        "lore", "LORE{}", PROSE, name="A Page", tags=["expanded"])
    gate = CanonizeGate(registry, ContextAssembler(registry, None), Broken())

    report = asyncio.run(gate.review_entity(entity_id))
    assert report["status"] == "unreviewed"
    assert registry.get_element(entity_id)["audit"]["status"] == "unreviewed"


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


def test_already_settled_verdicts_are_not_re_audited():
    """
    'composed' was missing from the skip list, so a plain run re-audited all 38
    composed pages before reaching the one entity that needed it -- 38 model
    calls and about half an hour, which makes the gate too costly to run
    casually. A composed page is assembled from canon rather than invented, so
    it has already been through a path that cannot contradict canon.
    """
    registry = DNARegistry()
    ids = {}
    for verdict in ("consistent", "patched", "composed", "flagged",
                    "unreviewed", None):
        entity_id = registry.register_element(
            "lore", "LORE{}", PROSE, name=f"Page {verdict}", tags=["expanded"])
        if verdict:
            registry.get_element(entity_id)["audit"] = {"status": verdict}
        ids[verdict] = entity_id

    gate = CanonizeGate(registry, ContextAssembler(registry, None), Auditor())
    due = set(gate._reviewable_ids())

    for settled in ("consistent", "patched", "composed"):
        assert ids[settled] not in due, f"{settled} should not be re-audited"
    for pending in ("flagged", "unreviewed", None):
        assert ids[pending] in due, f"{pending} still needs review"

    assert set(gate._reviewable_ids(force=True)) == set(ids.values())
