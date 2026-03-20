"""
Agent Contracts — Typed schemas for inter-agent communication.

Solves: Phase 2 Bottleneck — "Telephone Game" / Parsing Failures
Enhancement: Bucket G (Structured Agent Contracts)

Every agent-to-agent hand-off in the DNA Framework must use one of
these Pydantic models. This eliminates:
  - Ambiguous string parsing between agents
  - Cumulative translation errors ("Telephone Game" effect)
  - Wasted tokens on intermediate re-interpretation

Usage:
  from core.contracts import IntentResult, ArbiterOutcome, GuardrailVerdict
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────
# Layer I — Runtime Contracts
# ──────────────────────────────────────────────────────────────────────

class IntentResult(BaseModel):
    """Output of the Orchestrator's intent classification.

    The Orchestrator parses player input and returns this structured
    decision. Downstream consumers never need to parse raw strings.
    """
    workflow: str = Field(
        description="Routing decision: 'scene_flow', 'mechanics_required', or 'generation_event'"
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation of why this workflow was chosen"
    )
    target_skill: Optional[str] = Field(
        default=None,
        description="Specific skill/stat to roll if mechanics_required"
    )
    status: str = Field(
        default="routed_to_narrative",
        description="Pipeline status: 'routed_to_narrative', 'resolved_via_rules', 'routed_to_forge', 'error'"
    )
    outcome: Optional[ArbiterOutcome] = Field(
        default=None,
        description="Populated when status='resolved_via_rules'"
    )
    message: Optional[str] = Field(
        default=None,
        description="Error details when status='error'"
    )


class ArbiterOutcome(BaseModel):
    """Output of a Layer IV Game System Arbiter (e.g., D&D 5e, Coin Flip).

    Mechanical truth — the Narrative Weaver must faithfully describe this
    result without inventing new consequences.
    """
    success: bool = Field(description="Whether the action succeeded mechanically")
    narrative_effect: str = Field(
        description="Plain-English description of the mechanical result for the Weaver"
    )
    damage: Optional[int] = Field(default=None, description="Damage dealt, if applicable")
    state_delta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Granular state changes (e.g., {'hp': -8}) for Event Ledger emission"
    )
    target_id: Optional[str] = Field(
        default=None,
        description="Entity ID affected by this outcome"
    )


# Forward reference resolution (IntentResult references ArbiterOutcome)
IntentResult.model_rebuild()


class WeaverRequest(BaseModel):
    """Input to the Narrative Weaver.

    Bundles everything the Weaver needs to generate prose without
    making any mechanical decisions of its own.
    """
    mechanical_outcome: ArbiterOutcome = Field(
        description="The Arbiter's resolved outcome to narrate"
    )
    scene_context: str = Field(
        description="Current location/scene description for tone grounding"
    )
    injection_note: str = Field(
        default="",
        description="Optional GM note (e.g., encounter injection) to weave in"
    )
    recent_events: str = Field(
        default="",
        description="Rendered Event Ledger context for continuity"
    )


# ──────────────────────────────────────────────────────────────────────
# Layer III — Guardrail Contracts
# ──────────────────────────────────────────────────────────────────────

class GuardrailVerdict(BaseModel):
    """Output of Safety Governor and Consistency Auditor checks.

    Both guardrails return the same shape, making them interchangeable
    in the parallel validation pipeline.
    """
    status: str = Field(description="'valid' or 'invalid'")
    correction_note: str = Field(
        default="",
        description="Explanation of the violation (empty if valid)"
    )
    offending_text: str = Field(
        default="",
        description="Exact offending sentence for surgical patching (Auditor only)"
    )


class CriticVerdict(BaseModel):
    """Output of the State Critic circuit breaker (Bucket I).

    A fast, boolean check: does the prose match the mechanical delta?
    """
    is_consistent: bool = Field(
        description="True if narrative faithfully represents the mechanical outcome"
    )
    mismatch_detail: str = Field(
        default="",
        description="What the prose got wrong vs. the mechanical truth"
    )


# ──────────────────────────────────────────────────────────────────────
# Layer II — DNA / PCG Contracts
# ──────────────────────────────────────────────────────────────────────

class LoreChunk(BaseModel):
    """An immutable factual record extracted from the Event Ledger.

    Used by the Chronicler's Lore Extractor (Bucket H) to replace
    lossy LLM summarization with discrete, searchable facts.
    """
    fact: str = Field(description="Single factual statement about the world")
    entity_id: str = Field(
        default="",
        description="DNA Registry ID of the entity this fact concerns"
    )
    location: str = Field(default="", description="Scene/location context")
    importance: int = Field(
        default=1,
        description="1-5 rating: 1=flavor, 3=plot-relevant, 5=campaign-critical"
    )
    source_turn: int = Field(
        default=0,
        description="The turn number when this fact was established"
    )


class EncounterSpec(BaseModel):
    """Output of the EncounterDirector when injecting a dynamic event."""
    encounter_type: str = Field(
        default="combat_or_social",
        description="Category: 'combat', 'social', 'environmental', 'combat_or_social'"
    )
    description: str = Field(description="Narrative hook for the encounter")
    danger_level: int = Field(
        default=5,
        description="1-10 danger rating for pacing calibration"
    )
