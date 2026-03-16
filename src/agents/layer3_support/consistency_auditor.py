import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ConsistencyAuditor:
    """
    Analyzes generated text against the authoritative World State to detect
    hallucinations, contradictions, or physical impossibilities.

    Enhanced with the "Patch Agent" pattern: instead of forcing full regeneration
    on failure, the Auditor can surgically edit only the offending sentence(s).
    This guarantees forward momentum and eliminates infinite rollback loops.
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

        # Audit prompt — now requests the offending text when invalid
        audit_template = """
You are the Consistency Auditor for a TTRPG engine.
Your job is to read the CURRENT WORLD STATE and a newly generated PASSAGE of text.
You must determine if the PASSAGE contradicts the WORLD STATE or makes logical errors (e.g. claiming a dead NPC is alive, or an item is present when it isn't).

CURRENT WORLD STATE:
{state}

NEW PASSAGE:
{passage}

If the passage is perfectly consistent, reply ONLY with the exact word: VALID
If the passage contains a contradiction, reply with this exact format:
INVALID | [The exact sentence from the passage that is wrong] | [A short explanation of the error]
"""
        self.audit_prompt = PromptTemplate(
            template=audit_template,
            input_variables=["state", "passage"]
        )
        self.audit_chain = self.audit_prompt | self.llm | self.parser

        # Patch prompt — surgically rewrites only the offending sentence
        patch_template = """
You are a precise text editor for a TTRPG narrative engine.
You have been given a FULL PASSAGE and told that ONE SPECIFIC SENTENCE contains an error.
Your job is to rewrite ONLY that sentence so it no longer contradicts the WORLD STATE.
Keep the same tone, style, and narrative flow. Change as few words as possible.

WORLD STATE:
{state}

FULL PASSAGE:
{passage}

OFFENDING SENTENCE:
{offending_text}

ERROR EXPLANATION:
{error_note}

Output the COMPLETE corrected passage (with the fixed sentence in place). Do not add commentary.
"""
        self.patch_prompt = PromptTemplate(
            template=patch_template,
            input_variables=["state", "passage", "offending_text", "error_note"]
        )
        self.patch_chain = self.patch_prompt | self.llm | self.parser

    async def audit(self, passage: str, current_state: dict) -> dict:
        """
        Runs the LLM consistency check.

        Returns:
            - status: "valid" or "invalid"
            - correction_note: explanation of the error (empty if valid)
            - offending_text: the exact sentence that is wrong (empty if valid)
        """
        print("[ConsistencyAuditor] Auditing passage against World State...")

        if not passage.strip():
             return {"status": "valid", "correction_note": "", "offending_text": ""}

        try:
            response = await self.audit_chain.ainvoke({
                "state": str(current_state),
                "passage": passage
            })
            response = response.strip()

            if response.startswith("VALID"):
                return {"status": "valid", "correction_note": "", "offending_text": ""}
            else:
                parts = response.split("|")
                if len(parts) >= 3:
                    offending = parts[1].strip()
                    note = parts[2].strip()
                elif len(parts) == 2:
                    offending = parts[1].strip()
                    note = offending
                else:
                    offending = ""
                    note = response

                print(f"[ConsistencyAuditor] CONTRADICTION DETECTED: {note}")
                return {"status": "invalid", "correction_note": note, "offending_text": offending}

        except Exception as e:
            print(f"[ConsistencyAuditor] Error during audit: {e}. Defaulting to valid to prevent hang.")
            return {"status": "valid", "correction_note": "", "offending_text": ""}

    async def patch(self, prose: str, audit_result: dict, current_state: dict = None) -> str:
        """
        Surgically edits only the offending sentence in the prose.

        Instead of forcing the Narrative Weaver to regenerate the entire response,
        this method rewrites only the problematic sentence while preserving the
        surrounding narrative flow.

        Args:
            prose: The full generated prose containing the error
            audit_result: The dict returned by audit() with offending_text and correction_note
            current_state: The current world state dict for context

        Returns:
            The corrected prose string
        """
        offending = audit_result.get("offending_text", "")
        note = audit_result.get("correction_note", "")

        if not offending:
            # No specific sentence identified — fall back to appending a note
            print("[ConsistencyAuditor] No offending text identified, appending correction note.")
            return prose + f"\n\n[OOC System Message - Logic Contradiction]: {note}"

        print(f"[ConsistencyAuditor] Patching offending sentence: '{offending[:60]}...'")

        try:
            patched = await self.patch_chain.ainvoke({
                "state": str(current_state or {}),
                "passage": prose,
                "offending_text": offending,
                "error_note": note
            })
            return patched.strip()

        except Exception as e:
            print(f"[ConsistencyAuditor] Patch failed: {e}. Returning original with note appended.")
            return prose + f"\n\n[OOC System Message - Logic Contradiction]: {note}"

