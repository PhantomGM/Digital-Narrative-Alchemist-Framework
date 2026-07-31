import asyncio
from typing import Dict, Any, Optional
from layer1_core.simulators import EnvironmentSimulator, EncounterDirector
from layer3_operations.consistency_auditor import ConsistencyAuditor
from layer3_operations.safety_governor import SafetyGovernor
from layer3_operations.player_profiles import PlayerProfileManager
from layer3_operations.chronicler import Chronicler
from layer3_operations.wiki_bridge import WikiBridge, normalize_entity_id
from layer3_operations.state_critic import StateCritic
from common.paths import PathConfigError, resolve_wiki_path
from layer2_narrative.event_ledger import EventLedger, StateEvent
from layer1_core.contracts import (
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
        self.chronicler = Chronicler(compression_interval=10)

        # --- Wiki RAG Integration (optional) ---
        # Configured via OBSIDIAN_WIKI_PATH. This used to fall back to a
        # hardcoded WSL path, which does not exist on Windows — so the exists()
        # guard below silently skipped ingestion and the session ran with no
        # wiki lore at all, reporting nothing. It now always says why it is off.
        self.wiki_bridge = None
        try:
            wiki_path = resolve_wiki_path(required=False)
        except PathConfigError as exc:
            wiki_path = None
            print(f"[SessionDirector] Wiki RAG disabled — {exc}")

        if wiki_path:
            self.wiki_bridge = WikiBridge(wiki_path)
            wiki_lore = self.wiki_bridge.ingest_wiki()
            self.chronicler.add_external_lore(wiki_lore)
            print(f"[SessionDirector] Wiki RAG enabled: {len(wiki_lore)} lore chunks from {wiki_path}")
        else:
            print("[SessionDirector] Wiki RAG disabled — OBSIDIAN_WIKI_PATH is not set.")
        # ----------------------------

        self.auditor = ConsistencyAuditor()
        self.safety_gov = SafetyGovernor(campaign_tone="Dark Fantasy", profile_manager=self.profile_manager)
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
        context_window = await self.state_keeper.get_context_window(location_tag, n=10)
        current_reality = context_window["current_state"]

        # --- Wiki RAG Query ---
        # Query lore relevant to the current location or player input
        # For now, we search for the location name and any entities in the reality
        search_terms = [location_tag] + list(current_reality.get("entities", {}).keys())
        relevant_lore = []
        seen_facts = set()
        for term in search_terms:
            # query_lore matches entity_id exactly, so the term must be reduced
            # the same way ingestion reduces a page title. The old
            # lower()/replace(" ", "_") missed every hyphenated name — an
            # "Arch-Librarian Kaelen" page was ingested but never retrievable.
            # The raw and legacy forms are still tried, because event-sourced
            # chunks store their target verbatim.
            for key in {normalize_entity_id(term), term.lower().replace(" ", "_"), term}:
                if not key:
                    continue
                for chunk in self.chronicler.query_lore(entity_id=key):
                    if chunk.fact not in seen_facts:
                        seen_facts.add(chunk.fact)
                        relevant_lore.append(chunk)


        # Also do a broad search if no specific entities matched (stub for semantic search)
        if not relevant_lore:
             # Just pull the most important facts for now as a fallback
             relevant_lore = self.chronicler.query_lore(min_importance=3)
        
        lore_context = "\n".join([f"- {c.fact}" for c in relevant_lore[:5]])
        context_window["world_lore"] = lore_context
        # ----------------------

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

            await self.state_keeper.event_ledger.emit(StateEvent(
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

            await self.state_keeper.event_ledger.emit(StateEvent(
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
            prose = await self.weaver.render_prose(outcome_data, str(context_window))
        elif result.get("status") == "routed_to_forge":
            prose = f"The GM pauses to consult their notes... (Forge Generation Required for: {player_input})"
        else:
             # Just narrative flow
             prose = await self.weaver.render_prose(
                 {"success": True, "narrative_effect": f"Player enacts: {player_input}{injection_note}"},
                 str(context_window)
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
            self.auditor.audit(prose, context_window)
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
            prose = await self.auditor.patch(prose, audit_check, current_state=context_window)
            audit_check = await self.auditor.audit(prose, context_window)
            audit_verdict = GuardrailVerdict(**audit_check)
            patch_attempts += 1

        # If patching exhausted, append a fallback note
        if audit_verdict.status == "invalid":
            prose += f"\n\n[OOC System Message - Logic Contradiction]: {audit_verdict.correction_note}"

        # ── TRACK A COMPLETE — Record turn + fire background tasks ─────
        await self.state_keeper.event_ledger.emit(StateEvent(
            event_type="TURN_COMPLETED",
            target=player_id,
            delta={"action": player_input[:100], "outcome": result.get("status", "unknown")},
            source_agent="SessionDirector",
            location=location_tag
        ))

        # Bucket F: Fire Track B/C background tasks (non-blocking)
        self._fire_background_tasks(location_tag, archivist=getattr(self, '_archivist', None))

        return prose
