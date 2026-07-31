"""
Unit tests for the structured phenotype tail (phenotype_meta) and its
integration with the DNARegistry and ExpansionManager.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.phenotype_meta import (
    parse_phenotype_tail, strip_phenotype_tail, strip_decoder_artifacts)
from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.inheritance import InheritanceEngine
from layer5_dna_substrate.expansion_manager import ExpansionManager, _resolve_stub_type


SAMPLE_PROFILE = """### **Vaelthra the Thornbound**

**Role:** The BBEG

A rose carved from bone, blooming only where blood has been spilled.

### 🔗 Unmade Connections (DNA Stubs)

* **[NPC] High Inquisitor Eloril:** Blindly loyal enforcer, former student.
* **[Faction] The Crimson Choir:** A rebel faction of bards once aligned with her.

```yaml
name: Vaelthra the Thornbound
gist: A tyrannical drow priestess who enforces sacred order to smother the chaos inside her.
summary: >
  Once a high priestess of the Umbral Synod, Vaelthra purged her temple's elders
  and now rules a subterranean order through ritual and fear. She believes
  obedience is grace and hides both a forbidden moon-shard and a living twin
  sister leading a resistance against her.
stubs:
  - type: npc
    name: High Inquisitor Eloril
    gist: Blindly loyal enforcer and former student of Vaelthra.
  - type: rebel group
    name: The Crimson Choir
    gist: A rebel faction of bards once aligned with Vaelthra.
```
"""


def test_parse_tail_extracts_fields():
    meta = parse_phenotype_tail(SAMPLE_PROFILE)
    assert meta is not None
    assert meta["name"] == "Vaelthra the Thornbound"
    assert meta["gist"].startswith("A tyrannical drow priestess")
    assert "Umbral Synod" in meta["summary"]
    assert len(meta["stubs"]) == 2
    assert meta["stubs"][0] == {
        "type": "npc",
        "name": "High Inquisitor Eloril",
        "gist": "Blindly loyal enforcer and former student of Vaelthra.",
    }
    print("✓ test_parse_tail_extracts_fields passed")


def test_parse_returns_none_without_tail():
    assert parse_phenotype_tail("### Just a profile\nNo tail here.") is None
    assert parse_phenotype_tail("") is None
    assert parse_phenotype_tail(None) is None
    # A YAML block that isn't a tail (no name/gist/summary) is ignored
    assert parse_phenotype_tail("```yaml\nfoo: bar\n```") is None
    print("✓ test_parse_returns_none_without_tail passed")


def test_parse_picks_last_valid_block():
    text = (
        "```yaml\nname: Decoy Early Block\n```\n\nProse in between.\n\n"
        "```yaml\nname: The Real Entity\ngist: The actual tail.\nstubs: []\n```\n"
    )
    meta = parse_phenotype_tail(text)
    assert meta["name"] == "The Real Entity"
    assert meta["stubs"] == []
    print("✓ test_parse_picks_last_valid_block passed")


def test_strip_removes_only_tail():
    stripped = strip_phenotype_tail(SAMPLE_PROFILE)
    assert "Vaelthra the Thornbound" in stripped          # prose remains
    assert "Unmade Connections" in stripped               # prose section remains
    assert "```yaml" not in stripped                      # tail removed
    # Stripping is idempotent on tail-less text
    assert strip_phenotype_tail(stripped) == stripped
    print("✓ test_strip_removes_only_tail passed")


def test_strip_removes_echoed_tail_heading():
    """Decoders that echo the tail instruction's heading must not leave it orphaned."""
    with_heading = (
        "### **Entity**\n\nProse.\n\n---\n\n"
        "### 🔩 MACHINE-READABLE TAIL (MANDATORY)\n\n"
        "```yaml\nname: Entity\ngist: A thing.\nstubs: []\n```\n"
    )
    stripped = strip_phenotype_tail(with_heading)
    assert "MACHINE-READABLE TAIL" not in stripped
    assert "```yaml" not in stripped
    assert stripped.rstrip().endswith("---")
    assert "Prose." in stripped

    # Heading with no fenced block behind it is still cleaned up
    orphan_only = "### **Entity**\n\nProse.\n\n### MACHINE-READABLE TAIL (MANDATORY)\n"
    assert "MACHINE-READABLE TAIL" not in strip_phenotype_tail(orphan_only)

    # A heading mid-document (not trailing) is left alone
    mid = "Intro\n\n## MACHINE-READABLE TAIL notes\n\nMore prose after.\n"
    assert strip_phenotype_tail(mid) == mid
    print("✓ test_strip_removes_echoed_tail_heading passed")


def test_strip_decoder_artifacts_removes_art_keeps_prose():
    """Fenced diagrams and ASCII art are scaffolding; fenced in-world prose is content."""
    flow = ("Intro.\n\n```\n[Scarcity] ──> [Broker Monopoly] ──> [Cartel]\n```\n\nOutro.\n")
    assert "──>" not in strip_decoder_artifacts(flow)
    assert "Intro." in strip_decoder_artifacts(flow) and "Outro." in strip_decoder_artifacts(flow)

    ascii_art = ("Before.\n\n```\n      _.-'''''-._\n     /  (o)  (o) \\\n     '-._______.-'\n```\n\nAfter.\n")
    assert "(o)" not in strip_decoder_artifacts(ascii_art)
    assert "Before." in strip_decoder_artifacts(ascii_art)

    # An in-world quotation must survive untouched
    quote = ('Prose.\n\n```\n"To cross into the Wastes is to watch the world lose its colour."\n'
             "— From the journals of Master Cartographer Ilvane Roth, 298 AS\n```\n\nMore prose.\n")
    assert strip_decoder_artifacts(quote) == quote

    # The structured yaml tail is language-tagged and must never be touched here
    tail = "Prose.\n\n```yaml\nname: Thing\ngist: A thing.\nstubs: []\n```\n"
    assert strip_decoder_artifacts(tail) == tail
    print("✓ test_strip_decoder_artifacts_removes_art_keeps_prose passed")


def test_resolve_stub_type_fuzzy():
    assert _resolve_stub_type("npc") == "npc"
    assert _resolve_stub_type("rebel group") == "faction"
    assert _resolve_stub_type("ancient relic") == "item"
    assert _resolve_stub_type("Temple") == "location"
    assert _resolve_stub_type("something unknown") == "npc"  # default
    print("✓ test_resolve_stub_type_fuzzy passed")


def test_resolve_stub_type_lore_and_culture():
    """Beliefs file as lore; peoples file as culture. Neither should fall back to npc."""
    for raw in ("lore", "doctrine", "myth", "legend", "scripture", "prophecy", "creed"):
        assert _resolve_stub_type(raw) == "lore", raw
    for raw in ("culture", "people", "tribe", "society"):
        assert _resolve_stub_type(raw) == "culture", raw
    for raw in ("creature", "beast", "monster", "swarm", "predator"):
        assert _resolve_stub_type(raw) == "creature", raw

    # Adjacent types must not be swallowed by the new entries
    assert _resolve_stub_type("chronicle") == "chronicle"
    assert _resolve_stub_type("event") == "chronicle"
    assert _resolve_stub_type("faction") == "faction"
    assert _resolve_stub_type("person") == "npc"
    print("✓ test_resolve_stub_type_lore_and_culture passed")


def test_lore_and_culture_are_valid_tail_types():
    from layer5_dna_substrate.phenotype_meta import VALID_STUB_TYPES
    assert {"lore", "culture", "creature"} <= VALID_STUB_TYPES
    print("✓ test_lore_and_culture_are_valid_tail_types passed")


def test_structured_stubs_registered():
    reg = DNARegistry()
    manager = ExpansionManager(reg, forge=None, inheritance=None, decoder=None)

    source_id = reg.register_element("npc", "DNA_X", SAMPLE_PROFILE, name="Vaelthra the Thornbound")
    stub_ids = manager.parse_and_register_stubs(source_id, SAMPLE_PROFILE)

    assert len(stub_ids) == 2
    eloril = reg.find_by_name("High Inquisitor Eloril")
    assert eloril is not None
    assert eloril["type"] == "npc"
    assert eloril["gist"] == "Blindly loyal enforcer and former student of Vaelthra."
    assert "stub" in eloril["tags"]

    choir = reg.find_by_name("The Crimson Choir")
    assert choir["type"] == "faction"  # "rebel group" fuzzy-resolved

    # Both stubs are linked back to the source
    peer_ids = {edge["id"] for edge in reg.get_links(source_id)["peer"]}
    assert {eloril["id"], choir["id"]} <= peer_ids
    print("✓ test_structured_stubs_registered passed")


def test_find_by_name_matches_aliases():
    reg = DNARegistry()
    guild = reg.register_element("faction", "DNA_G", "The guild.", name="The Scriveners Guild")
    reg._records[guild]["aliases"] = ["Ancient Scriveners Guild"]
    assert reg.find_by_name("ancient scriveners guild")["id"] == guild
    assert reg.find_by_name("The Scriveners Guild")["id"] == guild
    assert reg.find_by_name("Some Other Guild") is None
    print("✓ test_find_by_name_matches_aliases passed")


def test_find_by_name_ignores_articles_and_punctuation():
    """A stray leading article or apostrophe must not mint a duplicate entity."""
    reg = DNARegistry()
    guild = reg.register_element("faction", "DNA_G", "The guild.", name="The Scriveners Guild")
    reg._records[guild]["aliases"] = ["Ancient Scriveners Guild"]

    # Article added to, or dropped from, the stored name
    assert reg.find_by_name("Scriveners Guild")["id"] == guild
    # Article added to an alias stored without one — the case that leaked through
    assert reg.find_by_name("The Ancient Scriveners Guild")["id"] == guild

    archives = reg.register_element("location", "DNA_A", "Archives.", name="The Scrivener's Archives")
    assert reg.find_by_name("Scriveners Archives")["id"] == archives   # punctuation-insensitive

    # Genuinely different names still miss
    assert reg.find_by_name("The Whisperers") is None
    print("✓ test_find_by_name_ignores_articles_and_punctuation passed")


def test_stub_dedupe_links_existing_entity():
    reg = DNARegistry()
    manager = ExpansionManager(reg, forge=None, inheritance=None, decoder=None)

    existing_id = reg.register_element("npc", "DNA_E", "An enforcer.", name="High Inquisitor Eloril")
    source_id = reg.register_element("npc", "DNA_X", SAMPLE_PROFILE, name="Vaelthra the Thornbound")

    stub_ids = manager.parse_and_register_stubs(source_id, SAMPLE_PROFILE)

    # Eloril already existed: linked, not duplicated
    assert len(stub_ids) == 1
    assert len(reg.get_all_by_type("npc")) == 2  # Vaelthra + original Eloril only
    peer_ids = {edge["id"] for edge in reg.get_links(source_id)["peer"]}
    assert existing_id in peer_ids
    print("✓ test_stub_dedupe_links_existing_entity passed")


def test_legacy_regex_fallback_still_works():
    reg = DNARegistry()
    manager = ExpansionManager(reg, forge=None, inheritance=None, decoder=None)

    legacy_profile = (
        "### **Old Entity**\n\nSome prose.\n\n"
        "### 🔗 Unmade Connections (DNA Stubs)\n\n"
        "* **[Location] The Sunken Temple:** A drowned shrine she still visits.\n\n---\n"
    )
    source_id = reg.register_element("npc", "DNA_L", legacy_profile, name="Old Entity")
    stub_ids = manager.parse_and_register_stubs(source_id, legacy_profile)

    assert len(stub_ids) == 1
    temple = reg.find_by_name("The Sunken Temple")
    assert temple is not None
    assert temple["type"] == "location"
    print("✓ test_legacy_regex_fallback_still_works passed")


def test_expand_stub_stores_tail_metadata():
    reg = DNARegistry()

    class FakeForge:
        def synthesize_element(self, element_type, constraint_package=""):
            return {"type": element_type, "dna": "FAKE_DNA", "constraints": constraint_package}

    class FakeDecoder:
        def decode_element(self, element_data, context=None):
            return SAMPLE_PROFILE  # pretend the LLM decoded Vaelthra

    manager = ExpansionManager(reg, FakeForge(), InheritanceEngine(reg), FakeDecoder())

    source_id = reg.register_element("faction", "DNA_S", "The Umbral Synod.", name="Umbral Synod")
    stub_ids = manager.parse_and_register_stubs(
        source_id,
        "### Src\n```yaml\nname: Umbral Synod\ngist: g\nstubs:\n  - type: npc\n    name: Vaelthra\n    gist: Their exiled priestess.\n```",
    )
    assert len(stub_ids) == 1

    manager.expand_stub(stub_ids[0])
    record = reg.get_element(stub_ids[0])
    assert record["name"] == "Vaelthra the Thornbound"   # tail name wins over stub name
    assert record["gist"].startswith("A tyrannical drow priestess")
    assert "Umbral Synod" in record["summary"]
    assert "stub" not in record["tags"] and "expanded" in record["tags"]
    print("✓ test_expand_stub_stores_tail_metadata passed")


def test_inheritance_prefers_gist_and_summary():
    reg = DNARegistry()
    engine = InheritanceEngine(reg)

    with_meta = reg.register_element(
        "npc", "DNA_1", "### **Someone**\nLong appearance prose that should not appear...",
        name="Someone", gist="A spy posing as a baker.", summary="Feeds secrets to the Choir.",
        tags=["spy"],
    )
    without_meta = reg.register_element("npc", "DNA_2", "Raw phenotype text only.", tags=["old"])

    constraints = engine.compile_constraints([with_meta, without_meta])
    assert "A spy posing as a baker." in constraints
    assert "Feeds secrets to the Choir." in constraints
    assert "Long appearance prose" not in constraints      # summary replaced truncation
    assert "Raw phenotype text only." in constraints       # legacy path intact
    print("✓ test_inheritance_prefers_gist_and_summary passed")


if __name__ == "__main__":
    test_parse_tail_extracts_fields()
    test_parse_returns_none_without_tail()
    test_parse_picks_last_valid_block()
    test_strip_removes_only_tail()
    test_resolve_stub_type_fuzzy()
    test_structured_stubs_registered()
    test_stub_dedupe_links_existing_entity()
    test_legacy_regex_fallback_still_works()
    test_expand_stub_stores_tail_metadata()
    test_inheritance_prefers_gist_and_summary()
    print("\nAll phenotype_meta tests passed.")
