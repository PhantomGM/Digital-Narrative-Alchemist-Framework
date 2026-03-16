import asyncio
from typing import Dict, Any
from agents.layer1_runtime.simulators import EnvironmentSimulator, EncounterDirector
from agents.layer3_support.consistency_auditor import ConsistencyAuditor
from agents.layer3_support.safety_governor import SafetyGovernor
from agents.layer3_support.player_profiles import PlayerProfileManager
from agents.layer3_support.chronicler import Chronicler
from core.event_ledger import EventLedger, StateEvent

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

    Enhanced with:
    - Parallel dispatch (Bucket A): Safety + Orchestrator run simultaneously
    - Patch-based auditing (Bucket B): Surgical sentence editing instead of regen
    - Event Ledger context (Bucket C): All agents share the same state deltas
    - Chronicler integration (Bucket E): Periodic context compression
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

        self.current_scene = None
        self.pacing_level = "calm" # calm, tense, combat, climactic
        self._max_patch_attempts = 2  # Bucket B: cap on surgical edits

    def frame_scene(self, location_tag: str) -> str:
        """Retrieves state and asks the Weaver to set the opening scene."""
        reality = self.state_keeper.get_reality(location_tag)
        print(f"[SessionDirector] Framing Scene: {location_tag}. Pacing: {self.pacing_level}")
        return f"Scene Framed for {location_tag}. Entities present: {reality.get('entities', [])}"

    async def advance_scene(self, player_id: str, player_input: str, location_tag: str) -> str:
        """
        The core gameplay loop method.

        Pipeline (with parallelization):
        1. PARALLEL: Safety pre-screen + Orchestrator intent classification
        2. Short-circuit if input violates safety boundaries
        3. Arc Tracker evaluates for meta-currency
        4. Encounter/hazard injection based on pacing
        5. Narrative Weaver generates prose
        6. PARALLEL: Safety Governor + Consistency Auditor validate output
        7. Patch loop: surgical edits if Auditor flags contradictions
        8. Chronicler tick (async compression every N turns)
        """
        print(f"\n--- [SessionDirector] Processing Input from {player_id} ---")

        # Fetch enriched context (current state + recent deltas from Event Ledger)
        context_window = self.state_keeper.get_context_window(location_tag, n=10)
        current_reality = context_window["current_state"]

        # ── PHASE 1: Parallel Input Processing (Bucket A) ──────────────
        # Safety pre-screen and Orchestrator run simultaneously.
        # If safety flags the input itself, we short-circuit immediately.
        safety_input_task = self.safety_gov.filter_input(
            player_input, active_player_ids=[player_id]
        )
        orchestrator_task = self.orchestrator.process_player_input(
            player_input, str(context_window)
        )

        safety_input_check, result = await asyncio.gather(
            safety_input_task, orchestrator_task
        )

        # Short-circuit: if the player's raw input violates safety, stop here
        if safety_input_check["status"] == "invalid":
            print(f"[SessionDirector] Input blocked by Safety Governor.")

            # Emit a ledger event for the blocked input
            self.state_keeper.event_ledger.emit(StateEvent(
                event_type="INPUT_BLOCKED",
                target=player_id,
                delta={"reason": safety_input_check["correction_note"]},
                source_agent="SafetyGovernor",
                location=location_tag
            ))

            return (
                f"[OOC - Safety System]: Your input was flagged before processing. "
                f"{safety_input_check['correction_note']} "
                f"Please rephrase your action."
            )

        print(f"[SessionDirector] Orchestrator routed and resolved: {result['status']}")

        # ── PHASE 2: Arc Tracking ──────────────────────────────────────
        arc_note = self.arc_tracker.evaluate_action(player_id, player_input)

        # ── PHASE 3: Encounter/Hazard Injection ────────────────────────
        injection_note = ""
        if self.encounter_dir.assess_encounter_chance(self.pacing_level):
            self.pacing_level = "tense"
            encounter = self.encounter_dir.generate_encounter(current_reality)
            injection_note = f" (GM Note: Injecting Encounter - {encounter['description']})"
            print(f"[SessionDirector] Escalating pacing to '{self.pacing_level}' due to encounter.")

            # Emit pacing shift to the Event Ledger
            self.state_keeper.event_ledger.emit(StateEvent(
                event_type="PACING_SHIFT",
                target=location_tag,
                delta={"pacing": self.pacing_level, "encounter": encounter["description"]},
                source_agent="SessionDirector",
                location=location_tag
            ))

        # ── PHASE 4: Narrative Weaving ─────────────────────────────────
        if result.get("status") == "resolved_via_rules":
            outcome_data = result["outcome"].copy()
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

        # ── PHASE 5: Parallel Output Validation (Bucket A) ────────────
        # Safety Governor and Consistency Auditor run simultaneously on the output.
        print("\n[SessionDirector] Running output through Layer III middleware...")
        safety_check, audit_check = await asyncio.gather(
            self.safety_gov.filter_content(prose, active_player_ids=[player_id]),
            self.auditor.audit(prose, current_reality)
        )

        # Handle safety violations on output
        if safety_check["status"] == "invalid":
            prose += f"\n\n[OOC System Message - Tone/Safety Warning]: {safety_check['correction_note']}"

        # ── PHASE 6: Patch Loop (Bucket B) ─────────────────────────────
        # Instead of appending OOC messages, surgically edit the offending sentence.
        patch_attempts = 0
        while audit_check["status"] == "invalid" and patch_attempts < self._max_patch_attempts:
            print(f"[SessionDirector] Patch attempt {patch_attempts + 1}/{self._max_patch_attempts}...")
            prose = await self.auditor.patch(prose, audit_check, current_state=current_reality)
            audit_check = await self.auditor.audit(prose, current_reality)
            patch_attempts += 1

        # If patching exhausted, append a fallback note
        if audit_check["status"] == "invalid":
            prose += f"\n\n[OOC System Message - Logic Contradiction]: {audit_check['correction_note']}"

        # ── PHASE 7: Chronicler Tick (Bucket E) ────────────────────────
        # Record the turn event, then check if compression is needed.
        self.state_keeper.event_ledger.emit(StateEvent(
            event_type="TURN_COMPLETED",
            target=player_id,
            delta={"action": player_input[:100], "outcome": result.get("status", "unknown")},
            source_agent="SessionDirector",
            location=location_tag
        ))

        self.chronicler.tick()
        if self.chronicler.should_compress():
            # Run compression asynchronously — don't block the player response
            archivist = getattr(self, '_archivist', None)
            asyncio.create_task(
                self.chronicler.compress(
                    self.state_keeper.event_ledger,
                    self.state_keeper,
                    archivist
                )
            )

        return prose
