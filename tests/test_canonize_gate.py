"""
Unit tests for the CanonizeGate loop and the canon-respecting ObsidianSync.
"""

import asyncio
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.context_assembler import ContextAssembler
from layer5_dna_substrate.canonize_gate import CanonizeGate
from layer5_dna_substrate.obsidian_sync import ObsidianSync
from layer5_dna_substrate.phenotype_meta import split_phenotype_tail

TAIL = "```yaml\nname: Warden Hesk\ngist: A compromised gate warden.\nsummary: Owes the Choir.\nstubs: []\n```"
PROFILE = f"### **Warden Hesk**\n\nHesk guards the gate. The gods answer his prayers nightly.\n\n{TAIL}\n"


class FakeAuditor:
    """Plays back a scripted list of audit results; patch replaces the offending sentence."""
    def __init__(self, script):
        self.script = list(script)
        self.audit_calls = 0
        self.patch_calls = 0

    async def audit(self, passage, current_state, fail_open=True):
        self.audit_calls += 1
        result = self.script.pop(0)
        if callable(result):
            return result()
        return result

    async def patch(self, prose, audit_result, current_state=None):
        self.patch_calls += 1
        return prose.replace(audit_result["offending_text"], "The gods are silent, as they have always been.")


def make_gate(auditor):
    reg = DNARegistry()
    npc = reg.register_element("npc", "DNA_N", PROFILE, name="Warden Hesk",
                               gist="A compromised gate warden.")
    gate = CanonizeGate(reg, ContextAssembler(reg, vault=None), auditor)
    return reg, npc, gate


VALID = {"status": "valid", "correction_note": "", "offending_text": ""}
INVALID = {"status": "invalid",
           "correction_note": "The gods are dead; they cannot answer prayers.",
           "offending_text": "The gods answer his prayers nightly."}


def test_consistent_first_pass():
    reg, npc, gate = make_gate(FakeAuditor([VALID]))
    report = asyncio.run(gate.review_entity(npc))
    assert report["status"] == "consistent"
    assert reg.get_element(npc)["audit"]["status"] == "consistent"
    assert reg.get_element(npc)["phenotype"] == PROFILE  # untouched
    print("✓ test_consistent_first_pass passed")


def test_patched_preserves_tail():
    auditor = FakeAuditor([INVALID, VALID])
    reg, npc, gate = make_gate(auditor)
    report = asyncio.run(gate.review_entity(npc))

    assert report["status"] == "patched"
    assert auditor.patch_calls == 1
    phenotype = reg.get_element(npc)["phenotype"]
    assert "The gods are silent" in phenotype           # patch applied
    assert "answer his prayers" not in phenotype        # contradiction gone
    prose, tail = split_phenotype_tail(phenotype)
    assert tail == TAIL                                 # tail reattached untouched
    print("✓ test_patched_preserves_tail passed")


def test_flagged_after_max_rounds_keeps_original():
    auditor = FakeAuditor([INVALID, INVALID, INVALID])
    reg, npc, gate = make_gate(auditor)
    report = asyncio.run(gate.review_entity(npc))

    assert report["status"] == "flagged"
    assert "still inconsistent after 3 audit rounds" in report["notes"][-1]
    assert reg.get_element(npc)["phenotype"] == PROFILE  # flagged: original kept
    print("✓ test_flagged_after_max_rounds_keeps_original passed")


def test_flagged_when_no_offending_sentence():
    vague = {"status": "invalid", "correction_note": "Something is off.", "offending_text": ""}
    auditor = FakeAuditor([vague])
    reg, npc, gate = make_gate(auditor)
    report = asyncio.run(gate.review_entity(npc))
    assert report["status"] == "flagged"
    assert auditor.patch_calls == 0                      # nothing to patch surgically
    print("✓ test_flagged_when_no_offending_sentence passed")


def test_unreviewed_on_audit_error():
    error = {"status": "error", "correction_note": "boom", "offending_text": ""}
    reg, npc, gate = make_gate(FakeAuditor([error]))
    report = asyncio.run(gate.review_entity(npc))
    assert report["status"] == "unreviewed"
    assert reg.get_element(npc)["phenotype"] == PROFILE
    print("✓ test_unreviewed_on_audit_error passed")


def test_flagged_when_patch_emits_ooc_note():
    class OOCPatchAuditor(FakeAuditor):
        async def patch(self, prose, audit_result, current_state=None):
            self.patch_calls += 1
            return prose + "\n\n[OOC System Message - Logic Contradiction]: could not fix"

    reg, npc, gate = make_gate(OOCPatchAuditor([INVALID]))
    report = asyncio.run(gate.review_entity(npc))
    assert report["status"] == "flagged"
    assert "[OOC System Message" not in reg.get_element(npc)["phenotype"]
    print("✓ test_flagged_when_patch_emits_ooc_note passed")


def test_review_all_skips_stubs_and_passed():
    auditor = FakeAuditor([VALID, VALID])
    reg = DNARegistry()
    npc_a = reg.register_element("npc", "DNA_A", PROFILE, name="A")
    npc_b = reg.register_element("npc", "DNA_B", PROFILE, name="B")
    reg.register_element("npc", "STUB", "[STUB] C", name="C", tags=["stub"])
    gate = CanonizeGate(reg, ContextAssembler(reg, vault=None), auditor)

    reports = asyncio.run(gate.review_all())
    assert len(reports) == 2                             # stub skipped
    assert auditor.audit_calls == 2

    # Second run: both already passed, nothing re-audited without force
    reports = asyncio.run(gate.review_all())
    assert reports == []
    print("✓ test_review_all_skips_stubs_and_passed passed")


# ── ObsidianSync canon protection ────────────────────────────

def build_sync_registry():
    reg = DNARegistry()
    npc = reg.register_element("npc", "DNA_N", PROFILE, name="Warden Hesk",
                               gist="A compromised gate warden.")
    reg._records[npc]["audit"] = {"status": "patched"}
    chron = reg.register_element("chronicle", "DNA_C", "### The Sundering\n\nThe world broke.",
                                 name="The Sundering", gist="The world-breaking event.")
    reg.register_element("npc", "STUB", "[STUB] Nobody", name="Nobody", tags=["stub"])
    return reg, npc, chron


def test_sync_writes_drafts_with_vault_conventions():
    reg, npc, chron = build_sync_registry()
    out = tempfile.mkdtemp(prefix="test_gate_sync_")
    try:
        counts = ObsidianSync(reg, out).sync()
        assert counts == {"written": 2, "skipped_protected": 0, "skipped_stubs": 1}

        npc_path = os.path.join(out, "Characters", "Warden Hesk.md")   # npc -> Characters
        chron_path = os.path.join(out, "History", "The Sundering.md")  # chronicle -> History
        assert os.path.isfile(npc_path) and os.path.isfile(chron_path)

        with open(npc_path, encoding="utf-8") as f:
            note = f.read()
        assert "status: draft" in note
        assert "audit: patched" in note
        assert "created: " in note and "updated: " in note
        assert "dna-generated" in note
        assert "```yaml" not in note                      # tail stripped from the note body
        assert "*A compromised gate warden.*" in note     # gist under the title
    finally:
        shutil.rmtree(out, ignore_errors=True)
    print("✓ test_sync_writes_drafts_with_vault_conventions passed")


def test_sync_files_lore_and_culture_in_their_own_folders():
    """A doctrine belongs in Lore/, a people in Cultures/ — not lumped elsewhere."""
    reg = DNARegistry()
    reg.register_element("lore", "DNA_L", "### The Creed\n\nWhat they believe.",
                         name="The First Truth", gist="The Orthodoxy's central doctrine.")
    reg.register_element("culture", "DNA_C", "### A People\n\nHow they live.",
                         name="The Soot-Walkers", gist="Masked scavengers.")
    reg.register_element("linguistic", "DNA_T", "### A Tongue\n\nHow they speak.",
                         name="Cinder Tongue", gist="A language.")

    out = tempfile.mkdtemp(prefix="test_lore_sync_")
    try:
        ObsidianSync(reg, out).sync()
        assert os.path.isfile(os.path.join(out, "Lore", "The First Truth.md"))
        assert os.path.isfile(os.path.join(out, "Cultures", "The Soot-Walkers.md"))
        # Languages still belong with the peoples who speak them
        assert os.path.isfile(os.path.join(out, "Cultures", "Cinder Tongue.md"))
        # Creatures file into the Bestiary
        reg.register_element("creature", "DNA_B", "### A Beast\n\nIt hunts.",
                             name="Dust-Wraith", gist="Animated ash.")
        ObsidianSync(reg, out).sync()
        assert os.path.isfile(os.path.join(out, "Bestiary", "Dust-Wraith.md"))
        # And nothing landed in the catch-all
        assert not os.path.isdir(os.path.join(out, "Drafts"))
    finally:
        shutil.rmtree(out, ignore_errors=True)
    print("✓ test_sync_files_lore_and_culture_in_their_own_folders passed")


def test_sync_never_overwrites_canon():
    reg, npc, chron = build_sync_registry()
    out = tempfile.mkdtemp(prefix="test_gate_canon_")
    try:
        canon_dir = os.path.join(out, "Characters")
        os.makedirs(canon_dir)
        canon_text = "---\ntype: character\nstatus: canon\ncreated: 2026-01-01\n---\n\n# Warden Hesk\n\nThe author's own words.\n"
        canon_path = os.path.join(canon_dir, "Warden Hesk.md")
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(canon_text)

        counts = ObsidianSync(reg, out).sync()
        assert counts["skipped_protected"] == 1
        with open(canon_path, encoding="utf-8") as f:
            assert f.read() == canon_text                 # byte-for-byte untouched
    finally:
        shutil.rmtree(out, ignore_errors=True)
    print("✓ test_sync_never_overwrites_canon passed")


def test_sync_overwrites_draft_but_keeps_created_date():
    reg, npc, chron = build_sync_registry()
    out = tempfile.mkdtemp(prefix="test_gate_draft_")
    try:
        draft_dir = os.path.join(out, "Characters")
        os.makedirs(draft_dir)
        draft_path = os.path.join(draft_dir, "Warden Hesk.md")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write("---\ntype: character\nstatus: draft\ncreated: 2026-01-01\n---\n\n# Old draft\n")

        ObsidianSync(reg, out).sync()
        with open(draft_path, encoding="utf-8") as f:
            note = f.read()
        assert "Old draft" not in note                    # draft refreshed
        assert "created: 2026-01-01" in note              # original created date kept
    finally:
        shutil.rmtree(out, ignore_errors=True)
    print("✓ test_sync_overwrites_draft_but_keeps_created_date passed")


if __name__ == "__main__":
    test_consistent_first_pass()
    test_patched_preserves_tail()
    test_flagged_after_max_rounds_keeps_original()
    test_flagged_when_no_offending_sentence()
    test_unreviewed_on_audit_error()
    test_flagged_when_patch_emits_ooc_note()
    test_review_all_skips_stubs_and_passed()
    test_sync_writes_drafts_with_vault_conventions()
    test_sync_never_overwrites_canon()
    test_sync_overwrites_draft_but_keeps_created_date()
    print("\nAll canonize gate tests passed.")
