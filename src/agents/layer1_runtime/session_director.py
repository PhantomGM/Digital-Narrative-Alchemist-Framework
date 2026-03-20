import asyncio
from typing import Dict, Any, Optional
from agents.layer1_runtime.simulators import EnvironmentSimulator, EncounterDirector
from agents.layer3_support.consistency_auditor import ConsistencyAuditor
from agents.layer3_support.safety_governor import SafetyGovernor
from agents.layer3_support.player_profiles import PlayerProfileManager
from agents.layer3_support.chronicler import Chronicler
from agents.layer3_support.state_critic import StateCritic
from core.event_ledger import EventLedger, StateEvent
from core.contracts import (
    IntentResult,
    ArbiterOutcome,
    GuardrailVerdict,
    CriticVerdict,
    EncounterSpec,
)

class CharacterArcTracker:
    """Monitors PC personal arcs, awarding meta-currency and tracking goal progression."""
    def __init__(self):
        self.arcs = {}

    def register_pc(self, pc_id: str, goals: list, flaws: list):
        self.arcs[pc_id] = {"goals": goals, "flaws": flaws, "inspiration": 0}
        print(f"[ArcTracker] Registered arcs for {pc_id}.")

    def evaluate_action(self, pc_id: str, action: str) -> str:
        """A simple stub: In a full system, an LLM would evaluate if the action hits a goal/flaw."""
        return "Action did not trigger an arc milestone."

class SessionDirector:
    """
    Controls structural pacing, scene framing, escalation, and transition timing.
    Acts as the main loop coordinator between Layer I agents.

    Phase 1 Enhancements (Buckets A–E):
    - Parallel dispatch: Safety + Orchestrator run simultaneously
    - Patch-based auditing: Surgical sentence editing instead of regen
    - Event Ledger context: All agents share the same state deltas
    - Chronicler integration: Periodic context compression

    Phase 2 Enhancements (Buckets F–I):
    - Tri-Track Async (F): Background tasks never block the player response
    - Structured Contracts (G): Typed Pydantic schemas for all agent hand-offs
    - Dual-Memory / Lore Extraction (H): Chronicler extracts LoreChunks
    - State Critic (I): Fast mechanical-truth validation before guardrails
    """
    def __init__(self, orchestrator, weaver, state_keeper, registry=None):
        self.orchestrator = orchestrator
        self.weaver = weaver
        self.state_keeper = state_keeper
        self.registry = registry  # Optional link to Layer II
        self.arc_tracker = CharacterArcTracker()
        self.env_sim = EnvironmentSimulator()
        self.encounter_dir = EncounterDirector()

        # Layer III Support
        self.profile_manager = PlayerProfileManager()
        self.auditor = ConsistencyAuditor()
        self.safety_gov = SafetyGovernor(campaign_tone="Dark Fantasy", profile_manager=self.profile_manager)
        self.chronicler = Chronicler(compression_interval=10)
        self.state_critic = StateCritic()  # Bucket I: Circuit breaker

        self.current_scene = None
        self.pacing_level = "calm" # calm, tense, combat, climactic
        self._max_patch_attempts = 2  # Bucket B: cap on surgical edits

        # Track B/C background tasks (Bucket F: Tri-Track)
        self._background_tasks: list[asyncio.Task] = []

    def frame_scene(self, location_tag: str) -> str:
        """Retrieves state and asks the Weaver to set the opening scene."""
        reality = self.state_keeper.get_reality(location_tag)
        print(f"[SessionDirector] Framing Scene: {location_tag}. Pacing: {self.pacing_level}")
        return f"Scene Framed for {location_tag}. Entities present: {reality.get('entities', [])}"

    def _fire_background_tasks(self, location_tag: str, archivist=None):
        """
        Track B/C (Bucket F): Fire non-blocking background tasks.

        These run concurrently while the player reads their response.
        Track B: NPC Engine moves, Simulator updates (future)
        Track C: Chronicler compression, Lore Extraction
        """
        # Clean up completed background tasks
        self._background_tasks = [t for t in self._background_tasks if not t.done()]

        # Track C — Chronicler compression (already async)
        self.chronicler.tick()
        if self.chronicler.should_compress():
            task = asyncio.create_task(
                self.chronicler.compress(
                    self.state_keeper.event_ledger,
                    self.state_keeper,
                    archivist
                )
            )
            self._background_tasks.append(task)
            print("[SessionDirector] Track C: Chronicler compression fired in background.")

        # Track B — Simulator updates (stub — future: NPC Engine moves)
        # self._background_tasks.append(asyncio.create_task(self._run_simulators(location_tag)))

    async def advance_scene(self, player_id: str, player_input: str, location_tag: str) -> str:
        """
        The core gameplay loop method.

        Tri-Track Pipeline (Phase 2):
        ═══════════════════════════════════════════════════════════════
        TRACK A (Blocking — user waits for this):
          1. PARALLEL: Safety pre-screen + Orchestrator intent classification
          2. Short-circuit if input violates safety boundaries
          3. Arc Tracker evaluates for meta-currency
          4. Encounter/hazard injection based on pacing
          5. Narrative Weaver generates prose
          6. State Critic validates prose vs mechanical delta (Bucket I)
          7. PARALLEL: Safety Governor + Consistency Auditor validate output
          8. Patch loop: surgical edits if Auditor flags contradictions
          → Return prose to player

        TRACK B (Non-blocking — future):
          - NPC Engine background moves
          - Simulator pre-computation

        TRACK C (Non-blocking):
          - Chronicler compression + Lore Extraction
        ═══════════════════════════════════════════════════════════════
        """
        print(f"\n--- [SessionDirector] Processing Input from {player_id} ---")

        # Fetch enriched context (current state + recent deltas from Event Ledger)
        context_window = self.state_keeper.get_context_window(location_tag, n=10)
        current_reality = context_window["current_state"]

        # ── TRACK A, PHASE 1: Parallel Input Processing (Bucket A) ─────
        # Safety pre-screen and Orchestrator run simultaneously.
        safety_input_task = self.safety_gov.filter_input(
            player_input, active_player_ids=[player_id]
        )
        orchestrator_task = self.orchestrator.process_player_input(
            player_input, str(context_window)
        )

        safety_input_check, result = await asyncio.gather(
            safety_input_task, orchestrator_task
        )

        # Wrap raw dicts into typed contracts (Bucket G)
        safety_input_verdict = GuardrailVerdict(**safety_input_check)

        # Short-circuit: if the player's raw input violates safety, stop here
        if safety_input_verdict.status == "invalid":
            print(f"[SessionDirector] Input blocked by Safety Governor.")

            self.state_keeper.event_ledger.emit(StateEvent(
                event_type="INPUT_BLOCKED",
                target=player_id,
                delta={"reason": safety_input_verdict.correction_note},
                source_agent="SafetyGovernor",
                location=location_tag
            ))

            return (
                f"[OOC - Safety System]: Your input was flagged before processing. "
                f"{safety_input_verdict.correction_note} "
                f"Please rephrase your action."
            )

        print(f"[SessionDirector] Orchestrator routed and resolved: {result['status']}")

        # ── TRACK A, PHASE 2: Arc Tracking ─────────────────────────────
        arc_note = self.arc_tracker.evaluate_action(player_id, player_input)

        # ── TRACK A, PHASE 3: Encounter/Hazard Injection ───────────────
        injection_note = ""
        if self.encounter_dir.assess_encounter_chance(self.pacing_level):
            self.pacing_level = "tense"
            raw_encounter = self.encounter_dir.generate_encounter(current_reality)

            # Wrap in typed contract (Bucket G)
            encounter = EncounterSpec(**raw_encounter)
            injection_note = f" (GM Note: Injecting Encounter - {encounter.description})"
            print(f"[SessionDirector] Escalating pacing to '{self.pacing_level}' due to encounter.")

            self.state_keeper.event_ledger.emit(StateEvent(
                event_type="PACING_SHIFT",
                target=location_tag,
                delta={"pacing": self.pacing_level, "encounter": encounter.description},
                source_agent="SessionDirector",
                location=location_tag
            ))

        # ── TRACK A, PHASE 4: Narrative Weaving ───────────────────────
        mechanical_delta: Optional[dict] = None  # Track for State Critic

        if result.get("status") == "resolved_via_rules":
            outcome_data = result["outcome"].copy()
            mechanical_delta = outcome_data.copy()  # Preserve for Critic
            if injection_note:
                outcome_data['narrative_effect'] += injection_note
            prose = await self.weaver.render_prose(outcome_data, location_tag)
        elif result.get("status") == "routed_to_forge":
            prose = f"The GM pauses to consult their notes... (Forge Generation Required for: {player_input})"
        else:
             # Just narrative flow
             prose = await self.weaver.render_prose(
                 {"success": True, "narrative_effect": f"Player enacts: {player_input}{injection_note}"},
                 location_tag
             )

        # ── TRACK A, PHASE 5: State Critic (Bucket I) ─────────────────
        # Fast check: does the prose match the mechanical delta?
        if mechanical_delta:
            critic_result = await self.state_critic.validate(prose, mechanical_delta)
            critic_verdict = CriticVerdict(**critic_result)

            if not critic_verdict.is_consistent:
                print(f"[SessionDirector] State Critic flagged mismatch. Re-running Weaver with correction...")
                # Re-run Weaver with the Critic's feedback injected
                corrected_outcome = mechanical_delta.copy()
                corrected_outcome["narrative_effect"] += (
                    f" [CORRECTION: {critic_verdict.mismatch_detail}. "
                    f"You MUST accurately reflect the mechanical outcome.]"
                )
                prose = await self.weaver.render_prose(corrected_outcome, location_tag)

        # ── TRACK A, PHASE 6: Parallel Output Validation (Bucket A) ───
        print("\n[SessionDirector] Running output through Layer III middleware...")
        safety_check, audit_check = await asyncio.gather(
            self.safety_gov.filter_content(prose, active_player_ids=[player_id]),
            self.auditor.audit(prose, current_reality)
        )

        # Wrap in typed contracts (Bucket G)
        safety_verdict = GuardrailVerdict(**safety_check)
        audit_verdict = GuardrailVerdict(**audit_check)

        # Handle safety violations on output
        if safety_verdict.status == "invalid":
            prose += f"\n\n[OOC System Message - Tone/Safety Warning]: {safety_verdict.correction_note}"

        # ── TRACK A, PHASE 7: Patch Loop (Bucket B) ───────────────────
        patch_attempts = 0
        while audit_verdict.status == "invalid" and patch_attempts < self._max_patch_attempts:
            print(f"[SessionDirector] Patch attempt {patch_attempts + 1}/{self._max_patch_attempts}...")
            prose = await self.auditor.patch(prose, audit_check, current_state=current_reality)
            audit_check = await self.auditor.audit(prose, current_reality)
            audit_verdict = GuardrailVerdict(**audit_check)
            patch_attempts += 1

        # If patching exhausted, append a fallback note
        if audit_verdict.status == "invalid":
            prose += f"\n\n[OOC System Message - Logic Contradiction]: {audit_verdict.correction_note}"

        # ── TRACK A COMPLETE — Record turn + fire background tasks ─────
        self.state_keeper.event_ledger.emit(StateEvent(
            event_type="TURN_COMPLETED",
            target=player_id,
            delta={"action": player_input[:100], "outcome": result.get("status", "unknown")},
            source_agent="SessionDirector",
            location=location_tag
        ))

        # Bucket F: Fire Track B/C background tasks (non-blocking)
        self._fire_background_tasks(location_tag, archivist=getattr(self, '_archivist', None))

        return prose
