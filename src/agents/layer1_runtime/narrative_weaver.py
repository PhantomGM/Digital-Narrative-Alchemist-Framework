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
    def __init__(self, llm_model="qwen3.5:397b-cloud"):
        api_key = os.getenv("OLLAMA_API_KEY", "dummy_key")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        
        self.llm = ChatOpenAI(
            model=llm_model, 
            temperature=0.7,
            api_key=api_key,
            base_url=base_url
        )
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
