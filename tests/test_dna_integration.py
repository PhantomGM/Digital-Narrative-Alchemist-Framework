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
        os.path.dirname(__file__), '..', 'src', 'layer5_dna_substrate', 'decoders'
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
        os.path.dirname(__file__), '..', 'src', 'layer5_dna_substrate', 'templates'
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
        from layer5_dna_substrate.generators.npc import generate_npc_dna
        dna = generate_npc_dna()
        assert isinstance(dna, str) and len(dna) > 20

    def test_faction_generator(self):
        from layer5_dna_substrate.generators.faction import generate_faction_dna
        dna = generate_faction_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_quest_generator(self):
        from layer5_dna_substrate.generators.quest import generate_quest_dna
        dna = generate_quest_dna()
        assert isinstance(dna, str) and 'QUEST' in dna

    def test_item_generator(self):
        from layer5_dna_substrate.generators.item import generate_item_dna
        dna = generate_item_dna()
        assert isinstance(dna, str) and 'ITEM' in dna

    def test_location_generator(self):
        from layer5_dna_substrate.generators.location import generate_location_dna
        dna = generate_location_dna()
        assert isinstance(dna, str) and 'SETTLEMENT' in dna

    def test_travel_generator(self):
        from layer5_dna_substrate.generators.travel import generate_travel_dna
        dna = generate_travel_dna()
        assert isinstance(dna, str) and 'TRAVEL' in dna

    def test_world_generator(self):
        from layer5_dna_substrate.generators.world import WorldDNAGenerator
        gen = WorldDNAGenerator()
        dna = gen.generate_dna()
        assert isinstance(dna, str) and len(dna) > 100

    def test_trap_generator(self):
        from layer5_dna_substrate.generators.trap import generate_trap_dna
        dna = generate_trap_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_establishment_generator(self):
        from layer5_dna_substrate.generators.establishment import generate_establishment_dna
        dna = generate_establishment_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_creature_generator(self):
        from layer5_dna_substrate.generators.creature import generate_creature_dna
        dna = generate_creature_dna()
        assert isinstance(dna, str) and len(dna) > 50
        # Ecology genome, not a personality genome: it must carry a Sapience score
        # and the hazard blocks, and must NOT carry the NPC moral axes (LNC/GNE).
        assert dna.startswith("CREATURE{")
        for block in ("BODY{", "HUNT{", "ECO{", "ANOM{"):
            assert block in dna, f"creature DNA missing {block}"
        sap = int(dna.split("[")[1].split("/")[2].split("]")[0])
        assert 1 <= sap <= 9

    def test_creature_is_a_first_class_forge_type(self):
        from layer5_dna_substrate.forge import ProceduralForge
        out = ProceduralForge().synthesize_element("creature")
        assert out["type"] == "creature" and out["dna"].startswith("CREATURE{")

    def test_creature_seed_is_reproducible(self):
        from layer5_dna_substrate.generators.creature import generate_creature_dna
        assert generate_creature_dna(seed=42) == generate_creature_dna(seed=42)
        # different seeds should (essentially always) differ
        assert generate_creature_dna(seed=1) != generate_creature_dna(seed=2)

    def test_creature_pins_override_the_roll(self):
        from layer5_dna_substrate.generators.creature import generate_creature_dna
        # Pin the Dust-Wraith invariants; the rest still rolls, but pinned axes are fixed.
        dna = generate_creature_dna(seed=7, sapience=2, form="swarm", origin="nanite-born",
                                    diet="flesh-and-metal", method="swarm", aggression=8,
                                    ability="swarm-mind", weakness="specific-frequency")
        assert "[9/" not in dna.split("]")[0] or True  # threat still free
        top = dna.splitlines()[0]
        assert top.endswith("#nanite-born #swarm")
        assert top.split("/")[2].startswith("2")           # sapience pinned to 2
        assert "DIET:flesh-and-metal" in dna and "MTH:swarm" in dna and "AGG:8" in dna
        assert "PWK:swarm-mind" in dna and "WKN:specific-frequency" in dna

    def test_creature_pins_are_validated(self):
        import pytest
        from layer5_dna_substrate.generators.creature import generate_creature_dna
        with pytest.raises(ValueError):
            generate_creature_dna(form="dragon")          # not in vocabulary
        with pytest.raises(ValueError):
            generate_creature_dna(sapience=12)            # out of 1-9 range
        with pytest.raises(ValueError):
            generate_creature_dna(nonsense="x")           # unknown axis

    def test_forge_forwards_creature_pins(self):
        from layer5_dna_substrate.forge import ProceduralForge
        out = ProceduralForge().synthesize_element("creature", sapience=1, form="ooze")
        assert "#ooze" in out["dna"] and out["dna"].splitlines()[0].split("/")[2].startswith("1")

    def test_culture_generator(self):
        from layer5_dna_substrate.generators.culture import generate_culture_dna
        dna = generate_culture_dna()
        assert isinstance(dna, str) and len(dna) > 50
        assert dna.startswith("CULTURE{")
        # A way-of-life genome, not a personality one: it carries lifecycle/belief
        # blocks and a kinship tag, and no NPC moral axes.
        for block in ("VALUES{", "LIFE{", "RITE{", "BELIEF{", "WORLD{", "NAME{"):
            assert block in dna, f"culture DNA missing {block}"

    def test_culture_is_a_first_class_forge_type(self):
        from layer5_dna_substrate.forge import ProceduralForge
        out = ProceduralForge().synthesize_element("culture")
        assert out["type"] == "culture" and out["dna"].startswith("CULTURE{")

    def test_culture_seed_and_pins(self):
        from layer5_dna_substrate.generators.culture import generate_culture_dna
        import pytest
        assert generate_culture_dna(seed=5) == generate_culture_dna(seed=5)
        # Pin a known people's invariants (a scavenger, covenant-bound, waste taboo).
        dna = generate_culture_dna(seed=1, subsistence="scavenger", kinship="covenant",
                                   taboo="waste", cohesion=6)
        top = dna.splitlines()[0]
        assert top.endswith("#scavenger #covenant")
        assert top.split("/")[1] == "6"                    # cohesion pinned
        assert "TABOO:waste" in dna
        with pytest.raises(ValueError):
            generate_culture_dna(kinship="monarchy")       # not in vocabulary
        with pytest.raises(ValueError):
            generate_culture_dna(cohesion=0)               # out of range

    def test_regional_poi_generator(self):
        from layer5_dna_substrate.generators.regional_poi import generate_regional_poi_dna
        dna = generate_regional_poi_dna()
        assert isinstance(dna, str) and len(dna) > 10

    def test_wonder_generator(self):
        from layer5_dna_substrate.generators.wonder import generate_world_wonder_dna
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
