# Digital Narrative Alchemist (DNA) Framework

A modular, multi-agent AI framework designed to serve as a comprehensive, autonomous Tabletop Roleplaying Game (TTRPG) Game Master.

Unlike simple chat-bot RPGs, the DNA framework separates narrative generation, procedural content generation (PCG), safety/consistency auditing, and hard-coded mechanical rules adjudication into specialized agent layers.

---

## 🏗️ System Architecture

The DNA Framework is built on a philosophy of **System Agnosticism**. The foundational AI handles world simulation and narrative flow, while rules adjudication and mathematics are handled via modular, hot-swappable sub-agent cartridges.

The architecture is divided into four distinct operational layers encompassing over two dozen normalized agents.

### Layer I: Core Runtime Intelligence (`src/layer1_core/`)

These agents form the active, base-level computational "brain" of the AI GM. They manage state tracking, formal contracts, and simulators.

* **Orchestrator**: The master routing hub. It intercepts player input, decides if a mechanical rule needs to be invoked, or if it can be handled purely narratively.
* **World State Keeper**: Tracks the authoritative present reality and stores/retrieves past scenes to maintain strict canon.
* **Contracts**: Pydantic schemas that define the typed structure for inter-agent communications.
* **Simulators (Faction, Environment, Encounter)**: Autonomous agents that inject dynamic hazards, weather, and macro-social events into the scene based on pacing needs.

### Layer II: Narrative Engine (`src/layer2_narrative/`)

Specialized for vivid prose and ordered event sourcing.

* **Event Ledger**: All state changes emit deltas to an ordered log, ensuring every agent sees the same micro-state.
* **Narrative Weaver**: Translates raw state changes and mechanical outcomes into vivid, engaging prose for the players.

### Layer III: Operations / Reliability Layer (`src/layer3_operations/`)

Middleware guardrails ensuring safe, logical, and tonally consistent operation over long sessions.

* **Session Director**: Controls structural pacing, scene framing, and encounter injection. Coordinates all sub-agents through a **parallel async pipeline**.
* **Pre-Session Setup**: Manages the initialization sequence spanning world generation to history consensus before gameplay starts.
* **Consistency Auditor (Patch Agent)**: Intercepts LLM outputs to compare them against the World State. Surgically patches hallucinated impossibilities in-place.
* **Safety Governor**: Analyzes player input and LLM output to ensure it adheres to pre-defined campaign tones and safety boundaries.
* **Chronicler**: Background agent that **compresses the Event Ledger** every N turns into dense factual summaries.
* **State Critic**: Narrative-mechanical consistency circuit breaker.
* **Player Profiles**: Tracks and monitors player cognitive boundaries and engagement models.

### Layer IV: Modular Game-System Layer (`src/layer4_rules/`)

Swappable logic cartridges tailored to specific, hard-coded TTRPG rulesets. By swapping the Arbiter in these directories, the mathematical framework of the game changes without breaking the rest of the AI.

#### Active Cartridges

| System Name | Directory | Capabilities |
| :--- | :--- | :--- |
| Pathfinder 2nd Edition SRD | `PF2EDNA` | `combat_resolution`, `skill_checks`, `saving_throws`, `spellcasting`, `rest_mechanics`, `encounter_budgeting` |
| One Page 5e (Stub) | `one_page_5e` | Basic action resolution stub |
| Coin Flip (Stub) | `coin_flip` | Pure 50/50 probability testing |

### Layer V: DNA / PCG Substrate (`src/layer5_dna_substrate/`)

Handles the procedural generation of raw world elements (Genotypes) and invokes an LLM to translate them into rich narrative content (Phenotypes).

* **Procedural Forge** (`forge.py`): Master dispatcher for DNA generation. Routes calls to the correct generator in `generators/`.
* **DNA Decoder** (`decoder.py`): Translates raw DNA strings into evocative, playable profiles via LLM chains.
* **DNA Registry** (`registry.py`): Graph-augmented database mapping DNA strings to decoded phenotypes. Supports BFS graph traversal.
* **Inheritance Engine** (`inheritance.py`): Resolves constraints using graph context.
* **History Consensus / Lore Extractor**: Auto-weaves deep campaign lore out of the semantic data mesh prior to player involvement.

---

## 🧠 LLM Orchestration & Resilience

The DNA Framework utilizes a centralized `ModelRouter` to decouple our 9 cognitive agents from vendor lock-in. Instead of hardcoded LLM initializations, the system assigns models based on a **3-Tier Decision Boundary**:

1. **Executable Actions (No LLM):** Pure state mutations and math (e.g., Layer IV rules calculations, PF2E damage application) never invoke an LLM.
2. **Semantic-Light (Low Latency / Local):** High-speed classification, auditing, and moderation tasks are routed to ultra-fast or local models (e.g., Gemini 2.5 Flash, Llama 4 Scout on Groq).
3. **Semantic-Heavy (Frontier Generative):** Deep prose, complex reasoning, and world-building rely on SOTA models (e.g., Claude 4.6 Opus, DeepSeek R1).

### The Multi-Provider Fallback Pipeline
To ensure seamless GM operation without player interruption, every LLM-gated agent is wired into an automatic fallback chain using LangChain's `.with_fallbacks()`. If a primary API request fails (503 Service Unavailable, Timeout, Rate Limit), the `ModelRouter` redirects the prompt to a secondary provider instantly.

**Refactored Agents utilizing the Fallback Pipeline:**
* `orchestrator` (Core routing logic)
* `narrative_weaver` (Player-facing prose delivery)
* `safety_governor` (Rapid Line & Veil enforcement)
* `state_critic` (Fast circuit breaking mapping logic to prose)
* `chronicler` (Background history compression)
* `consistency_auditor` (Contradiction detection and `auditor_patch` editing)
* `dna_decoder` (Translating world gen arrays to complex lore profiles)
* `history_consensus` (Microscope-style epoch generation)
* `lore_extractor` (JSON truth extraction)

---

## 🚀 Getting Started

The system is currently configured as a functional **Minimum Viable Backbone** with **architectural hardening** applied from a formal review.

### Core Modules

| Module | File | Description |
| :--- | :--- | :--- |
| Event Ledger | `src/layer2_narrative/event_ledger.py` | Ordered state delta log (event sourcing) |
| Orchestrator | `src/layer1_core/orchestrator.py` | Master input router |
| Contracts | `src/layer1_core/contracts.py` | 7 Pydantic schemas for typed inter-agent communication |
| Procedural Forge | `src/layer5_dna_substrate/forge.py` | DNA generation dispatcher (14 entity types) |
| DNA Decoder | `src/layer5_dna_substrate/decoder.py` | LLM-driven DNA → narrative translation |
| DNA Registry | `src/layer5_dna_substrate/registry.py` | Graph-augmented entity database |
| State Critic | `src/layer3_operations/state_critic.py` | Narrative-mechanical consistency circuit breaker |

### Environment Setup

* Python 3.10+
* Copy `.env.example` to `.env` and configure your API keys.

The framework evaluates the cognitive load required for each agent and routes requests dynamically. You do **not** need all keys to run the system; the router will silently skip providers you haven't configured and fall back to the next available one.

Supported providers include:

* **OpenAI** (`OPENAI_API_KEY`)
* **Anthropic** (`ANTHROPIC_API_KEY`)
* **Google Gemini** (`GOOGLE_API_KEY`)
* **Groq** (`GROQ_API_KEY`)
* **DeepSeek** (`DEEPSEEK_API_KEY`)
* **Mistral** (`MISTRAL_API_KEY`)
* **Ollama** (`OLLAMA_API_KEY`, `OLLAMA_BASE_URL`)

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
