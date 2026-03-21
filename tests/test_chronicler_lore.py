"""
Unit tests for Phase 2 Bucket H — Chronicler Lore Extraction.

Tests the Chronicler's _extract_lore_chunks() method and query_lore()
to verify that discrete, immutable LoreChunks are correctly generated
from raw events and searchable by entity, location, and importance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import patch
from layer2_narrative.event_ledger import StateEvent
from layer1_core.contracts import LoreChunk


@pytest.fixture
def chronicler():
    """Create a Chronicler with mocked LLM."""
    with patch('layer3_operations.chronicler.ChatOpenAI'):
        from layer3_operations.chronicler import Chronicler
        c = Chronicler(compression_interval=5)
        return c


@pytest.fixture
def sample_events():
    """Create a batch of sample events for lore extraction."""
    return [
        StateEvent(
            event_type="ADD_ENTITY",
            target="npc_blacksmith",
            delta={"name": "Kael", "role": "blacksmith"},
            source_agent="ProceduralForge",
            location="iron_district",
        ),
        StateEvent(
            event_type="TURN_COMPLETED",
            target="player_01",
            delta={"action": "searched the chest", "outcome": "routed_to_narrative"},
            source_agent="SessionDirector",
            location="tavern_cellar",
        ),
        StateEvent(
            event_type="REMOVE_ENTITY",
            target="goblin_04",
            delta={"reason": "killed in combat"},
            source_agent="Arbiter",
            location="tavern_cellar",
        ),
        StateEvent(
            event_type="PACING_SHIFT",
            target="tavern_cellar",
            delta={"pacing": "tense", "encounter": "Rival party appears"},
            source_agent="SessionDirector",
            location="tavern_cellar",
        ),
    ]


class TestLoreExtraction:
    """Tests for the _extract_lore_chunks method."""

    def test_extracts_correct_count(self, chronicler, sample_events):
        chunks = chronicler._extract_lore_chunks(sample_events)
        assert len(chunks) == 4

    def test_entity_ids_preserved(self, chronicler, sample_events):
        chunks = chronicler._extract_lore_chunks(sample_events)
        entity_ids = [c.entity_id for c in chunks]
        assert "npc_blacksmith" in entity_ids
        assert "goblin_04" in entity_ids
        assert "player_01" in entity_ids

    def test_locations_preserved(self, chronicler, sample_events):
        chunks = chronicler._extract_lore_chunks(sample_events)
        locations = [c.location for c in chunks]
        assert "iron_district" in locations
        assert "tavern_cellar" in locations

    def test_importance_mapping(self, chronicler, sample_events):
        chunks = chronicler._extract_lore_chunks(sample_events)
        importance_by_entity = {c.entity_id: c.importance for c in chunks}
        # ADD_ENTITY = 3, TURN_COMPLETED = 1, REMOVE_ENTITY = 4, PACING_SHIFT = 2
        assert importance_by_entity["npc_blacksmith"] == 3
        assert importance_by_entity["player_01"] == 1
        assert importance_by_entity["goblin_04"] == 4

    def test_facts_contain_delta_data(self, chronicler, sample_events):
        chunks = chronicler._extract_lore_chunks(sample_events)
        blacksmith = next(c for c in chunks if c.entity_id == "npc_blacksmith")
        assert "Kael" in blacksmith.fact
        assert "blacksmith" in blacksmith.fact

    def test_all_chunks_are_lore_chunk_type(self, chronicler, sample_events):
        chunks = chronicler._extract_lore_chunks(sample_events)
        for chunk in chunks:
            assert isinstance(chunk, LoreChunk)


class TestLoreQuery:
    """Tests for the query_lore method."""

    def test_query_by_entity(self, chronicler, sample_events):
        chronicler._lore_store = chronicler._extract_lore_chunks(sample_events)
        results = chronicler.query_lore(entity_id="goblin_04")
        assert len(results) == 1
        assert results[0].entity_id == "goblin_04"

    def test_query_by_location(self, chronicler, sample_events):
        chronicler._lore_store = chronicler._extract_lore_chunks(sample_events)
        results = chronicler.query_lore(location="tavern_cellar")
        assert len(results) == 3  # player_01, goblin_04, pacing

    def test_query_by_min_importance(self, chronicler, sample_events):
        chronicler._lore_store = chronicler._extract_lore_chunks(sample_events)
        results = chronicler.query_lore(min_importance=3)
        assert len(results) == 2  # ADD_ENTITY(3) and REMOVE_ENTITY(4)

    def test_query_all(self, chronicler, sample_events):
        chronicler._lore_store = chronicler._extract_lore_chunks(sample_events)
        results = chronicler.query_lore()
        assert len(results) == 4

    def test_lore_count_property(self, chronicler, sample_events):
        assert chronicler.lore_count == 0
        chronicler._lore_store = chronicler._extract_lore_chunks(sample_events)
        assert chronicler.lore_count == 4

    def test_query_nonexistent_entity(self, chronicler, sample_events):
        chronicler._lore_store = chronicler._extract_lore_chunks(sample_events)
        results = chronicler.query_lore(entity_id="does_not_exist")
        assert len(results) == 0
