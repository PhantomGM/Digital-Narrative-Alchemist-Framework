import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class NarrativeWeaver:
    """
    Translates mechanical outcomes and state changes into vivid, player-facing prose.
    It *describes* truth but does not author new mechanical facts.
    """
    def __init__(self):
        from layer1_core.model_router import model_router
        self.llm = model_router.get_llm("narrative_weaver", temperature=0.7)
        self.parser = StrOutputParser()
        
        self.weaver_prompt = PromptTemplate(
            template="""You are the Narrative Weaver for a TTRPG AI Game Master.
Your job is to take raw mechanical outcomes and world state updates, and weave them into 
vivid, immersive, second-person prose for the players.

DO NOT invent new mechanical consequences. Only describe what has been passed to you.

Scene Context: {context}
Mechanical Outcome: {mechanical_outcome}

Write the narrative response in one cohesive paragraph:
""",
            input_variables=["context", "mechanical_outcome"]
        )

    async def render_prose(self, mechanical_outcome: dict, context: str) -> str:
        """Takes a mechanical resolution and returns LLM-generated descriptive prose."""
        print(f"[NarrativeWeaver] Passing outcome to LLM...")
        
        chain = self.weaver_prompt | self.llm | self.parser
        woven_prose = await chain.ainvoke({
            "context": context,
            "mechanical_outcome": json.dumps(mechanical_outcome)
        })
            
        return woven_prose
