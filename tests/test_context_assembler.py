"""
Unit tests for VaultAdapter and ContextAssembler, plus their wiring into
DNADecoder.format_context and ExpansionManager.expand_stub.
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.vault_adapter import VaultAdapter
from layer5_dna_substrate.context_assembler import ContextAssembler, AssemblyRequest, ContextPackage
from layer5_dna_substrate.expansion_manager import ExpansionManager


def make_vault(root: str):
    """Builds a minimal world-bible vault in `root`."""
    os.makedirs(os.path.join(root, "History"))
    os.makedirs(os.path.join(root, "Atlas"))

    def write(rel, text):
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(text)

    write("World Overview.md",
          "---\ntype: meta\nstatus: canon\n---\n\n# World Overview\n\n"
          "## Pillars\n\n1. Magic always has a price paid in memory.\n2. The gods are dead.\n")
    write(os.path.join("History", "Timeline.md"),
          "---\ntype: meta\nstatus: draft\n---\n\n# Timeline\n\n"
          "## Calendar\n\nYear zero is the Sundering. 10 months of 36 days.\n\n## Chronology\n\n| a | b |\n")
    write("Index.md",
          "---\ntype: meta\nstatus: canon\n---\n\n# Index\n\n"
          "- [[Blackspire Keep]] - a fortress that remembers its dead (canon)\n"
          "- [[The Ashen Road]] - trade route through the burned lands (draft)\n"
          "- [[Old Fort]] - superseded by Blackspire Keep (deprecated)\n")
    write(os.path.join("Atlas", "Blackspire Keep.md"),
          "---\ntype: location\nstatus: canon\n---\n\n# Blackspire Keep\n\n"
          "A basalt fortress whose walls whisper the names of the fallen.\n")


def with_vault(fn):
    """Runs fn(vault_path) inside a temp vault."""
    root = tempfile.mkdtemp(prefix="test_vault_")
    try:
        make_vault(root)
        fn(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ── VaultAdapter ─────────────────────────────────────────────

def test_vault_adapter_reads_overview_and_calendar():
    def check(root):
        vault = VaultAdapter(root)
        overview = vault.world_overview()
        assert "[CANON - immutable, do not contradict]" in overview
        assert "Magic always has a price" in overview

        calendar = vault.calendar_rules()
        assert "Year zero is the Sundering" in calendar
        assert "[DRAFT" in calendar
        assert "Chronology" not in calendar  # section extraction stops at next heading
    with_vault(check)
    print("✓ test_vault_adapter_reads_overview_and_calendar passed")


def test_vault_adapter_roster_and_excerpt():
    def check(root):
        vault = VaultAdapter(root)
        roster = vault.roster()
        names = {entry["name"]: entry for entry in roster}
        assert names["Blackspire Keep"]["status"] == "canon"
        assert names["The Ashen Road"]["status"] == "draft"
        assert names["Old Fort"]["status"] == "deprecated"

        excerpt = vault.page_excerpt("Blackspire Keep")  # found by name, no path needed
        assert "whisper the names of the fallen" in excerpt
        assert "[CANON" in excerpt
    with_vault(check)
    print("✓ test_vault_adapter_roster_and_excerpt passed")


def test_vault_adapter_missing_vault_degrades():
    vault = VaultAdapter(r"C:\definitely\not\a\vault")
    assert vault.world_overview() == ""
    assert vault.calendar_rules() == ""
    assert vault.roster() == []
    assert vault.page_excerpt("Anything") == ""
    print("✓ test_vault_adapter_missing_vault_degrades passed")


# ── ContextAssembler ─────────────────────────────────────────

def build_registry():
    """Region ⊃ Settlement ⊃ anchor NPC, plus a linguistic profile and a peer."""
    reg = DNARegistry()
    region = reg.register_element("region", "DNA_R", "The burned lands.", name="Cindermarch",
                                  gist="A region of ash and salvage baronies.")
    settlement = reg.register_element("settlement", "DNA_S", "A soot-stained town.", name="Blackspire Keep",
                                      gist="Fortress town that remembers its dead.")
    npc = reg.register_element("npc", "DNA_N", "A tired warden.", name="Warden Hesk",
                               gist="Gate warden who owes the Choir money.",
                               summary="Hesk guards the gate, drinks too much, and is compromised.")
    lang = reg.register_element("linguistic", "DNA_L", "Harsh consonants.", name="Cinder Tongue",
                                gist="Names favor hard consonants and ash-words.")
    peer = reg.register_element("npc", "DNA_P", "A rival.", name="Sable Vey",
                                gist="Smuggler who runs the under-gate.")
    reg.link_elements(region, settlement, "parent", "contains")
    reg.link_elements(settlement, npc, "parent", "home_of")
    reg.link_elements(lang, region, "peer", "spoken_in")
    reg.link_elements(npc, peer, "peer", "rival_of")
    return reg, region, settlement, npc, lang, peer


def test_assembler_layers():
    def check(root):
        reg, region, settlement, npc, lang, peer = build_registry()
        assembler = ContextAssembler(reg, VaultAdapter(root))

        pkg = assembler.assemble(AssemblyRequest(
            element_type="npc", anchor_id=npc, locale_id=settlement,
            imprint="The entity being generated is named 'Torvald'.",
            directives="Make them owe someone a debt.",
        ))

        # Layer 1: pillars + calendar + linguistic anchor (linked via locale chain)
        assert "Magic always has a price" in pkg.world_frame
        assert "Year zero is the Sundering" in pkg.world_frame
        assert "Cinder Tongue" in pkg.world_frame

        # Layer 2: containment chain innermost-first, enriched by the vault page
        assert pkg.locale.index("Blackspire Keep") < pkg.locale.index("Cindermarch")
        assert "whisper the names of the fallen" in pkg.locale

        # Layer 3: anchor summary + graph facts
        assert "compromised" in pkg.lineage
        assert "rival_of" in pkg.lineage

        # Layer 4: same-type + nearby + vault index, no deprecated pages
        assert "Sable Vey" in pkg.roster
        assert "The Ashen Road" in pkg.roster
        assert "Old Fort" not in pkg.roster
        assert "Do NOT recreate" in pkg.roster

        # Layer 5 + rendering
        assert "Torvald" in pkg.directives and "debt" in pkg.directives
        rendered = pkg.for_decoder()
        assert "## WORLD FRAME" in rendered and "## DIRECTIVES" in rendered
        # canon_slice: truth only, no generation directives
        slice_ = pkg.canon_slice()
        assert "Magic always has a price" in slice_
        assert "Torvald" not in slice_
    with_vault(check)
    print("✓ test_assembler_layers passed")


def test_assembler_without_vault_or_ids():
    reg, *_ = build_registry()
    assembler = ContextAssembler(reg, vault=None)
    pkg = assembler.assemble(AssemblyRequest(element_type="quest"))
    # No anchor, no locale, no vault: world frame still finds the linguistic
    # profile, roster still lists registry names, and nothing crashes.
    assert "Cinder Tongue" in pkg.world_frame
    assert pkg.locale == "" and pkg.lineage == ""
    assert isinstance(pkg.for_decoder(), str)
    print("✓ test_assembler_without_vault_or_ids passed")


def test_assembler_budget_caps_layers():
    def check(root):
        reg, region, settlement, npc, lang, peer = build_registry()
        assembler = ContextAssembler(reg, VaultAdapter(root))
        req = AssemblyRequest(element_type="npc", anchor_id=npc, locale_id=settlement,
                              budget_tokens=100)  # absurdly small
        pkg = assembler.assemble(req)
        for layer in (pkg.world_frame, pkg.locale, pkg.lineage, pkg.roster):
            assert len(layer) <= 100 * 0.30 * 4 + 1
        # Caps drop whole lines, so what's left starts intact
        assert pkg.world_frame == "" or not pkg.world_frame.endswith(("Magi", "pric"))
    with_vault(check)
    print("✓ test_assembler_budget_caps_layers passed")


# ── Wiring ───────────────────────────────────────────────────

def test_decoder_format_context_accepts_all_shapes():
    from layer5_dna_substrate.decoder import format_context
    assert format_context(None) == "No additional context provided."
    assert format_context("already formatted") == "already formatted"
    assert format_context({"notes": "abc"}) == "notes: abc"
    pkg = ContextPackage(world_frame="THE PILLARS")
    assert "THE PILLARS" in format_context(pkg)
    print("✓ test_decoder_format_context_accepts_all_shapes passed")


def test_expand_stub_uses_assembler_package():
    def check(root):
        reg, region, settlement, npc, lang, peer = build_registry()
        assembler = ContextAssembler(reg, VaultAdapter(root))
        received = {}

        class FakeForge:
            def synthesize_element(self, element_type, constraint_package=""):
                received["constraints"] = constraint_package
                return {"type": element_type, "dna": "FAKE", "constraints": constraint_package}

        class FakeDecoder:
            def decode_element(self, element_data, context=None):
                received["context"] = context
                return ("### **Torvald Ashhand**\n\nProse.\n\n"
                        "```yaml\nname: Torvald Ashhand\ngist: A debtor blacksmith.\n"
                        "summary: Owes Sable Vey a fortune.\nstubs: []\n```")

        manager = ExpansionManager(reg, FakeForge(), inheritance=None, decoder=FakeDecoder(),
                                   assembler=assembler)
        stub_ids = manager.parse_and_register_stubs(
            npc, "### Src\n```yaml\nname: Warden Hesk\ngist: g\nstubs:\n"
                 "  - type: npc\n    name: Torvald\n    gist: A blacksmith Hesk owes.\n```")
        assert len(stub_ids) == 1

        manager.expand_stub(stub_ids[0])

        # The decoder received the assembled package, not a notes dict
        pkg = received["context"]
        assert hasattr(pkg, "for_decoder")
        assert "Magic always has a price" in pkg.world_frame      # vault reached the decode
        assert "Blackspire Keep" in pkg.locale                    # locale resolved via npc's parent
        assert "Torvald" in pkg.directives                        # imprint carried through
        assert received["constraints"] == ""                      # no double lineage injection

        record = reg.get_element(stub_ids[0])
        assert record["name"] == "Torvald Ashhand"
        assert record["summary"] == "Owes Sable Vey a fortune."
    with_vault(check)
    print("✓ test_expand_stub_uses_assembler_package passed")


if __name__ == "__main__":
    test_vault_adapter_reads_overview_and_calendar()
    test_vault_adapter_roster_and_excerpt()
    test_vault_adapter_missing_vault_degrades()
    test_assembler_layers()
    test_assembler_without_vault_or_ids()
    test_assembler_budget_caps_layers()
    test_decoder_format_context_accepts_all_shapes()
    test_expand_stub_uses_assembler_package()
    print("\nAll context assembler tests passed.")
