"""
State Critic — Fast circuit-breaker agent for narrative/mechanical consistency.

Solves: Phase 2 Enhancement — Narrative Weaver ignoring mechanical truth
Enhancement: Bucket I (State Critic Circuit Breaker)

Placed directly after the Narrative Weaver and BEFORE the Safety Governor
and Consistency Auditor. Uses a fast, low-parameter prompt (temperature=0)
to verify that the generated prose faithfully represents the Arbiter's
mechanical outcome.

If the Critic flags a mismatch, the Session Director re-runs the Weaver
once with the Critic's feedback injected as a correction constraint.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class StateCritic:
    """
    A lightweight, high-speed validation agent.

    Unlike the Consistency Auditor (which checks prose vs. world state
    for hallucinations), the State Critic specifically checks whether
    prose contradicts the mechanical delta from the Arbiter.

    Example catch:
        Arbiter says: {"success": True, "damage": 8}
        Weaver writes: "Your blade bounces harmlessly off the armor."
        Critic: MISMATCH — prose describes failure but math says success.
    """

    def __init__(self, llm_model: str = "qwen3.5:397b-cloud"):
        api_key = os.getenv("OLLAMA_API_KEY", "dummy_key")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.0,
            api_key=api_key,
            base_url=base_url,
            max_tokens=100,  # Keep it fast — boolean answer only
        )
        self.parser = StrOutputParser()

        self.critic_prompt = PromptTemplate(
            template="""You are the State Critic for a TTRPG AI system.
You verify that the NARRATIVE OUTPUT faithfully represents the MECHANICAL RESULT.

MECHANICAL RESULT (ground truth — this is what actually happened):
{mechanical_delta}

NARRATIVE OUTPUT (what was written for the player):
{prose}

Does the narrative contradict or misrepresent the mechanical result?
Consider: success/failure alignment, damage amounts, status effects, and outcomes.

If the narrative MATCHES the mechanical result, reply ONLY: MATCH
If the narrative CONTRADICTS the mechanical result, reply:
MISMATCH | [One sentence explaining what the prose got wrong]
""",
            input_variables=["mechanical_delta", "prose"]
        )
        self.chain = self.critic_prompt | self.llm | self.parser

    async def validate(self, prose: str, mechanical_delta: dict) -> dict:
        """
        Checks whether generated prose faithfully represents the mechanical outcome.

        Args:
            prose: The Narrative Weaver's output
            mechanical_delta: The Arbiter's raw mechanical result dict

        Returns:
            {
                "is_consistent": bool,
                "mismatch_detail": str  # empty if consistent
            }
        """
        print("[StateCritic] Validating prose against mechanical truth...")

        if not prose.strip() or not mechanical_delta:
            return {"is_consistent": True, "mismatch_detail": ""}

        try:
            response = await self.chain.ainvoke({
                "mechanical_delta": str(mechanical_delta),
                "prose": prose
            })
            response = response.strip()

            if response.startswith("MATCH"):
                print("[StateCritic] ✓ Prose matches mechanical outcome.")
                return {"is_consistent": True, "mismatch_detail": ""}
            else:
                detail = response.split("|", 1)[1].strip() if "|" in response else response
                print(f"[StateCritic] ✗ MISMATCH: {detail}")
                return {"is_consistent": False, "mismatch_detail": detail}

        except Exception as e:
            print(f"[StateCritic] Validation error: {e}. Defaulting to consistent.")
            return {"is_consistent": True, "mismatch_detail": ""}
