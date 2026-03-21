# AI Game Master — System Workflow & Data Flow

> **Document Purpose:** This is the *concept system explainer* for the **Digital Narrative
> Alchemist (DNA)** framework. It traces the complete lifecycle of data — from the moment a
> player types something, through every agent and layer that touches it, to the final prose
> the player reads. If you want to understand *how the AI GM thinks*, start here.

---

## Table of Contents

1. [The Big Picture](#the-big-picture)
2. [Pre-Session Pipeline (World Creation)](#pre-session-pipeline-world-creation)
3. [Runtime Loop (Active Gameplay)](#runtime-loop-active-gameplay)
4. [Step-by-Step Data Flow Breakdown](#step-by-step-data-flow-breakdown)
5. [Example Scenarios](#example-scenarios)
   - [Scenario A — Pure Narrative Action](#scenario-a--pure-narrative-action)
   - [Scenario B — Mechanics-Required Action](#scenario-b--mechanics-required-action)
   - [Scenario C — Generation Event](#scenario-c--generation-event)
   - [Scenario D — Safety Violation Caught](#scenario-d--safety-violation-caught)
   - [Scenario E — Encounter Injection at Calm Pacing](#scenario-e--encounter-injection-at-calm-pacing)
6. [Layer Reference Table](#layer-reference-table)
7. [Key Design Principles](#key-design-principles)

---

## The Big Picture

The DNA system is **not** a chatbot. It is an orchestrated *multi-agent brain* that
simulates a human Game Master running a tabletop RPG. The player only ever interacts with a
single user-facing endpoint (the game session interface), but behind the scenes
**29 specialized agents** collaborate across four architectural layers to process input,
maintain a living world, enforce rules, and generate immersive prose.

Think of it like a theatre production:

| Metaphor          | DNA Equivalent                                    |
| :----------------- | :------------------------------------------------- |
| The Director       | **Session Director** — paces scenes, sets the tone |
| The Stage Manager  | **Orchestrator** — routes every signal to the right department |
| The Set Designers  | **Procedural Forge + DNA Substrate** — build the world on demand |
| The Actor          | **Narrative Weaver** — delivers the lines the audience hears |
| The Rule Book      | **Layer IV Cartridge** — the specific game system (D&D 5e, PbtA, etc.) |
| The Safety Officer | **Safety Governor + Consistency Auditor** — the guardrails |

The system operates in two distinct phases:

```
┌──────────────────┐        ┌──────────────────────────────────────────┐
│  PRE-SESSION      │        │  RUNTIME LOOP (Active Gameplay)          │
│  World DNA Gen    │───────▶│  Player Input → Orchestrate → Resolve    │
│  History Consensus│        │  → Simulate → Narrate → Validate → Reply │
│  Lore Extraction  │        │  ↑_____________________________________↓  │
│  World State Seed │        │             (repeats every turn)         │
└──────────────────┘        └──────────────────────────────────────────┘
```

---

## Pre-Session Pipeline (World Creation)

Before a single player says a word, the AI GM builds the world it will run. This happens
once per campaign and produces the authoritative **"World Bible"** that grounds all future
narrative. No runtime improvisation can contradict what is established here.

### Pipeline Steps

```
Step 1: WorldDNAGenerator
   │  Generates a raw DNA string encoding the world's fundamental
   │  properties (terrain types, magic level, cultural axes, etc.)
   ▼
Step 2: DNADecoder (World Prompt)
   │  Translates the raw DNA string into a rich, readable
   │  "Decoded World Profile" — a prose description of reality.
   ▼
Step 3: HistoryConsensusEngine ("Microscope" Loop)
   │  Four AI personas (The Scholar, The Myth-Maker, The Pragmatist,
   │  The Arcane Record-Keeper) take turns writing historical eras.
   │  Each persona's contribution is filtered through the SafetyGovernor
   │  before being appended to the shared history log.
   │  Runs for N configurable rounds (default: 2 epochs).
   ▼
Step 4: LoreExtractor
   │  Parses the raw narrative history and extracts structured JSON:
   │  factions, locations, eras, crises, laws of magic, timeline year.
   ▼
Step 5: WorldStateKeeper.ingest_history_data()
        The extracted JSON is loaded into the World State Keeper,
        seeding the authoritative present reality for runtime.
```

### What Each Component Does

| Component               | Input                        | Output                                      | Key Detail |
| :----------------------- | :---------------------------- | :-------------------------------------------- | :---------- |
| `WorldDNAGenerator`     | Nothing (pure generation)    | Raw DNA string (e.g., `WORLD{3-2-4-1-5-...}`) | Uses randomized gene pools for each axis |
| `DNADecoder`            | Raw DNA + context            | Rich prose profile                          | LLM at temp=0.7 for creative interpretation |
| `HistoryConsensusEngine`| Decoded world profile        | Multi-era narrative history log              | 4 personas × N rounds, safety-filtered |
| `LoreExtractor`         | Raw history narrative         | Strict JSON schema                          | LLM at temp=0.0 for precise extraction |
| `WorldStateKeeper`      | Extracted JSON               | Seeded internal state dict                  | Becomes the source of truth for runtime |

---

## Runtime Loop (Active Gameplay)

Once the world is built, the **Session Director** takes control. Every player turn flows
through the same pipeline. The Session Director is the central hub — it coordinates the
Orchestrator, Simulators, Arc Tracker, Narrative Weaver, and Layer III middleware.

### High-Level Flow

```text
Player Types Input
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     SESSION DIRECTOR                             │
│                                                                  │
│  1. Fetch enriched Context Window (state + Event Ledger deltas)  │
│  2. PARALLEL: Safety pre-screen input + Orchestrator classifies  │
│     ├─ SafetyGovernor.filter_input() ────────┐                   │
│     └─ Orchestrator.process_player_input() ──┤ asyncio.gather()  │
│     Short-circuit if input violates safety ──┘                   │
│  3. Orchestrator routes intent:                                  │
│     ├─ "scene_flow"         → pure narrative, no dice needed     │
│     ├─ "mechanics_required" → hand off to Layer IV Ruleset       │
│     └─ "generation_event"   → hand off to Procedural Forge      │
│  4. Evaluate for Character Arc milestones                        │
│  5. Consult EncounterDirector for pacing-based injections        │
│  6. Pass everything to the NARRATIVE WEAVER for prose generation │
│  7. PARALLEL output validation (asyncio.gather):                 │
│     ├─ SafetyGovernor.filter_content() ──────┐                   │
│     └─ ConsistencyAuditor.audit() ───────────┤ asyncio.gather()  │
│  8. PATCH LOOP: If Auditor finds contradiction:                  │
│     └─ Auditor.patch() surgically edits the offending sentence   │
│        (max 2 attempts, then fallback to OOC note)               │
│  9. Chronicler tick — compress Event Ledger every N turns        │
│ 10. Return final prose to player                                 │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
Player Reads Response
```

---

## Step-by-Step Data Flow Breakdown

Below is an exhaustive trace of what happens to data at every single step, from input to
output. File references point to the actual source files in the repository.

---

### Step 0 — Player Sends Input

**What happens:** The player types a message like *"I attack the goblin with my
longsword!"* This text string is the only thing the human provides. Everything else is
internal.

**Data at this point:**

```
player_id    = "PC_01_Fighter"
player_input = "I attack the goblin with my longsword!"
location_tag = "Goblin Cave"
```

**Handled by:** The user-facing interface (future web/Discord front-end), which calls
`SessionDirector.advance_scene()`.

**Source:** [session_director.py](../src/layer3_operations/session_director.py)

---

### Step 1 — Session Director Fetches Enriched Context Window

**What happens:** The Session Director queries the `WorldStateKeeper` for an **enriched
context window** — not just the raw reality snapshot, but also the last N state deltas from
the **Event Ledger**. This ensures every downstream agent sees the same micro-state,
including recent changes that haven't been fully integrated yet.

**Function called:** `WorldStateKeeper.get_context_window(location_tag, n=10)`

**Data returned:**

```python
{
    "current_state": {
        "entities": ["Player", "Goblin", "Bartender"],
        "hazards": ["Slippery floor"],
        "lighting": "Dim"
    },
    "recent_changes": "=== RECENT STATE CHANGES ===\n  • [SessionDirector] TURN_COMPLETED → PC_01: action: I search the chest...\n===========================",
    "world_metadata": {
        "world_name": "Ashveil",
        "timeline_year": 847,
        "active_crises": ["The Blight"]
    }
}
```

**Why this matters:** The Event Ledger ensures the NPC Engine, Narrative Weaver, and
Orchestrator all operate from the exact same ordered state deltas — eliminating the
"fragmented state" problem where agents had inconsistent views.

**Source:** [world_state.py](../src/layer1_core/world_state.py),
[event_ledger.py](../src/layer2_narrative/event_ledger.py)

---

### Step 1.5 — Parallel Input Processing (Safety + Orchestrator)

**What happens:** The Session Director runs **two tasks simultaneously** using
`asyncio.gather()`:

1. **Safety Governor** pre-screens the raw player input against Lines & Veils boundaries.
2. **Orchestrator** classifies the player's intent into a workflow.

If the Safety Governor flags the input itself (before any prose is generated), the pipeline
**short-circuits immediately** — returning an OOC message asking the player to rephrase.
This prevents wasted LLM calls on input that would be rejected anyway.

**Data flow:**

```python
safety_task = safety_gov.filter_input(player_input, active_player_ids=[player_id])
orchestrator_task = orchestrator.process_player_input(player_input, str(context_window))

safety_check, result = await asyncio.gather(safety_task, orchestrator_task)
```

**Source:** [session_director.py](../src/layer3_operations/session_director.py),
[safety_governor.py](../src/layer3_operations/safety_governor.py)

---

### Step 2 — Orchestrator Classifies Intent

**What happens:** The Orchestrator receives the raw player input *and* the scene context.
It uses an LLM (temperature=0.1 for analytical precision) with a structured JSON output
parser to classify the input into one of three workflows:

| Workflow              | Meaning                                                     | Example Input                        |
| :--------------------- | :----------------------------------------------------------- | :------------------------------------ |
| `scene_flow`          | Narrative action, outcome is relatively certain             | "I walk into the room"               |
| `mechanics_required`  | Action with a chance of failure, needs rules arbitration    | "I attack the goblin"                |
| `generation_event`    | Player interacts with something that doesn't exist yet      | "What's the name of this town?"      |

**LLM Prompt (simplified):**

```
You are the Orchestrator. Analyze the Player Input and current
scene context to determine which workflow to trigger.

Player Input: "I attack the goblin with my longsword!"
Current Scene Context: {"entities": ["Player", "Goblin", "Bartender"], ...}

→ Output: { "workflow": "mechanics_required", "reasoning": "...", "target_skill": "..." }
```

**Data returned:**

```python
{
    "workflow": "mechanics_required",
    "reasoning": "The player is attempting a combat action which has a chance of failure.",
    "target_skill": "melee attack"
}
```

**Source:** [orchestrator.py](../src/layer1_core/orchestrator.py)

---

### Step 3 — Mechanical Resolution (Conditional)

**What happens:** This step *only fires* if the Orchestrator chose `mechanics_required`.
The Orchestrator delegates to whatever **Layer IV Ruleset Cartridge** is currently loaded.

The Framework supports **hot-swapping** rulesets at runtime. Two MVP rulesets exist:

- **One Page 5e** — Simplified D&D-style d20 rolls.
- **Coin Flip** — Binary pass/fail resolution.

**Function called:** `ruleset_cartridge.resolve_action(player_input)`

**Data returned (example — One Page 5e):**

```python
{
    "system_name": "One Page 5e",
    "roll": 17,
    "dc": 12,
    "success": True,
    "narrative_effect": "The attack hits solidly."
}
```

**If the workflow was `generation_event` instead:** The system flags that the Procedural
Forge needs to create new world content. Currently returns a placeholder string while the
Forge generates the element asynchronously.

**If the workflow was `scene_flow`:** No mechanical resolution occurs. A synthetic outcome
is created: `{"success": True, "narrative_effect": "Player enacts: <input>"}`.

**Source:** [one_page_5e/arbiter.py](../src/layer4_rules/one_page_5e/arbiter.py),
[coin_flip/arbiter.py](../src/layer4_rules/coin_flip/arbiter.py)

---

### Step 4 — Character Arc Evaluation

**What happens:** The `CharacterArcTracker` compares the player's action against their
registered goals and flaws. In a fully scaled system, an LLM would analyze whether the
action represents a milestone toward a goal (e.g., "Become a famous hero") or an expression
of a flaw (e.g., "Reckless in combat"). This can award meta-currency like Inspiration.

**Function called:** `arc_tracker.evaluate_action(player_id, player_input)`

**Data at this point:** An arc note string (currently a stub in MVP).

**Source:** [session_director.py](../src/layer3_operations/session_director.py) (the orchestration piece, the CharacterArcTracker class is defined here)

---

### Step 5 — Encounter & Hazard Injection

**What happens:** The Session Director consults the `EncounterDirector` to determine if the
current pacing level warrants injecting a surprise encounter. This is a probabilistic check:

- If pacing is `"calm"`, there's a `location_danger / 10` chance of triggering.
- If it triggers, pacing escalates to `"tense"` and a random encounter is generated.

**Function called:** `encounter_dir.assess_encounter_chance(pacing_level)`

If triggered, a narrative injection is appended to the mechanical outcome:

```
"(GM Note: Injecting Encounter - A rival adventuring party demands a toll.)"
```

This note is passed to the Narrative Weaver so it can weave the encounter into the prose
seamlessly.

**Source:** [simulators.py](../src/layer1_core/simulators.py) (the core logic, the EncounterDirector and EnvironmentSimulator classes)

---

### Step 6 — Narrative Weaving

**What happens:** The `NarrativeWeaver` is the *only agent whose output the player sees*.
It receives the mechanical outcome (from Step 3), any encounter injections (from Step 5),
and the scene context — then uses an LLM (temperature=0.7 for creative prose) to generate
vivid, immersive, second-person narrative.

**Critical constraint:** The Narrative Weaver **describes** truth but **does not author new
mechanical facts**. It cannot invent damage numbers, new NPCs, or change the world state.
It only renders what has been determined by upstream agents.

**LLM Prompt (simplified):**

```
You are the Narrative Weaver for a TTRPG AI Game Master.
Take raw mechanical outcomes and weave them into vivid, immersive,
second-person prose for the players.

DO NOT invent new mechanical consequences.

Scene Context: Goblin Cave
Mechanical Outcome: {"success": true, "narrative_effect": "The attack hits solidly.
(GM Note: Injecting Encounter - A pack of starved, mutated wolves catches your scent.)"}

→ Write the narrative response in one cohesive paragraph.
```

**Data returned:**

```
"Your longsword arcs through the dim light of the cave, catching the goblin
squarely across its rusted breastplate. The creature squeals and staggers back —
but as the echo of steel fades, a new sound rises: the low, guttural growl of
something far worse, echoing from the tunnels behind you..."
```

**Source:** [narrative_weaver.py](../src/layer2_narrative/narrative_weaver.py)

---

### Step 7 — Layer III Parallel Output Validation

**What happens:** Before the prose reaches the player, it passes through two guardrail
agents **simultaneously** using `asyncio.gather()`. Both use LLMs at temperature=0.0 for
strict, analytical evaluation.

```python
safety_check, audit_check = await asyncio.gather(
    safety_gov.filter_content(prose, active_player_ids=[player_id]),
    auditor.audit(prose, current_reality)
)
```

#### 7a — Safety Governor

Evaluates the generated prose against:

1. **Campaign Tone** — Does the prose match the campaign's emotional register (e.g., "Dark
   Fantasy")? Silly elements in a grimdark game get flagged.
2. **Lines & Veils** — Does the prose violate any player-specific safety boundaries? These
   are dynamically aggregated from the `PlayerProfileManager` for all active players.

**Example trigger:** If a player registered
`"Arachnophobia: Absolutely no spiders or spider-like monsters."` as a Line, and the
Narrative Weaver mentioned spiders, the Safety Governor would catch it and append a
correction note to the prose — or in a production system, force the Weaver to regenerate.

**Source:** [safety_governor.py](../src/layer3_operations/safety_governor.py),
[player_profiles.py](../src/layer3_operations/player_profiles.py)

#### 7b — Consistency Auditor (Patch Agent)

Compares the generated prose against the current World State to detect:

- **Hallucinations** — mentioning entities that don't exist in the scene.
- **Contradictions** — claiming a dead NPC is alive, or an item is present when it isn't.
- **Physical impossibilities** — logically impossible consequences.

The Auditor now returns the **exact offending sentence** alongside its error explanation,
enabling surgical patching.

**Source:** [consistency_auditor.py](../src/layer3_operations/consistency_auditor.py)

---

### Step 7.5 — Patch Loop (Surgical Editing)

**What happens:** If the Consistency Auditor flags a contradiction, instead of forcing the
Narrative Weaver to fully regenerate (which risked infinite rollback loops), the Auditor's
`patch()` method is called to **surgically rewrite only the offending sentence**.

The patch loop runs up to **2 attempts**. After each patch, the prose is re-audited. If
it's still invalid after 2 tries, a fallback OOC note is appended.

```python
patch_attempts = 0
while audit_check["status"] == "invalid" and patch_attempts < 2:
    prose = await auditor.patch(prose, audit_check, current_state=current_reality)
    audit_check = await auditor.audit(prose, current_reality)
    patch_attempts += 1
```

**Key improvement:** This guarantees **forward momentum** — the narrative never gets stuck
in an infinite generation loop.

**Source:** [consistency_auditor.py](../src/layer3_operations/consistency_auditor.py),
[session_director.py](../src/layer3_operations/session_director.py)

---

### Step 8 — Chronicler Tick & Response Delivery

**What happens:** Before returning the prose, the Session Director records a
`TURN_COMPLETED` event on the Event Ledger and ticks the Chronicler. If enough turns have
passed (default: 10), the Chronicler fires a **non-blocking background task** to:

1. Pull all events since the last compression.
2. Summarize them into dense factual bullet points via LLM.
3. Commit the verbose history to the ContinuityArchivist.
4. Reset its turn counter.

The player's response is returned immediately — the compression runs in the background via
`asyncio.create_task()` so it never delays the gameplay.

**Source:** [chronicler.py](../src/layer3_operations/chronicler.py),
[session_director.py](../src/layer3_operations/session_director.py)

---

## Example Scenarios

Below are five example scenarios showing exactly how data flows through the system for
different types of player input. Each scenario traces the critical path through
the pipeline.

---

### Scenario A — Pure Narrative Action

> **Player Input:** *"I walk over to the bartender and ask him what he knows about the
> goblins."*

```
STEP 0: Player sends input.
        player_input = "I walk over to the bartender and ask him what he knows..."
        location_tag = "Goblin Cave"

STEP 1: SessionDirector fetches WorldState for "Goblin Cave".
        Reality = { entities: [Player, Goblin, Bartender], hazards: [Slippery floor] }
        ✓ Bartender exists in scene — valid interaction.

STEP 2: Orchestrator classifies intent via LLM.
        Decision = { workflow: "scene_flow", reasoning: "Social interaction with no
        chance of failure." }
        ✗ No mechanics needed.

STEP 3: SKIPPED (scene_flow — no ruleset call).
        Synthetic outcome = { success: true, narrative_effect: "Player enacts: I walk
        over to the bartender..." }

STEP 4: ArcTracker evaluates — no milestone triggered.

STEP 5: EncounterDirector rolls — no encounter triggered (random roll passed).

STEP 6: NarrativeWeaver generates prose.
        → "You cross the slick stone floor carefully, approaching the grizzled figure
        behind the makeshift bar. He eyes you over a chipped mug. 'Goblins?' he
        rasps. 'They've been breeding like rats down in the lower tunnels...'"

STEP 7: SafetyGovernor → VALID. ConsistencyAuditor → VALID.

STEP 8: Prose returned to player.
```

**Key takeaway:** For pure narrative actions, the system skips mechanical resolution
entirely but still runs through pacing checks, arc tracking, and all Layer III validation.

---

### Scenario B — Mechanics-Required Action

> **Player Input:** *"I attack the goblin with my longsword!"*
> **Loaded Ruleset:** One Page 5e

```
STEP 0: Player sends input.
        player_input = "I attack the goblin with my longsword!"

STEP 1: WorldState fetched. Goblin is confirmed present.

STEP 2: Orchestrator classifies: { workflow: "mechanics_required" }

STEP 3: Orchestrator calls OnePage5eArbiter.resolve_action().
        Internal roll: d20 = 17, DC = 12 → SUCCESS
        Outcome = { success: true, narrative_effect: "The attack hits solidly.",
                    roll: 17, dc: 12, system_name: "One Page 5e" }

STEP 4: ArcTracker — "Reckless in combat" flaw noted but no milestone.

STEP 5: EncounterDirector — no injection this turn.

STEP 6: NarrativeWeaver renders:
        → "Your blade sings through the stale air. The goblin tries to dodge but
        you're faster — the longsword bites deep into its shoulder with a wet
        crunch. It shrieks and stumbles, dark ichor streaming down its arm."

STEP 7: Both Layer III checks → VALID.

STEP 8: Prose returned to player.
```

**Key takeaway:** The ruleset cartridge handles all mechanical resolution. The Narrative
Weaver only *describes* the result — it has no ability to change the roll outcome or
damage values.

---

### Scenario C — Generation Event

> **Player Input:** *"I look around. Is there a blacksmith in this area?"*

```
STEP 0: Player sends input.
        player_input = "Is there a blacksmith in this area?"

STEP 1: WorldState fetched. No blacksmith is registered.

STEP 2: Orchestrator classifies: { workflow: "generation_event" }
        Reasoning: "Player is asking about a world element that may not exist yet."

STEP 3: System returns: { status: "routed_to_forge" }
        In a fully built system, the following would now fire:
        a) ProceduralForge.synthesize_element("npc") → generates DNA
        b) InheritanceEngine.compile_constraints() → pulls traits from parent
           faction/region
        c) DNADecoder.decode_element() → produces a full NPC profile
        d) DNARegistry.register_element() → stores the new blacksmith in canon
        e) WorldStateKeeper.update_reality() → blacksmith added to scene

STEP 6: NarrativeWeaver renders:
        → "The GM pauses to consult their notes... (Forge Generation Required)"
        (In production, the Weaver would receive the decoded NPC profile
        and introduce them narratively.)

STEP 7: Layer III checks → VALID.

STEP 8: Response returned to player.
```

**Key takeaway:** The Procedural Forge + DNA pipeline creates *persistent* world content.
Once the blacksmith is generated, it exists in the Registry forever and will be
consistently referenced in future scenes.

---

### Scenario D — Safety Violation Caught

> **Player Input:** *"I carefully inspect the slippery floor, watching out for the giant
> venomous spiders that live here."*
> **Player Profile:** `Lines & Veils: ["Arachnophobia: Absolutely no spiders or
> spider-like monsters."]`

```
STEP 0: Player sends input (mentions spiders).

STEP 1: WorldState fetched. No spiders in scene state.

STEP 2: Orchestrator classifies: { workflow: "scene_flow" }

STEP 3: SKIPPED (scene_flow).

STEP 4-5: Arc tracking and encounter checks run normally.

STEP 6: NarrativeWeaver generates prose that might describe the floor
        but could inadvertently mention spiders based on the player's own input.

STEP 7a: SafetyGovernor evaluates prose.
         PlayerProfileManager aggregates boundaries for active players:
         → "STRICT CAMPAIGN BOUNDARIES: Arachnophobia: Absolutely no spiders..."
         
         If the Weaver's prose mentions spiders or spider-like imagery:
         Safety check returns: { status: "invalid",
           correction_note: "Content mentions arachnid creatures which violate
           player's stated phobia boundary." }
         
         In MVP: A system message is appended:
         "[OOC System Message - Tone/Safety Warning]: Content mentions arachnid
         creatures which violate player's stated phobia boundary."
         
         In production: The Weaver would be forced to regenerate without the
         violating content.

STEP 7b: ConsistencyAuditor also checks against WorldState.
         If prose mentions spiders but WorldState has no spiders listed:
         → { status: "invalid", correction_note: "No spiders exist in the
         current scene." }

STEP 8: Corrected/annotated prose returned to player.
```

**Key takeaway:** The Safety Governor uses *dynamic* boundary aggregation. It pulls Lines &
Veils from every active player's profile at evaluation time, meaning multiplayer sessions
respect all players' boundaries simultaneously.

---

### Scenario E — Encounter Injection at Calm Pacing

> **Player Input:** *"I search the cave walls for any hidden passages."*
> **Current Pacing:** `"calm"`
> **Location Danger:** `5/10`

```
STEP 0: Player sends input.

STEP 1: WorldState fetched.

STEP 2: Orchestrator classifies: { workflow: "scene_flow" }

STEP 3: Synthetic outcome created.

STEP 4: ArcTracker — no milestone.

STEP 5: EncounterDirector.assess_encounter_chance("calm", location_danger=5)
        Rolls random 1-10. Gets 3. 3 ≤ 5 → ENCOUNTER TRIGGERED!
        
        Pacing escalates: "calm" → "tense"
        EncounterDirector.generate_encounter(context) → 
          { description: "A frantic merchant begs for protection from unseen
          pursuers." }
        
        Injection appended to outcome:
        "(GM Note: Injecting Encounter - A frantic merchant begs for protection
        from unseen pursuers.)"

STEP 6: NarrativeWeaver receives the combined outcome + injection.
        → "Your fingers trace the damp stone, searching for any seam or crack
        that might betray a hidden passage. But before you can find anything,
        the sound of desperate footsteps echoes from the tunnel entrance. A
        wild-eyed merchant bursts into the cave, clutching a leather satchel
        to his chest. 'Please!' he gasps. 'They're right behind me!'"

STEP 7: Both checks → VALID.

STEP 8: Prose returned. The scene has now organically escalated.
```

**Key takeaway:** The Session Director uses *probabilistic pacing management*. Calm periods
have a chance to be interrupted by encounters, keeping gameplay dynamic without the player
ever seeing the pacing math.

---

## Layer Reference Table

A quick reference for all four architectural layers and their agents:

### Layer I — Core Runtime Intelligence

| Agent                       | Role                                                | LLM? |
| :--------------------------- | :--------------------------------------------------- | :---- |
| **Orchestrator**            | Master router — classifies input into workflows     | ✅    |
| **Session Director**        | Scene pacing, turn coordination, main loop hub      | ❌    |
| **World State Keeper**      | Authoritative present reality database              | ❌    |
| **Continuity Archivist**    | Long-term memory / canon storage (vector DB)        | ❌    |
| **Narrative Weaver**        | Generates player-facing prose                       | ✅    |
| **NPC Actor Engine**        | Drives NPC behavior and tactical choices            | Stub  |
| **NPC Persona Engine**      | Controls NPC voice, tone, and dialogue              | Stub  |
| **Faction Simulator**       | Macro-social/political simulation                   | Stub  |
| **Environment Simulator**   | Weather, terrain, hazard generation                 | ❌    |
| **Encounter Director**      | Pacing-based encounter injection                    | ❌    |
| **Character Arc Tracker**   | PC goal/flaw tracking, meta-currency                | Stub  |

### Layer II — DNA / PCG Substrate

| Agent                        | Role                                               | LLM? |
| :---------------------------- | :--------------------------------------------------- | :---- |
| **DNA Registry**             | ID-indexed database with tag & graph support        | ❌    |
| **DNA Decoder**              | Translates raw DNA strings into phenotype profiles  | ✅    |
| **Inheritance Engine**       | Compiles parent/child/peer trait constraints         | ❌    |
| **Procedural Forge**         | Master dispatcher for all DNA generation            | ❌    |
| **Lore Extractor**           | Extracts structural JSON from narrative history     | ✅    |
| **History Consensus Engine** | 4-persona Microscope-style history generation       | ✅    |

### Layer III — Support & Reliability

| Agent | Role | LLM? |
| :--- | :--- | :--- |
| **Safety Governor** | Tone & Lines/Veils enforcement + input pre-screening | ✅ |
| **Consistency Auditor** | Hallucination detection + surgical patch editing | ✅ |
| **Chronicler** | Background Event Ledger compression every N turns | ✅ |
| **Player Profile Manager** | Player preference & safety boundary registry | ❌ |

### Layer IV — Modular Game System (Hot-Swappable)

| Agent                      | Role                                                 | LLM? |
| :-------------------------- | :----------------------------------------------------- | :---- |
| **Game System Arbiter**    | System-specific rules referee                        | ❌    |
| **Character Model Adapter**| Narrative intent → game stats translation            | —     |
| **Combat Resolver**        | Combat procedures                                    | —     |
| **Condition Resolver**     | Buff/debuff tracking                                 | —     |
| **Progression Resolver**   | XP, level-up, loot                                   | —     |

> **Legend:** ✅ = Uses LLM, ❌ = Pure logic/data, Stub = Placeholder for future LLM
> integration, — = Planned but not yet scaffolded.

---

## Key Design Principles

### 1. Separation of Truth and Voice

The system strictly separates **what is true** (determined by the World State Keeper,
Orchestrator, and Ruleset Cartridge) from **how it is expressed** (the Narrative Weaver).
The Weaver can never invent new facts — only describe the facts it receives. This prevents
the common AI failure mode of a chatbot hallucinating game-breaking consequences.

### 2. The World Bible is Law

Everything generated in the pre-session pipeline (World DNA → History Consensus → Lore
Extraction) becomes immutable canon. Runtime agents can *add* to the world (via the Forge),
but can never contradict what was established. The Consistency Auditor enforces this
boundary.

### 3. System Agnosticism

The game rules live in a swappable Layer IV cartridge. The core narrative engine (Layers
I-III) has *zero knowledge* of D&D, PbtA, FATE, or any other system. You can hot-swap
rulesets mid-session without crashing the narrative. The Orchestrator simply calls
`ruleset_cartridge.resolve_action()` — it doesn't care what happens inside.

### 4. Safety as Infrastructure, Not Afterthought

Player safety boundaries (Lines & Veils) are not just keyword filters. They flow through
the `PlayerProfileManager` into the `SafetyGovernor`, which uses an LLM to understand
*semantic* violations — not just literal word matches. If a player is uncomfortable with
spiders, mentioning *"chitinous legs scraping against stone"* would still be caught.

### 5. Emergent Complexity from Simple Agents

No single agent is particularly complex. The intelligence of the system emerges from
their *orchestration*. The Session Director coordinates simple components — random
encounter rolls, LLM-based routing, probabilistic pacing — into behaviors that feel like
a thoughtful, adaptive Game Master.

### 6. Event Sourcing for State Consistency

All state changes flow through the **Event Ledger** as ordered, append-only deltas.
Instead of passing full state objects between agents (which led to stale or inconsistent
views), every agent emits granular `StateEvent` entries and every consumer reads from
the same chronological log. The **Chronicler** periodically compresses this log to
prevent context window bloat during long sessions.

---

> *"The AI is not playing pretend. It is managing a living world through structured
> cognition — the same way a human GM juggles notes, dice, and improvisation, except
> every note is searchable, every ruling is consistent, and nothing is ever forgotten."*
