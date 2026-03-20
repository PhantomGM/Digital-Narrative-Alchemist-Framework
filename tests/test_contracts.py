"""
Unit tests for Phase 2 Bucket G — Structured Agent Contracts.

Validates that all Pydantic schemas correctly serialize/deserialize
and enforce their field constraints.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from core.contracts import (
    IntentResult,
    ArbiterOutcome,
    WeaverRequest,
    GuardrailVerdict,
    CriticVerdict,
    LoreChunk,
    EncounterSpec,
)


class TestArbiterOutcome:
    """Tests for the ArbiterOutcome contract."""

    def test_basic_creation(self):
        outcome = ArbiterOutcome(success=True, narrative_effect="A solid hit!")
        assert outcome.success is True
        assert outcome.narrative_effect == "A solid hit!"
        assert outcome.damage is None
        assert outcome.state_delta is None

    def test_with_damage_and_delta(self):
        outcome = ArbiterOutcome(
            success=True,
            narrative_effect="Critical strike!",
            damage=16,
            state_delta={"hp": -16},
            target_id="goblin_01"
        )
        assert outcome.damage == 16
        assert outcome.state_delta == {"hp": -16}
        assert outcome.target_id == "goblin_01"

    def test_serialization_roundtrip(self):
        original = ArbiterOutcome(success=False, narrative_effect="You missed.", damage=0)
        data = original.model_dump()
        restored = ArbiterOutcome(**data)
        assert restored.success == original.success
        assert restored.narrative_effect == original.narrative_effect


class TestGuardrailVerdict:
    """Tests for the GuardrailVerdict contract (used by Safety Gov + Auditor)."""

    def test_valid_verdict(self):
        v = GuardrailVerdict(status="valid")
        assert v.status == "valid"
        assert v.correction_note == ""
        assert v.offending_text == ""

    def test_invalid_with_offending_text(self):
        v = GuardrailVerdict(
            status="invalid",
            correction_note="Dead NPC speaking",
            offending_text="The goblin chieftain greets you warmly."
        )
        assert v.status == "invalid"
        assert "Dead NPC" in v.correction_note
        assert "goblin chieftain" in v.offending_text

    def test_from_raw_dict(self):
        """Simulates wrapping a raw safety_gov return dict."""
        raw = {"status": "valid", "correction_note": ""}
        v = GuardrailVerdict(**raw)
        assert v.status == "valid"


class TestCriticVerdict:
    """Tests for the State Critic circuit breaker contract."""

    def test_consistent(self):
        v = CriticVerdict(is_consistent=True)
        assert v.is_consistent is True
        assert v.mismatch_detail == ""

    def test_mismatch(self):
        v = CriticVerdict(
            is_consistent=False,
            mismatch_detail="Prose describes failure but Arbiter says success"
        )
        assert v.is_consistent is False
        assert "failure" in v.mismatch_detail


class TestLoreChunk:
    """Tests for the LoreChunk contract (Bucket H: Dual-Memory)."""

    def test_basic_lore(self):
        chunk = LoreChunk(
            fact="Goblin dropped a rusty dagger",
            entity_id="goblin_04",
            importance=3,
        )
        assert chunk.fact == "Goblin dropped a rusty dagger"
        assert chunk.importance == 3
        assert chunk.source_turn == 0

    def test_defaults(self):
        chunk = LoreChunk(fact="It rained.")
        assert chunk.entity_id == ""
        assert chunk.location == ""
        assert chunk.importance == 1
        assert chunk.source_turn == 0


class TestEncounterSpec:
    """Tests for the EncounterSpec contract."""

    def test_from_raw_simulator(self):
        """Simulates wrapping EncounterDirector output."""
        raw = {"type": "combat_or_social", "description": "A rival party demands a toll."}
        spec = EncounterSpec(encounter_type=raw["type"], description=raw["description"])
        assert spec.encounter_type == "combat_or_social"
        assert "rival" in spec.description
        assert spec.danger_level == 5  # default


class TestIntentResult:
    """Tests for the Orchestrator IntentResult contract."""

    def test_basic_routing(self):
        result = IntentResult(
            workflow="scene_flow",
            reasoning="Player is just talking to an NPC",
            status="routed_to_narrative"
        )
        assert result.workflow == "scene_flow"
        assert result.outcome is None

    def test_with_arbiter_outcome(self):
        outcome = ArbiterOutcome(success=True, narrative_effect="Hit!", damage=8)
        result = IntentResult(
            workflow="mechanics_required",
            reasoning="Player attacked",
            status="resolved_via_rules",
            outcome=outcome
        )
        assert result.outcome is not None
        assert result.outcome.damage == 8


class TestWeaverRequest:
    """Tests for the WeaverRequest contract."""

    def test_full_request(self):
        req = WeaverRequest(
            mechanical_outcome=ArbiterOutcome(success=True, narrative_effect="Hit!"),
            scene_context="A dark tavern",
            injection_note="(GM: Encounter incoming)",
            recent_events="Player searched the chest."
        )
        assert req.scene_context == "A dark tavern"
        assert "Encounter" in req.injection_note
