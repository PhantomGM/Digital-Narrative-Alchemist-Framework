"""
Smoke tests for DNA/Gene integration — verifies that all decoder prompts load
correctly and all generators produce non-empty DNA strings.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest


class TestDecoderLoading:
    """Verify all decoder .md files exist and are loadable."""

    DECODERS_DIR = os.path.join(
        os.path.dirname(__file__), '..', 'src', 'agents', 'layer2_dna', 'decoders'
    )

    EXPECTED_DECODERS = [
        'npc.md', 'faction.md', 'quest.md', 'item.md',
        'location.md', 'travel.md', 'world.md',
        'settlement.md', 'region.md',  # New in this integration
    ]

    def test_all_decoder_files_exist(self):
        for decoder in self.EXPECTED_DECODERS:
            path = os.path.join(self.DECODERS_DIR, decoder)
            assert os.path.exists(path), f"Missing decoder: {decoder}"

    def test_decoder_files_are_non_empty(self):
        for decoder in self.EXPECTED_DECODERS:
            path = os.path.join(self.DECODERS_DIR, decoder)
            size = os.path.getsize(path)
            assert size > 1000, f"Decoder {decoder} is too small ({size} bytes) — may not be the canonical version"

    def test_decoder_files_contain_decoding_instructions(self):
        """All canonical decoders should contain structured decoding instructions."""
        VALID_HEADERS = ['CRITICAL OUTPUT RULES', 'DECODING INSTRUCTIONS', 'FINAL INSTRUCTIONS', 'DECODING PROCESS']
        for decoder in self.EXPECTED_DECODERS:
            path = os.path.join(self.DECODERS_DIR, decoder)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().upper()
            has_header = any(h.upper() in content for h in VALID_HEADERS)
            assert has_header, \
                f"Decoder {decoder} missing any of: {VALID_HEADERS}"


class TestTemplateLoading:
    """Verify all output template files exist and have YAML frontmatter."""

    TEMPLATES_DIR = os.path.join(
        os.path.dirname(__file__), '..', 'src', 'agents', 'layer2_dna', 'templates'
    )

    EXPECTED_TEMPLATES = [
        'npc.md', 'faction.md', 'quest.md', 'item.md',
        'settlement.md', 'region.md', 'travel.md', 'world.md',
    ]

    def test_all_template_files_exist(self):
        for template in self.EXPECTED_TEMPLATES:
            path = os.path.join(self.TEMPLATES_DIR, template)
            assert os.path.exists(path), f"Missing template: {template}"

    def test_template_files_have_yaml_frontmatter(self):
        for template in self.EXPECTED_TEMPLATES:
            path = os.path.join(self.TEMPLATES_DIR, template)
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            assert first_line == '---', \
                f"Template {template} missing YAML frontmatter (first line: '{first_line}')"


class TestGeneratorSmokeTests:
    """Run every generator function and verify it produces a non-empty DNA string."""

    def test_npc_generator(self):
        from agents.layer2_dna.generators.npc import generate_npc_dna
        dna = generate_npc_dna()
        assert isinstance(dna, str) and len(dna) > 20

    def test_faction_generator(self):
        from agents.layer2_dna.generators.faction import generate_faction_dna
        dna = generate_faction_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_quest_generator(self):
        from agents.layer2_dna.generators.quest import generate_quest_dna
        dna = generate_quest_dna()
        assert isinstance(dna, str) and 'QUEST' in dna

    def test_item_generator(self):
        from agents.layer2_dna.generators.item import generate_item_dna
        dna = generate_item_dna()
        assert isinstance(dna, str) and 'ITEM' in dna

    def test_location_generator(self):
        from agents.layer2_dna.generators.location import generate_location_dna
        dna = generate_location_dna()
        assert isinstance(dna, str) and 'SETTLEMENT' in dna

    def test_travel_generator(self):
        from agents.layer2_dna.generators.travel import generate_travel_dna
        dna = generate_travel_dna()
        assert isinstance(dna, str) and 'TRAVEL' in dna

    def test_world_generator(self):
        from agents.layer2_dna.generators.world import WorldDNAGenerator
        gen = WorldDNAGenerator()
        dna = gen.generate_dna()
        assert isinstance(dna, str) and len(dna) > 100

    def test_trap_generator(self):
        from agents.layer2_dna.generators.trap import generate_trap_dna
        dna = generate_trap_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_establishment_generator(self):
        from agents.layer2_dna.generators.establishment import generate_establishment_dna
        dna = generate_establishment_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_regional_poi_generator(self):
        from agents.layer2_dna.generators.regional_poi import generate_regional_poi_dna
        dna = generate_regional_poi_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_wonder_generator(self):
        from agents.layer2_dna.generators.wonder import generate_world_wonder_dna
        dna = generate_world_wonder_dna()
        assert isinstance(dna, str) and len(dna) > 10


class TestSystemDocsExist:
    """Verify system specification documents were imported."""

    DOCS_DIR = os.path.join(
        os.path.dirname(__file__), '..', 'docs', 'dna_specs'
    )

    EXPECTED_DOCS = [
        'dna_system_rules.md',
        'metadata_priority_logic.md',
        'conductor_routing.md',
    ]

    def test_system_docs_exist(self):
        for doc in self.EXPECTED_DOCS:
            path = os.path.join(self.DOCS_DIR, doc)
            assert os.path.exists(path), f"Missing system doc: {doc}"

    def test_system_docs_are_substantial(self):
        for doc in self.EXPECTED_DOCS:
            path = os.path.join(self.DOCS_DIR, doc)
            size = os.path.getsize(path)
            assert size > 2000, f"System doc {doc} is too small ({size} bytes)"
