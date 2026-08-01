# Digital Narrative Alchemist (DNA) Framework

A modular, multi-agent AI framework built around one substrate serving two ends:

* **A world-building backbone** — generating an internally consistent world bible that a human author owns and approves. This is intended to drive a user-facing AI **co-creator** app, where the author makes every creative decision and the machine does the drafting, cross-referencing, and consistency checking.
* **An autonomous TTRPG Game Master** — running play, adjudicating rules deterministically, and narrating the outcome, drawing on the world the substrate built.

Neither is a subsystem of the other. The GM needs a world that holds together under scrutiny; the co-creator needs those same guarantees with the author in the loop. Both are served by the same DNA substrate, the same canon model, and the same consistency auditing.

Unlike simple chat-bot RPGs, the DNA framework separates narrative generation, procedural content generation (PCG), safety/consistency auditing, and hard-coded mechanical rules adjudication into specialized agent layers.

---

## 🚀 Getting Started

The system is currently configured as a functional **Minimum Viable Backbone** with **architectural hardening** applied from a formal review.

### Environment Setup

* Python 3.10+
* Copy `.env.example` to `.env` and configure your API keys.

The framework evaluates the cognitive load required for each agent and routes requests dynamically via the central `ModelRouter`. You do **not** need all keys to run the system; the multi-provider `.with_fallbacks()` pipeline will silently skip providers you haven't configured and fall back to the next available one.

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

The suite runs entirely offline: every model call is stubbed, so no API keys are
needed to test. `tests/test_readme_claims.py` checks the counts quoted in this
file against the code, so the two cannot drift apart unnoticed.

### Pointing at a Vault

Every script that touches a world bible needs to be told where it is, either with
`--vault` or via `OBSIDIAN_VAULT_PATH`. **Nothing guesses a default.** An
unresolvable path string is not silently created as a directory: a Windows path
handed to a POSIX interpreter is not a path at all, and a hardcoded fallback once
wrote an entire generated vault into a single mangled directory inside the repo.
Scripts fail with an explanation instead.

```bash
.\venv\Scripts\python.exe scripts\sync_to_obsidian.py --vault "C:\path\to\Vault"
```

---

## 🔄 A Single Player Turn (Minimal Lifecycle)

Multi-agent systems can seem overwhelming. So how does a simple action flow through the DNA Framework?

### Example A: A Narrative Flow
1. **Player Input:** *“I look around the tavern.”* 
2. **Intent Routing (`Orchestrator`):** The orchestration layer intercepts the text, recognizing it as a non-mechanical narrative action (no rule lookups needed). It updates the `World State Keeper` with the player's new location.
3. **Response Generation (`Narrative Weaver`):** The Weaver receives the updated state ("Player observing the tavern") and invokes a Tier-3 generative LLM to craft immersive prose. The output is logged in the `Event Ledger` and sent to the player.

### Example B: A Mechanical Flow (The Framework's True Power)
1. **Player Input:** *“I attack the goblin with my broadsword.”*
2. **Intent Routing (`Orchestrator`):** Recognizing a mechanical attack intent, the Orchestrator steps back and tokenizes the input, routing it directly into **Tier 1**. 
3. **Deterministic Math (`Layer IV Rules`):** Pure Python math calculates the roll, the goblin's armor class, and the damage reduction *without ever touching an LLM*, ensuring zero math hallucination. It returns a strict JSON payload: `{ "target": "goblin 3", "HP_delta": -12, "status_applied": "bleeding" }`.
4. **Response Translation (`Narrative Weaver`):** The Weaver receives the cold mathematical payload and translates it into Tier-3 generative prose. The AI hasn't done the math; it is simply playing the role of the narrator reading the math.

---

## 📖 The World Bible Pipeline

The substrate generates a world into an Obsidian vault, one page per entity. Its
purpose is not volume — it is a world that survives scrutiny, so that a GM can
answer a player's question and a co-creator can trust what it is shown.

### The canon model

Every page carries a status, and the boundary is absolute:

| Status | Meaning |
| :--- | :--- |
| `canon` | Approved by the author. Treated as fact. Never contradicted silently. |
| `draft` | Proposed. May change freely. |
| `deprecated` | No longer true. Kept, and linked forward to its replacement. |

**Everything the machine invents enters as `draft`. Only the author promotes to
canon.** The pipeline enforces this rather than merely asking: the vault sync
refuses to overwrite a canon page, the canonize gate audits canon but will not
patch it, and retyping an entity whose page is canon is rejected outright.

### Three ways to make a page

Not everything should be generated, and this is the substrate's central idea:

1. **Generate** (DNA + decoder) — for entities that *should* vary: an NPC, a
   creature, a culture. Random DNA is a constraint scaffold that forces variety;
   the surrounding canon supplies the fit; the model supplies the novelty. The
   same seed under different context yields a different, still-valid creation.
2. **Compose** (from canon, no DNA, no model) — for an entity canon already
   describes. Rolling a genome here would contradict what is established, so the
   page is assembled from existing canon text with each statement sourced.
3. **Derive** (a view over canon) — for things that must *not* vary: the
   timeline, indexes, hub rosters, and the list of entities the world has named
   but not yet written. Regenerating these must be idempotent, so no model is
   involved at all. Stubs in particular *cannot* be found any other way — they
   are held out of the vault deliberately, so no search can see them.

### DNA types

Every one of the 21 registered generator types now has a dedicated decoder. Each type exists
because a shared one leaked something it shouldn't, and each keystone axis was
chosen to prevent a specific observed failure:

| Type | Keystone axis | Prevents |
| :--- | :--- | :--- |
| `creature` | Sapience | A mindless swarm being given morality and motive |
| `culture` | Cohesion | A whole people rendered as a monolith with one agenda |
| `lore` | Veracity, held independent of Reach | Belief being conflated with truth |
| `text` | Legibility, paired with purport vs. actual | A document treated as its own message |

Also registered: `npc`, `faction`, `location`, `settlement`, `region`, `item`,
`quest`, `travel`, `chronicle`, `linguistic`, `world`.

### Consistency auditing

Generated prose is audited against a **canon slice** assembled per entity: the
world frame, the containment chain, the author's standing rulings, and the **full
text** of the canon pages the passage actually depends on. Gists are not enough —
judging a claim against a one-line summary produced both false positives (a true
statement patched away) and false negatives (a ruling violated undetected). The
author's terminology rulings are appended after any length cap, because they were
once truncated out of every prompt, and a rule absent from the prompt cannot be
followed.

### Scripts

| Script | Purpose |
| :--- | :--- |
| `seed_to_bible_demo.py` | Seed a world, decode it, register the stubs it implies |
| `multi_agent_expansion_demo.py` | Expand pending stubs in parallel |
| `canonize_gate.py` | Audit entities against canon, then sync drafts |
| `compose_from_canon.py` | Build pages for stubs canon already describes |
| `compose_timeline.py` | Re-derive the chronology from dated events |
| `compose_stub_index.py` | Re-derive the list of named-but-unwritten entities |
| `compose_world_graph.py` | Render the registry as a self-contained interactive graph |
| `backfill_registry.py` | Reconcile the registry against the vault; derive the link-gap worklist |
| `export_showcase.py` | Carve the curated example registry out of a working one |
| `sync_to_obsidian.py` | Write the registry into the vault, canon untouched |
| `list_models.py` | Probe which models the configured keys can actually reach |

### Which registry?

The registry is where a world lives — every entity, its DNA, its decoded prose,
and the graph of what relates to what. Two of them matter here:

| File | Tracked | What it is |
| :--- | :---: | :--- |
| `data/showcase_registry.json` | yes | A curated slice of a real generated world. What the scripts above default to, and what a fresh clone runs against. |
| `data/world_builder_registry.json` | no | Your working world. Grows on every run, carries the full text of every page, stays local. |

The example slice is not a fixture — it is genuine pipeline output, one entity
per generated type plus a few unmade stubs, so the derivers, the graph view and
the stub index all have something real to work on. Regenerate it with
`export_showcase.py`; choose what goes in by editing `data/showcase_names.txt`.

Nothing forces this split. If your world is meant to be public, track it.

---

## 🧩 Building a Layer IV Rules Cartridge

The true power of the DNA framework is **System Agnosticism**. 
You can switch the mechanical engine of the game simply by dropping a new Python cartridge into the Layer IV `src/layer4_rules/` folder. This guarantees the LLM *never* hallucinates mathematical dice rolls.

To build an MVP TTRPG cartridge from scratch, you only need three things:
- [ ] **Core Arbiter Adapter:** Your cartridge's entry point that inherits requests from the Orchestrator.
- [ ] **A Dice Roller / Resolver Logics:** Pure Python math functions determining successes.
- [ ] **A State Delta Schema:** A Pydantic schema enforcing exactly what gets passed back to the Narrative engine.

### Explicit API Contracts
When the `Orchestrator` maps a player intent to a mechanical action (e.g., picking a lock), it pushes a strict JSON dictionary to your adapter:

**Input from Orchestrator:**
```json
// Note: These key-value pairs are dynamically generated by the Orchestrator based on your specific TTRPG's configuration.
{
  "action": "pick_lock",
  "skill_modifier": 4,
  "target_dc": 15
}
```

Your pure-Python resolver logic calculates the outcome utilizing whatever rule system you wrote. It **must** return an explicitly typed Pydantic object for the `Narrative Weaver` to process safely.

**Required Pydantic Return Schema (`layer1_core/contracts.py`):**
```python
from pydantic import BaseModel
from typing import Optional

class StateDelta(BaseModel):
    success: bool
    numerical_result: int
    delta_description: str
    fatal_error: Optional[bool] = False
```

**Output from your Custom Cartridge:**
```json
{
  "success": true,
  "numerical_result": 22,
  "delta_description": "Thieves tools defeated the rusty tumblers.",
  "fatal_error": false
}
```
If your custom cartridge outputs to this contract, you can wire *any* tabletop system into the DNA Framework.

---

## 🧠 Deep Architecture & Latency (The 5 Layers)

The DNA Framework utilizes exactly 5 operational layers mapped aggressively to a **3-Tier Decision Boundary**. By matching structural layers to Compute Tiers, developers immediately know the latency scale and API cost of the agents they are editing.

<details>
<summary><b>Click to expand the 5-Layer Deep Dive</b></summary>

### 1. `[Tier 1: Deterministic]` Layer IV: Modular Game-System Layer (`src/layer4_rules/`)
**Latency:** Sub-millisecond (Pure Python/SQLite)
No unpredictable LLMs are invoked in this directory. It houses swappable logic cartridges tailored to specific TTRPG rulesets. 

#### Active Cartridges
| System Name | Directory | Capabilities |
| :--- | :--- | :--- |
| Pathfinder 2nd Edition SRD | `PF2EDNA` | `combat_resolution`, `skill_checks`, `saving_throws`, `spellcasting`, `rest_mechanics`, `encounter_budgeting` |
| One Page 5e (Stub) | `one_page_5e` | Basic action resolution stub |
| Coin Flip (Stub) | `coin_flip` | Pure 50/50 probability testing |

### 2. `[Tier 2: Semantic Light]` Layer III: Operations / Reliability (`src/layer3_operations/`)
**Latency:** < 1 Second (Local Llama/Gemini Flash)
Middleware guardrails ensuring safe, logical, and tonally consistent operation over long sessions.
* **Session Director**: Controls structural pacing and encounter injection via **parallel async pipelines**.
* **Consistency Auditor**: Intercepts LLM outputs to compare them against the World State.
* **Safety Governor**: Rapidly analyzes player inputs ensuring strict adherence to boundaries.
* **Chronicler**: Background agent that compresses memory.
* **State Critic**: Narrative-mechanical consistency circuit breaker.

### 3. `[Tier 3: Semantic Heavy]` Layer II: Narrative Engine (`src/layer2_narrative/`)
**Latency:** 2-6 Seconds (Claude Opus/GPT-4o)
Specialized for vivid prose and ordered event sourcing.
* **Narrative Weaver**: Translates raw state changes and mechanical outcomes from Tier 1 into vivid, engaging prose.
* **Event Ledger**: Ordered immutable database tracking micro-state history.

### 4. `[Tier 3: Semantic Heavy]` Layer V: DNA / PCG Substrate (`src/layer5_dna_substrate/`)
**Latency:** 5-10 Seconds (Background/Pre-Computation)
The isolated procedural engine. Generates raw world elements (Genotypes), invokes frontier models to translate them into rich narrative content (Phenotypes), and maintains the world bible those phenotypes live in.

*Generation*
* **Procedural Forge**: Master dispatcher for DNA mathematical generation (21 entity types registered; 21 with dedicated decoders).
* **DNA Decoder**: Translates pure mathematical DNA strings into playable profiles.
* **Inheritance Engine**: Resolves constraints using graph context.
* **Expansion Manager**: Turns the stubs a phenotype implies into real entities, forwarding seed and axis pins so canon-established facts are not re-rolled at random.
* **DNA Registry**: The entity graph and working memory, with deterministic persistence.

*World fit and verification*
* **Context Assembler**: Builds the layered context package every decode and every audit reads — world frame, locale, lineage, negative space, directives — plus the cited canon text used for verification.
* **Vault Adapter**: Read-only access to the world bible: overview, calendar, standing rulings, page text, index roster.
* **Canonize Gate**: The audit → surgical patch → re-audit loop. Fail-closed, and it never patches a canon page.
* **Phenotype Meta**: The structured tail decoders emit (name, gist, summary, stubs), and the scrubbing of decoder scaffolding.

*Composition and derivation*
* **Canon Composer**: Builds a sourced page for a stub canon already describes, with no DNA and no model.
* **Timeline Composer**: Re-derives the chronology as a view over canon; idempotent by construction.
* **Obsidian Sync**: Writes the registry into the vault by type taxonomy, refusing to overwrite canon or deprecated pages.
* **History Consensus**: Microscope-style auto-weaving of deep campaign lore out of the semantic data mesh prior to player involvement.

### 5. `[Tier 2: Semantic Light]` Layer I: Core Runtime Intelligence (`src/layer1_core/`)
**Latency:** < 0.5 Seconds (Fast Routing Model or Keyword Logic)
The foundational brain routing traffic between all layers.
* **Orchestrator**: The master input router identifying intents.
* **ModelRouter**: The centralized multi-provider fallback factory serving instances from the 3-Tier Compute Matrix.
* **World State Keeper**: The authoritative tracking of the present reality.
* **Contracts**: Pydantic schemas (as detailed above).

</details>

---

## 🗺️ Roadmap

The DNA framework is actively under development. Current focus areas include:

1. **A user-facing co-creator app**: Putting the world-building pipeline behind an interface where the author reviews, approves, and promotes without touching a command line. The canon model and the audit trail already assume a human in this seat.
2. **Deepening the recovered decoders**: `agency`, `establishment`, `realm`, `regional_poi`, `trap` and `wonder` were recovered from an early master-prompt file and are marked as drafts in their own headers. `establishment` needs the most work — its generator emits twenty genes with no vocabularies defined, and the recovered key described an older seven-gene genome. `agency.SPEC` and `realm.CONF` also reference a value table that was never in this repository.
3. **Missing types**: a *phenomenon* type for forces that are real rather than believed, and a *group* type for peoples who are neither a faction nor a culture.
4. **More derivers**: The timeline proved the pattern. Indexes, folder hub rosters, regional gazetteers, and a faction power-web are all views over canon that should regenerate rather than be maintained by hand.
5. **Fleshing out Layer IV (TTRPG Cartridges)**: Building comprehensive Adapters and Resolvers to handle complex mathematics (e.g., tracking HP, Condition Effects, and XP) rather than utilizing stubbed logic.
6. **Session Pulse & Campaign Architecture**: Building out the remaining Layer III utilities to assist human co-GMs in scaffolding sessions before they begin.
7. **Speculative Streaming**: Implementing Narrative Weaver output streaming to the client while the Auditor reviews concurrently, further reducing perceived latency.
8. **External Graph Database**: Evaluating migration from in-memory graph to NetworkX or Neo4j for persistent cross-session relationship queries.
9. **Template-Driven Output**: Decoded pages currently conform to the vault taxonomy through `ObsidianSync`. Reading the vault's own `Templates/` directory instead would let a vault define its page shapes rather than the code assuming them.

---
*The Digital Narrative Alchemist is designed to push the boundaries of AI TTRPG emulation beyond simple chatbots, creating a dynamic, internally consistent, and mechanically rigorous virtual game master.*
