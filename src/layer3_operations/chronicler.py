"""
Chronicler — Background context compression + lore extraction agent.

Periodically compresses the active Event Ledger into dense factual summaries,
extracts discrete LoreChunks for semantic retrieval (Bucket H: Dual-Memory),
commits verbose history to long-term memory (ContinuityArchivist), and
replaces the working context with the compressed version.

Phase 1: Enhancement E5 (Context Compressor)
Phase 2: Bucket H (Dual-Memory — Episodic + Lore RAG)
"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from layer1_core.contracts import LoreChunk


class Chronicler:
    """
    Background agent that runs every N turns to compress the Event Ledger
    and extract discrete, immutable lore facts.

    Phase 1 — Compression:
    1. Pulls all events since the last compression
    2. Summarizes them into dense factual bullet points via LLM
    3. Commits the full verbose history to the ContinuityArchivist

    Phase 2 — Lore Extraction (Bucket H):
    4. Extracts individual LoreChunk records from events
    5. Stores them in a searchable in-memory lore store
    6. These facts never degrade — they're immutable and queryable
    """

    def __init__(self, compression_interval: int = 10):
        self.compression_interval = compression_interval
        self.turn_counter = 0
        self._last_compression_timestamp = 0.0
        self._compressed_summaries: list[str] = []
        self._lore_store: list[LoreChunk] = []  # Bucket H: immutable facts
        self._turn_number = 0  # Global turn counter for lore tagging

        from layer1_core.model_router import model_router
        self.llm = model_router.get_llm("chronicler", temperature=0.0)
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
        recent_events = await event_ledger.get_since(self._last_compression_timestamp)

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
        self._last_compression_timestamp = await event_ledger.get_last_timestamp()
        self.turn_counter = 0

        # 7. Bucket H: Extract discrete lore chunks from the raw events
        lore_chunks = self._extract_lore_chunks(recent_events)
        self._lore_store.extend(lore_chunks)
        print(f"[Chronicler] Extracted {len(lore_chunks)} lore chunks. Total store: {self.lore_count}.")

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

    def _extract_lore_chunks(self, events) -> list[LoreChunk]:
        """
        Bucket H: Extract discrete, immutable LoreChunks from events.

        Instead of relying solely on lossy LLM summarization, this method
        converts raw events into individual factual records that:
        - Never degrade through re-summarization
        - Are searchable by entity_id or location
        - Maintain fine-grained detail (e.g., 'rusty dagger' stays 'rusty dagger')
        """
        chunks = []
        self._turn_number += 1

        for event in events:
            # Determine importance based on event type
            importance_map = {
                "ADD_ENTITY": 3,
                "REMOVE_ENTITY": 4,
                "UPDATE_ENTITY": 2,
                "PACING_SHIFT": 2,
                "SCENE_TRANSITION": 3,
                "TURN_COMPLETED": 1,
                "INPUT_BLOCKED": 1,
            }
            importance = importance_map.get(event.event_type, 2)

            # Build the factual statement from the event delta
            delta_parts = [f"{k}: {v}" for k, v in event.delta.items()]
            fact = f"{event.event_type} on {event.target} — {', '.join(delta_parts)}"

            chunk = LoreChunk(
                fact=fact,
                entity_id=event.target,
                location=event.location,
                importance=importance,
                source_turn=self._turn_number,
            )
            chunks.append(chunk)

        return chunks

    def query_lore(self, entity_id: str = "", location: str = "",
                   min_importance: int = 1) -> list[LoreChunk]:
        """
        Query the lore store for facts matching the given criteria.

        Args:
            entity_id: Filter by entity (empty = all entities)
            location: Filter by location (empty = all locations)
            min_importance: Minimum importance rating (1-5)

        Returns:
            List of matching LoreChunks, ordered by source_turn
        """
        results = self._lore_store

        if entity_id:
            results = [c for c in results if c.entity_id == entity_id]
        if location:
            results = [c for c in results if c.location == location]
        if min_importance > 1:
            results = [c for c in results if c.importance >= min_importance]

        return sorted(results, key=lambda c: c.source_turn)

    @property
    def lore_count(self) -> int:
        """Number of lore chunks stored."""
        return len(self._lore_store)
