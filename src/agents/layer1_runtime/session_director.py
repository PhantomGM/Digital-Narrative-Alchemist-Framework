import asyncio
from typing import Dict, Any
from agents.layer1_runtime.simulators import EnvironmentSimulator, EncounterDirector
from agents.layer3_support.consistency_auditor import ConsistencyAuditor
from agents.layer3_support.safety_governor import SafetyGovernor

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
        self.auditor = ConsistencyAuditor()
        self.safety_gov = SafetyGovernor(campaign_tone="Dark Fantasy")
        
        self.current_scene = None
        self.pacing_level = "calm" # calm, tense, combat, climactic
        
    def frame_scene(self, location_tag: str) -> str:
        """Retrieves state and asks the Weaver to set the opening scene."""
        reality = self.state_keeper.get_reality(location_tag)
        print(f"[SessionDirector] Framing Scene: {location_tag}. Pacing: {self.pacing_level}")
        return f"Scene Framed for {location_tag}. Entities present: {reality.get('entities', [])}"

    async def advance_scene(self, player_id: str, player_input: str, location_tag: str) -> str:
        """
        The core gameplay loop method.
        1. Orchestrator parses intent.
        2. Arc Tracker evaluates for meta-currency.
        3. Mechanics resolve (if needed).
        4. Weaver generates output.
        """
        print(f"\n--- [SessionDirector] Processing Input from {player_id} ---")
        current_reality = self.state_keeper.get_reality(location_tag)
        
        # 1 & 3: Orchestrate and Adjudicate
        result = await self.orchestrator.process_player_input(player_input, str(current_reality))
        print(f"[SessionDirector] Orchestrator routed and resolved: {result['status']}")
        
        # 2: Arc Tracking
        arc_note = self.arc_tracker.evaluate_action(player_id, player_input)
        
        # 3.5: Simulator Injections (Obstacles, Weather, Encounters)
        # The Session Director consults its pacing level and the Encounter Director
        injection_note = ""
        if self.encounter_dir.assess_encounter_chance(self.pacing_level):
            self.pacing_level = "tense"
            encounter = self.encounter_dir.generate_encounter(current_reality)
            injection_note = f" (GM Note: Injecting Encounter - {encounter['description']})"
            print(f"[SessionDirector] Escalating pacing to '{self.pacing_level}' due to encounter.")

        # 4: Narrative Weaving
        # We pass the outcome (if rules fired) or the raw input (if scene flow), plus any injected hazards
        if result.get("status") == "resolved_via_rules":
            outcome_data = result["outcome"].copy()
            if injection_note:
                outcome_data['narrative_effect'] += injection_note
            prose = await self.weaver.render_prose(outcome_data, location_tag)
        elif result.get("status") == "routed_to_forge":
            # Just a stub for when the Forge would generate new reality
            prose = f"The GM pauses to consult their notes... (Forge Generation Required for: {player_input})"
        else:
             # Just narrative flow
             prose = await self.weaver.render_prose({"success": True, "narrative_effect": f"Player enacts: {player_input}{injection_note}"}, location_tag)
             
        # 5: Layer III Support Validation
        print("\n[SessionDirector] Running output through Layer III middleware...")
        safety_check = await self.safety_gov.filter_content(prose)
        if safety_check["status"] == "invalid":
            # In a full system we would force the weaver to regenerate. For MVP, we append a GM note.
            prose += f"\n\n[OOC System Message - Tone/Safety Warning]: {safety_check['correction_note']}"
            
        audit_check = await self.auditor.audit(prose, current_reality)
        if audit_check["status"] == "invalid":
            prose += f"\n\n[OOC System Message - Logic Contradiction]: {audit_check['correction_note']}"

        # Placeholder for dynamic state updating based on LLM output
        # self.state_keeper.update_reality...
        
        return prose
