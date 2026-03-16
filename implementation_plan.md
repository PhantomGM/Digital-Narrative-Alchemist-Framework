# Digital Narrative Alchemist (DNA) Framework Plan

This document outlines the architecture for the "Digital Narrative Alchemist" (DNA) multi-agent system, based on the provided architecture synthesis document. The system serves as a **genotype-to-phenotype content engine** wrapped in a multi-agent orchestration layer.

## System Architecture

The core philosophy is **System Agnosticism**. The foundational AI handles world simulation and narrative flow, while rules adjudication is handled via modular sub-agent cartridges (Layer IV).

The architecture is divided into four distinct operational layers encompassing 29 normalized agents.

### Layer I: Core Runtime Intelligence

These agents form the active, real-time "brain" of the AI GM.

1. **Orchestrator**: Master routing hub and traffic cop.
2. **Session Director**: Controls structural pacing and scene framing.
3. **World State Keeper**: Tracks the authoritative present reality.
4. **Continuity Archivist**: Stores and retrieves past scenes to maintain canon.
5. **Narrative Weaver**: Translates state changes into vivid prose for players.
6. **NPC Actor Engine**: Drives NPC behavior and tactical choices.
7. **NPC Persona Engine**: Dictates how NPCs express themselves.
8. **Faction & Culture Simulator**: Runs macro-social actors.
9. **Environment Simulator**: Manages physical space and hazards.
10. **Encounter & Challenge Director**: Builds non-combat challenges.
11. **Character Arc Tracker**: Monitors PC personal arcs.

### Layer II: DNA / PCG Substrate

The generation engine that translates building blocks into the world.

12. **DNA Registry**: Authoritative database for typed DNA strings.
13. **DNA Decoder & Phenotype Synthesizer**: Translates DNA strings into traits.
14. **Inheritance & Constraint Engine**: Resolves parent-child trait inheritance.
15. **Procedural Forge**: Synthesizes new world elements.
16. **Lore & History Atlas**: Maintains deep canon.
17. **Historiography Engine**: Generates biased history.
18. **Magic & Cosmology Engine**: Defines supernatural laws.
19. **Economy & Logistics Simulator**: Simulates trade and scarcity.

### Layer III: Support / Reliability Layer

Guardrails ensuring safe, logical operation.

20. **Safety Governor**: Enforces boundaries and campaign tone.
21. **Consistency Auditor**: Detects hallucinations and logic contradictions.
22. **Session Pulse Monitor**: Analyzes pacing and engagement.
23. **Table Operations Manager**: Formats output for humans.
24. **Campaign Architect**: Pre-session assistant for scaffolding.

### Layer IV: Modular Game-System Layer

A swappable cartridge tailored to specific TTRPG rulesets (e.g., D&D 5e).

25. **Game System Arbiter**: The system-specific referee.
26. **Character Model Adapter**: Translates narrative intent into game stats.
27. **Combat Resolver**: Handles combat procedures.
28. **Condition & Effect Resolver**: Tracks buffs/debuffs.
29. **Progression & Reward Resolver**: Handles XP and loot.

## Phased Implementation Strategy

To launch the system efficiently, the **Minimum Viable Backbone** was built first (16 elements):

- Orchestrator, Session Director, World State Keeper, Continuity Archivist, Narrative Weaver
- NPC Actor Engine, NPC Persona Engine, Environment Simulator, Faction Simulator
- DNA Registry, DNA Decoder, Inheritance Engine, Procedural Forge
- Consistency Auditor, Safety Governor
- **Two lightweight Game System Arbiter packages for hot-swapping tests.**

> [!NOTE]
> The MVP backbone is now functional. The focus has shifted to architectural hardening
> based on the formal review (see below).

---

## Completed Architectural Enhancements

Based on the formal [Architectural Review](docs/Architectural%20Review_%20DNA%20Framework.md), the following systemic improvements have been implemented. Each "Bucket" maps one or more identified bottlenecks (B1–B4) and proposed enhancements (E1–E5) to concrete code changes.

### Bucket A — Parallel Pipeline (B1, E1)

**Problem:** Serial LLM calls in the runtime loop caused 10–15+ second turn latency.

**Solution:** `SessionDirector.advance_scene()` now uses `asyncio.gather()` for two parallel phases:

1. **Input phase:** Safety Governor `filter_input()` runs in parallel with the Orchestrator's intent classification.
2. **Output phase:** Safety Governor `filter_content()` runs in parallel with the Consistency Auditor.

**Files changed:** `session_director.py`, `safety_governor.py` (new `filter_input()` method)

### Bucket B — Patch Auditor (B2, E3)

**Problem:** The Consistency Auditor was a binary pass/fail gate. On failure, it forced the Narrative Weaver to fully regenerate — risking infinite rollback loops.

**Solution:** The Auditor is now a "Patch Agent":

- `audit()` returns the **exact offending sentence** alongside the error explanation.
- New `patch()` method surgically rewrites only the bad sentence via a focused LLM call.
- Session Director caps patch attempts at **2** before falling back to an OOC note.

**Files changed:** `consistency_auditor.py`, `session_director.py`

### Bucket C — Event Ledger (B3, E4)

**Problem:** Agents passed full state objects, leading to inconsistent views of micro-state (e.g., NPC Engine using stale data).

**Solution:** New `EventLedger` (event sourcing pattern):

- All state changes are emitted as `StateEvent` deltas to an ordered, append-only log.
- Any agent can query the ledger by target, location, type, or timestamp.
- `snapshot()` replays events into a flattened current-state dict.
- `render_context()` produces LLM-ready context blocks.
- `WorldStateKeeper.get_context_window()` combines reality + recent deltas for downstream agents.

**New file:** `src/core/event_ledger.py`
**Files changed:** `world_state.py`

### Bucket D — Graph Registry (B4, E2)

**Problem:** The Registry relied solely on semantic vector search (RAG), which missed deterministic relationships (e.g., "NPC X is a member of Faction Y").

**Solution:** Graph-augmented retrieval with named relationship labels:

- `link_elements()` now accepts an optional `label` parameter (e.g., `"hates"`, `"father_of"`, `"trades_with"`).
- `query_graph(entity_id, depth)` performs BFS traversal returning human-readable relational fact strings.
- `get_contextual_brief()` combines deterministic graph facts with semantic phenotype excerpts — the primary method for LLM context injection.
- `get_link_ids()` provides backward-compatible plain-ID access.

**Files changed:** `registry.py`, `inheritance.py`

### Bucket E — Chronicler Agent (E5)

**Problem:** Long sessions (4+ hours) degraded context window quality and inflated token costs.

**Solution:** New `Chronicler` background agent:

- Runs every N turns (default: 10) to compress the Event Ledger into dense factual bullet points.
- Commits verbose history to `ContinuityArchivist` for long-term storage.
- Provides `get_session_context()` for compressed session history injection.
- Non-blocking — uses `asyncio.create_task()` to avoid delaying the player response.

**New file:** `src/agents/layer3_support/chronicler.py`
**Files changed:** `session_director.py`

---

## Testing

Unit tests are located in `tests/`:

| Test File | Tests | Coverage |
| :--- | :--- | :--- |
| `test_event_ledger.py` | 7 | Emit/retrieve, target/location filtering, snapshot reconstruction, entity removal, context rendering, max-event pruning |
| `test_registry_graph.py` | 6 | Labeled links, legacy compat, depth-1/2 graph traversal, contextual brief, default label behavior |

Run all tests:

```bash
.\venv\Scripts\python.exe -m pytest tests/ -v
```

---

## Technology Stack & Framework

- **Core Framework**: Custom multi-agent orchestration built on LangChain + OpenAI-compatible API.
- **LLM Runtime**: Ollama (configured for `qwen3.5:397b-cloud` by default, accessible at `http://localhost:11434/v1`).
- **Async Engine**: Python `asyncio` for parallel agent dispatch.
- **State Management**: Event Sourcing via `EventLedger` (in-memory, append-only).
- **Graph**: In-memory graph (Python dicts) for deterministic relationship queries. No external graph DB dependency.
- **Ruleset Cartridges (MVP)**: Two simple rulesets ("One Page 5e" and "Coin Flip") for hot-swapping tests.
