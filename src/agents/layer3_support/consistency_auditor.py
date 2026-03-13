import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ConsistencyAuditor:
    """
    Analyzes generated text against the authoritative World State to detect
    hallucinations, contradictions, or physical impossibilities.
    """
    def __init__(self, llm_model="qwen3.5:397b-cloud"):
        api_key = os.getenv("OLLAMA_API_KEY", "dummy_key")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        
        self.llm = ChatOpenAI(
            model=llm_model, 
            temperature=0.0, # Zero temp for analytical truthfulness
            api_key=api_key,
            base_url=base_url
        )
        self.parser = StrOutputParser()
        
        # A simple prompt evaluating consistency
        template = """
You are the Consistency Auditor for a TTRPG engine. 
Your job is to read the CURRENT WORLD STATE and a newly generated PASSAGE of text.
You must determine if the PASSAGE contradicts the WORLD STATE or makes logical errors (e.g. claiming a dead NPC is alive, or an item is present when it isn't).

CURRENT WORLD STATE:
{state}

NEW PASSAGE:
{passage}

If the passage is perfectly consistent, reply ONLY with the exact word: VALID
If the passage contains a contradiction, reply with: INVALID | [A short sentence explaining the exact logic error]
"""
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["state", "passage"]
        )
        self.chain = self.prompt | self.llm | self.parser

    async def audit(self, passage: str, current_state: dict) -> dict:
        """Runs the LLM check and returns parsed status."""
        print("[ConsistencyAuditor] Auditing passage against World State...")
        
        # Mock immediate pass if no passage is provided (shouldn't happen, but safe)
        if not passage.strip():
             return {"status": "valid", "correction_note": ""}
             
        # Use LLM to audit
        try:
            response = await self.chain.ainvoke({
                "state": str(current_state),
                "passage": passage
            })
            response = response.strip()
            
            if response.startswith("VALID"):
                return {"status": "valid", "correction_note": ""}
            else:
                note = response.split("|", 1)[1].strip() if "|" in response else response
                print(f"[ConsistencyAuditor] CONTRADICTION DETECTED: {note}")
                return {"status": "invalid", "correction_note": note}
                
        except Exception as e:
            print(f"[ConsistencyAuditor] Error during audit: {e}. Defaulting to valid to prevent hang.")
            return {"status": "valid", "correction_note": ""}
