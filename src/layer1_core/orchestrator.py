import json
import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Define the expected JSON output structure for the router
class RouteDecision(BaseModel):
    workflow: str = Field(description="The chosen workflow: 'scene_flow', 'mechanics_required', or 'generation_event'")
    reasoning: str = Field(description="Brief explanation of why this workflow was chosen")
    target_skill: Optional[str] = Field(description="The specific skill or stat to roll if mechanics_required is chosen")

class Orchestrator:
    """
    The master routing hub for the DNA system.
    Sequences agent calls, resolves conflicts, and acts as the traffic cop.
    """
    def __init__(self):
        self.active_agents = {}
        self.ruleset_cartridge = None
        
        from layer1_core.model_router import model_router
        self.llm = model_router.get_llm("orchestrator", temperature=0.1)
        
        self.parser = JsonOutputParser(pydantic_object=RouteDecision)
        
        self.router_prompt = PromptTemplate(
            template="""You are the Orchestrator, the master routing hub for an AI Game Master in a TTRPG.
Your job is to analyze the Player Input and determine which workflow to trigger.

Available Workflows:
1. 'scene_flow': The player takes a narrative action with a relatively certain outcome (e.g., talking to an NPC, walking into a room).
2. 'mechanics_required': The player attempts an action with a chance of failure, requiring the game rules to arbitrate (e.g., attacking, lying, climbing a sheer cliff).
3. 'generation_event': The player asks about or interacts with something that hasn't been created yet, requiring the Procedural Forge to create new world content (e.g., "What's the name of this town?", "I look for a blacksmith").

Player Input: {player_input}
Current Scene Context: {scene_context}

{format_instructions}
""",
            input_variables=["player_input", "scene_context"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
    def load_ruleset(self, ruleset_module: Any):
        """Hot-swaps the Layer IV Game System Arbiter."""
        self.ruleset_cartridge = ruleset_module
        print(f"Loaded ruleset: {self.ruleset_cartridge.system_name}")
        
    async def process_player_input(self, input_data: str, scene_context: str = "Tavern") -> dict:
        """Routes input through the layers based on the selected workflow using the LLM."""
        print(f"[Orchestrator] Analyzing player input: '{input_data}'")
        
        # Build the chain
        chain = self.router_prompt | self.llm | self.parser
        
        try:
            decision = await chain.ainvoke({"player_input": input_data, "scene_context": scene_context})
        except Exception as e:
            print(f"[Orchestrator] Error parsing LLM response: {e}")
            return {"status": "error", "message": str(e)}
        
        print(f"[Orchestrator] LLM Decision logic: {decision.get('reasoning')}")
        print(f"[Orchestrator] Routing to: {decision.get('workflow')}")
        
        workflow = decision.get("workflow")
        if workflow == "mechanics_required" and self.ruleset_cartridge:
             outcome = self.ruleset_cartridge.resolve_action(input_data)
             return {"status": "resolved_via_rules", "outcome": outcome}
        elif workflow == "generation_event":
             return {"status": "routed_to_forge"}
        else:
             return {"status": "routed_to_narrative"}
