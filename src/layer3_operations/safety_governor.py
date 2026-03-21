import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class SafetyGovernor:
    """
    Enforces campaign boundaries (Lines & Veils) and stylistic tone.
    Filters player input and generated outputs to maintain cohesion and safety.
    """
    def __init__(self, campaign_tone="Dark Fantasy", lines_and_veils=None, profile_manager=None):
        self.campaign_tone = campaign_tone
        self.lines_and_veils = lines_and_veils or "No specific triggers listed. Maintain general PG-13 safety."
        self.profile_manager = profile_manager
        
        from layer1_core.model_router import model_router
        self.llm = model_router.get_llm("safety_governor", temperature=0.0)
        self.parser = StrOutputParser()
        
        template = """
You are the Tone and Safety Governor for a TTRPG framework.
You must evaluate if the following PASSAGE respects the CAMPAIGN TONE and SAFETY BOUNDARIES.

CAMPAIGN TONE: {tone}
SAFETY BOUNDARIES (Lines & Veils): {boundaries}

NEW PASSAGE:
{passage}

Does this passage violate the tone (e.g., adding silly elements to a dark game) or cross a safety boundary?
If it is completely fine, reply ONLY with: VALID
If it is a tone break or safety violation, reply with: INVALID | [A short sentence explaining what needs to be rewritten]
"""
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["tone", "boundaries", "passage"]
        )
        self.chain = self.prompt | self.llm | self.parser

    async def filter_content(self, passage: str, active_player_ids: list = None) -> dict:
        """Parses the text through the safety and tone filter."""
        print(f"[SafetyGovernor] Evaluating content against '{self.campaign_tone}' tone...")
        
        if not passage.strip():
             return {"status": "valid", "correction_note": ""}
             
        # Dynamic boundary extraction
        current_boundaries = self.lines_and_veils
        if self.profile_manager and active_player_ids:
            current_boundaries = self.profile_manager.aggregate_safety_boundaries(active_player_ids)
             
        try:
            response = await self.chain.ainvoke({
                "tone": self.campaign_tone,
                "boundaries": current_boundaries,
                "passage": passage
            })
            response = response.strip()
            
            if response.startswith("VALID"):
                return {"status": "valid", "correction_note": ""}
            else:
                note = response.split("|", 1)[1].strip() if "|" in response else response
                print(f"[SafetyGovernor] TONE OR SAFETY VIOLATION: {note}")
                return {"status": "invalid", "correction_note": note}
                
        except Exception as e:
            print(f"[SafetyGovernor] Error during evaluation: {e}. Defaulting to valid to prevent hang.")
            return {"status": "valid", "correction_note": ""}

    async def filter_input(self, player_input: str, active_player_ids: list = None) -> dict:
        """
        Pre-screens raw player input for safety boundary violations BEFORE
        it enters the pipeline. This runs in parallel with the Orchestrator's
        intent classification, enabling early short-circuit if the input
        itself is problematic.

        This is a faster check than filter_content() since player inputs are
        typically much shorter than generated prose.
        """
        print(f"[SafetyGovernor] Pre-screening player input for safety violations...")

        if not player_input.strip():
            return {"status": "valid", "correction_note": ""}

        # Dynamic boundary extraction
        current_boundaries = self.lines_and_veils
        if self.profile_manager and active_player_ids:
            current_boundaries = self.profile_manager.aggregate_safety_boundaries(active_player_ids)

        try:
            response = await self.chain.ainvoke({
                "tone": self.campaign_tone,
                "boundaries": current_boundaries,
                "passage": player_input
            })
            response = response.strip()

            if response.startswith("VALID"):
                return {"status": "valid", "correction_note": ""}
            else:
                note = response.split("|", 1)[1].strip() if "|" in response else response
                print(f"[SafetyGovernor] INPUT SAFETY VIOLATION: {note}")
                return {"status": "invalid", "correction_note": note}

        except Exception as e:
            print(f"[SafetyGovernor] Input pre-screen error: {e}. Defaulting to valid.")
            return {"status": "valid", "correction_note": ""}
