"""
Chronicler — Background context compression agent for the DNA Framework.

Periodically compresses the active Event Ledger into dense factual summaries,
commits verbose history to long-term memory (ContinuityArchivist), and
replaces the working context with the compressed version.

This prevents context window degradation over long sessions (4+ hours)
and manages token costs by ensuring the Narrative Weaver always operates
with high token efficiency.

Solves: Enhancement E5 (Context Compressor)
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class Chronicler:
    """
    Background agent that runs every N turns to compress the Event Ledger.

    1. Pulls all events since the last compression
    2. Summarizes them into dense factual bullet points via LLM
    3. Commits the full verbose history to the ContinuityArchivist (Layer 2)
    4. Provides the compressed summary for the Session Director's working context
    """

    def __init__(self, compression_interval: int = 10, llm_model: str = "qwen3.5:397b-cloud"):
        self.compression_interval = compression_interval
        self.turn_counter = 0
        self._last_compression_timestamp = 0.0
        self._compressed_summaries: list[str] = []

        api_key = os.getenv("OLLAMA_API_KEY", "dummy_key")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.0,  # Zero temp for factual precision
            api_key=api_key,
            base_url=base_url
        )
        self.parser = StrOutputParser()

        self.compress_prompt = PromptTemplate(
            template="""You are a precise historian summarizing recent events in a TTRPG session.

Below is a chronological log of STATE CHANGES that occurred during the last few turns
of gameplay. Your job is to compress this into a dense, factual summary using bullet points.

RULES:
- Include ONLY facts: who did what, what changed, what was created/destroyed.
- Do NOT add flavor text or narrative embellishment.
- Use present tense for current states, past tense for completed actions.
- Keep each bullet point to one sentence maximum.
- Order bullets chronologically.

STATE CHANGE LOG:
{event_log}

CURRENT WORLD STATE SNAPSHOT:
{world_state}

Compressed summary (bullet points only):
""",
            input_variables=["event_log", "world_state"]
        )
        self.chain = self.compress_prompt | self.llm | self.parser

    def tick(self) -> None:
        """Increment the turn counter. Called at the end of each advance_scene()."""
        self.turn_counter += 1

    def should_compress(self) -> bool:
        """Returns True when enough turns have passed to warrant compression."""
        return self.turn_counter >= self.compression_interval

    async def compress(self, event_ledger, state_keeper, archivist=None) -> str:
        """
        Compresses recent events and optionally commits verbose history
        to long-term memory.

        Args:
            event_ledger: The EventLedger instance
            state_keeper: The WorldStateKeeper instance
            archivist: Optional ContinuityArchivist for long-term storage

        Returns:
            The compressed summary string
        """
        print(f"\n[Chronicler] Compressing {self.turn_counter} turns of state changes...")

        # 1. Pull events since last compression
        recent_events = event_ledger.get_since(self._last_compression_timestamp)

        if not recent_events:
            print("[Chronicler] No new events to compress.")
            self.turn_counter = 0
            return ""

        # 2. Render events as text for the LLM
        event_log = "\n".join(e.to_context_string() for e in recent_events)

        # 3. Get current world state snapshot
        world_snapshot = str(state_keeper.world_metadata)

        # 4. Compress via LLM
        try:
            compressed = await self.chain.ainvoke({
                "event_log": event_log,
                "world_state": world_snapshot
            })
            compressed = compressed.strip()
        except Exception as e:
            print(f"[Chronicler] Compression failed: {e}. Skipping this cycle.")
            self.turn_counter = 0
            return ""

        # 5. Archive the verbose log to long-term memory
        if archivist:
            verbose_entry = (
                f"=== Session Chronicle (Turns {self.turn_counter}) ===\n"
                f"{event_log}\n"
                f"=== Compressed Summary ===\n"
                f"{compressed}\n"
                f"==========================================="
            )
            archivist.save_scene(verbose_entry)
            print("[Chronicler] Verbose history committed to ContinuityArchivist.")

        # 6. Store the compressed summary and reset
        self._compressed_summaries.append(compressed)
        self._last_compression_timestamp = event_ledger.last_timestamp
        self.turn_counter = 0

        print(f"[Chronicler] Compression complete. Summary length: {len(compressed)} chars.")
        return compressed

    def get_session_context(self) -> str:
        """
        Returns all compressed summaries from this session as a single
        context block for injection into agent prompts.
        """
        if not self._compressed_summaries:
            return "No prior session history compressed yet."

        blocks = []
        for i, summary in enumerate(self._compressed_summaries, 1):
            blocks.append(f"--- Chronicle Block {i} ---\n{summary}")

        return "\n\n".join(blocks)
