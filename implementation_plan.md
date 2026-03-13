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

To launch the system efficiently, we will first build the **Minimum Viable Backbone** (16 elements):
- Orchestrator, Session Director, World State Keeper, Continuity Archivist, Narrative Weaver
- NPC Actor Engine, NPC Persona Engine, Environment Simulator, Faction Simulator
- DNA Registry, DNA Decoder, Inheritance Engine, Procedural Forge
- Consistency Auditor, Safety Governor
- **Two lightweight Game System Arbiter packages for hot-swapping tests.**

## Technology Stack & Framework
- **Core Framework**: **OpenClaw** (or a custom adaptation of its open-source skeleton). OpenClaw's modular "Skills" plugin architecture and support for independent, continuously running agents with distinct memory makes it an excellent fit for emulating an adaptive, creative GM brain.
- **Ruleset Cartridges (MVP)**: We will build two very simple rulesets (e.g., "One Page 5e" and a simple "2d6 PbtA" or "Coin Flip" resolution system) to explicitly test the hot-swapping capability of Layer IV during runtime without crashing the narrative.

## User Review Required
> [!IMPORTANT]
> The plan is finalized around OpenClaw and the modular hot-swapping MVP test.
> If you approve of this architectural plan, we can move into the **EXECUTION** phase and begin scaffolding the project structure and the first set of agents!
