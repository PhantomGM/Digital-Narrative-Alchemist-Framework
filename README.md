# Digital Narrative Alchemist (DNA) Framework

A modular, multi-agent AI framework designed to serve as a comprehensive, autonomous Tabletop Roleplaying Game (TTRPG) Game Master.

Unlike simple chat-bot RPGs, the DNA framework separates narrative generation, procedural content generation (PCG), safety/consistency auditing, and hard-coded mechanical rules adjudication into specialized agent layers.

---

## 🏗️ System Architecture

The DNA Framework is built on a philosophy of **System Agnosticism**. The foundational AI handles world simulation and narrative flow, while rules adjudication and mathematics are handled via modular, hot-swappable sub-agent cartridges.

The architecture is divided into four distinct operational layers encompassing over two dozen normalized agents.

### Layer I: Core Runtime Intelligence

These agents form the active, real-time "brain" of the AI GM. They manage the flow of the session, the pacing, and the authoritative truth of the game world.

* **Orchestrator**: The master routing hub. It intercepts player input, decides if a mechanical rule needs to be invoked, or if it can be handled purely narratively.
* **Session Director**: Controls structural pacing, scene framing, and encounter injection. Coordinates all sub-agents through a **parallel async pipeline** — Safety Governor and Orchestrator process input simultaneously via `asyncio.gather()`, cutting turn latency roughly in half.
* **World State Keeper & Continuity Archivist**: Tracks the authoritative present reality and stores/retrieves past scenes to maintain strict canon. Now powered by the **Event Ledger** — all state changes emit deltas to an ordered log, ensuring every agent sees the same micro-state.
* **Narrative Weaver**: Translates raw state changes and mechanical outcomes into vivid, engaging prose for the players.
* **Simulators (Faction, Environment, Encounter)**: Autonomous agents that inject dynamic hazards, weather, and macro-social events into the scene based on pacing needs.

### Layer II: DNA / PCG Substrate

Handles the procedural generation of raw world elements (Genotypes) and invokes an LLM to translate them into rich narrative content (Phenotypes).

* **Procedural Forge** (`forge.py`): Master dispatcher for DNA generation. Routes `synthesize_element(type)` calls to the correct generator.
* **DNA Decoder** (`decoder.py`): Auto-loads all decoder prompts from `decoders/` and translates raw DNA strings into evocative, playable profiles via LLM chains. Handles Langchain template escaping for DNA brace syntax.
* **DNA Registry** (`registry.py`): Graph-augmented database mapping DNA strings to decoded phenotypes. Supports **named relationship labels**, **BFS graph traversal**, and **contextual briefs** combining deterministic graph facts with semantic phenotype excerpts.
* **Inheritance Engine** (`inheritance.py`): Resolves Multi-Directional constraints (Up, Down, Sideways) with graph-augmented context from the Registry.

#### Supported Entity Types

| Scale | Entity Type | Generator | Decoder Prompt | Output Template |
| :--- | :--- | :--- | :--- | :--- |
| Macro | World | `world.py` (v3.2, PANTHEON + SHADOW + ORIGIN) | `world.md` | `templates/world.md` |
| Meso | Region | `region.py` | `region.md` | `templates/region.md` |
| Meso | Settlement | `location.py` (produces `SETTLEMENT{}` DNA) | `settlement.md` | `templates/settlement.md` |
| Meso | Location | `location.py` | `location.md` | `templates/settlement.md` |
| Org | Faction | `faction.py` | `faction.md` | `templates/faction.md` |
| Micro | NPC | `npc.py` (LNC/GNE dual-axis personality) | `npc.md` | `templates/npc.md` |
| Action | Quest | `quest.py` (GOAL/OBS/REWARD/NARR/MOTIV/ENGAGE/CHAIN/EVO) | `quest.md` | `templates/quest.md` |
| Artifact | Magic Item | `item.py` (PHY/MAG/HIS/LOR/ATTUNE/CHAIN/EVO) | `item.md` | `templates/item.md` |
| Environ | Travel | `travel.py` (Danger/Discovery/SpecialFactor) | `travel.md` | `templates/travel.md` |
| Struct | Trap | `trap.py` | — | — |
| Struct | Establishment | `establishment.py` | — | — |
| Struct | Regional POI | `regional_poi.py` | — | — |
| Struct | World Wonder | `wonder.py` | — | — |
| Org | Agency | `agency.py` | — | — |
| Macro | Realm | `realm.py` | — | — |

#### System Specification Documents

Canonical rules governing all DNA generation and decoding live in `docs/dna_specs/`:

* **DNA System Rules** — The 5 Narrative Synthesis Mandates, value interpretation ranges (1-33/34-66/67-99), CHAIN/EVO pattern definitions, and the Resolution Engine for contradiction handling.
* **Metadata Priority Logic** — Thin Parent architecture, field locking, and data hierarchy rules.
* **Conductor Routing** — User intent classification and routing to the correct generator/decoder pipeline.

### Layer III: Support / Reliability Layer

Middleware guardrails ensuring safe, logical, and tonally consistent operation.

* **Consistency Auditor (Patch Agent)**: Intercepts LLM outputs to compare them against the World State. If the LLM hallucinates an impossibility, the Auditor **surgically patches the offending sentence** in-place rather than forcing full regeneration — eliminating infinite rollback loops.
* **Safety Governor**: Analyzes player input and LLM output to ensure it adheres to pre-defined campaign tones and safety boundaries (Lines & Veils). Now includes input pre-screening via `filter_input()` for parallel safety checks.
* **Chronicler**: Background agent that **compresses the Event Ledger** every N turns into dense factual summaries, managing context window degradation over long sessions (4+ hours).

### Layer IV: Modular Game-System Layer

Swappable logic cartridges tailored to specific, hard-coded TTRPG rulesets.

* **Game System Arbiter**: The interface that processes intent. By swapping the Arbiter (e.g., from D&D 5e to a generic Coin Flip system), the entire mathematical framework of the game changes without breaking the narrative logic of Layers I-III.

---

## 🚀 Getting Started

The system is currently configured as a functional **Minimum Viable Backbone** with **architectural hardening** applied from a formal review.

### Core Modules

| Module | File | Description |
| :--- | :--- | :--- |
| Event Ledger | `src/core/event_ledger.py` | Ordered state delta log (event sourcing) |
| Orchestrator | `src/core/orchestrator.py` | Master input router |
| Contracts | `src/core/contracts.py` | 7 Pydantic schemas for typed inter-agent communication |
| Procedural Forge | `src/agents/layer2_dna/forge.py` | DNA generation dispatcher (14 entity types) |
| DNA Decoder | `src/agents/layer2_dna/decoder.py` | LLM-driven DNA → narrative translation (9 decoder prompts) |
| DNA Registry | `src/agents/layer2_dna/registry.py` | Graph-augmented entity database |
| State Critic | `src/agents/layer3_support/state_critic.py` | Narrative-mechanical consistency circuit breaker |

### Prerequisites

* Python 3.10+
* An active local LLM runtime (configured for `qwen3.5:397b-cloud` via Ollama by default, accessible at `http://localhost:11434/v1`)
* `.env` file containing:

  ```env
  OLLAMA_API_KEY=dummy_key
  OLLAMA_BASE_URL=http://localhost:11434/v1
  ```

### Running the Test Loop

To run the primary integration test, which demonstrates the Orchestrator routing, hot-swapping Layer IV rulesets, and Layer II Inheritance Generation:

```bash
python main.py
```

### Running Tests

```bash
.\venv\Scripts\python.exe -m pytest tests/ -v
```

## 🗺️ Roadmap

The DNA framework is actively under development. Current focus areas include:

1. **Fleshing out Layer IV (TTRPG Cartridges)**: Building comprehensive Adapters and Resolvers to handle complex mathematics (e.g., tracking HP, Condition Effects, and XP) rather than utilizing stubbed logic.
2. **Expanding Generator Coverage**: Fleshing out stub generators (realm, agency, region) into full DNA-producing generators with matching decoder prompts.
3. **Session Pulse & Campaign Architecture**: Building out the remaining Layer III utilities to assist human co-GMs in scaffolding sessions before they begin.
4. **Speculative Streaming**: Implementing Narrative Weaver output streaming to the client while the Auditor reviews concurrently, further reducing perceived latency.
5. **External Graph Database**: Evaluating migration from in-memory graph to NetworkX or Neo4j for persistent cross-session relationship queries.
6. **Template-Driven Output**: Wiring the output templates (`templates/`) into the decoder pipeline so decoded DNA conforms to the Obsidian-compatible template structure.

---
*The Digital Narrative Alchemist is designed to push the boundaries of AI TTRPG emulation beyond simple chatbots, creating a dynamic, internally consistent, and mechanically rigorous virtual game master.*
