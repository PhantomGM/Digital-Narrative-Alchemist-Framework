# Session 0 trial — findings

Run 2026-08-06. Four player-agents against the four sample profiles, a GM
synthesising, then 15 entities generated for real through `ProceduralForge` +
the live decoders (Gemini 2.5 Flash, free tier), then a pitch back to the table.
All four players accepted.

Artifacts: `01_round1_transcript.md`, `02_campaign_pitch.md`, `pages/` (15
decoded entities, ~145k chars), `registry.json`, `generate_world.py`.

**Nothing here touched `data/world_builder_registry.json`.** This is a new world.

---

## The result that changes §8

| World | Stubs implied per made entity |
| :--- | :--- |
| Skarn (112 records, mature) | **0.97** — sub-critical, terminates |
| The Hollow Assay (15 entities, new) | **3.67** — super-critical |

PROJECT_STATE §8 concluded that the system terminates because the observed
branching factor sits just under 1. That conclusion is **true only of a mature
world**, and the reason is now obvious: the brake is `find_by_name` dedupe, which
needs a populated registry to bite. A new world has nothing to dedupe against, so
it branches at very nearly the raw rate the decoders are asked for (2–4 Unmade
Connections; observed 3.67).

15 entities implied 55 stubs. Left to expand, those 55 would imply roughly 200,
and so on. **The runaway risk was never in the mature world — it is exactly in the
new-world case the AI canonizer is meant to handle.** The contract is not a
refinement; on a fresh world it is the only thing standing between Session 0 and
unbounded generation.

---

## What the trial validated

**1. Session 0 beats a static profile, and the margin is not small.**
The four stated genres had *no* common member. High Fantasy had three of four —
but the missing player was Marcus, the Explorer/Instigator, i.e. the one who
drives the plot when the party stalls. A profile-driven system majority-votes
High Fantasy and quietly disengages its own engine.

The interview showed the labels were misleading. Marcus wanted "dusty towns with
something wrong under the floorboards" and slow-burn dread. Elias wanted gothic
weight and a town with recurring faces. Sarah wanted dense asymmetric factions.
Chloe wanted warmth and a team. **Those four wants have no conflict at all.** The
frame that satisfies all of them — a frontier mining town over something wrong —
is not a compromise between the genres, and no amount of reading the profiles
would have produced it.

**2. Session 0 sets the quota, not just the tone.**
§8's generic contract proposed 2 factions. Sarah's answer — "same want for
different reasons is a coalition, not a conflict" — raised it to 3 *and specified
their kinds*: one seeking, one sealing, one indifferent to the mine entirely.
The generated factions came out matching that exactly (Whispering Descent,
Obsidian Vigil, Loom Syndicate), and Sarah confirmed on the pitch: "That's a real
triangle, not a line with a spectator." The premise also forced `regional_poi`
and `creature` into the contract, which the generic version did not have.

**3. Lines and Veils must reach generation, not just filtering. Proven twice.**
- Sarah clarified unprompted that her bigotry Line applies **to the setting**, not
  only to scenes: "even if no one's PC ever encounters it directly." `SafetyGovernor`
  checks passages after the fact and cannot enforce this — a culture genome emitting
  a caste read as racial produces a page that reads fine in isolation. Carried into
  the prompt instead, it held: her verdict on the finished pitch was "nobody's evil
  because of who they were born as."
- Marcus's claustrophobia Veil **collided with the premise itself**. A mine campaign
  is not fixable by filtering output; it changes what must be generated. Raising it
  in round two produced a usable rule from him — *"is the scene ABOUT the space
  being small, or is the space just where the scene happens"* — which went into the
  generation block. On the pitch he cleared the rockfall hook himself: "sounds like
  an event, not a scene I'm trapped inside."

**4. The private channel was used, by the person who needed it.**
Chloe said in round one she could not raise a Veil out loud — "especially being
newer to the table, I'd probably freeze up." Everyone else said out-loud was fine.
The GM offered a private channel to the whole table **without attributing it**,
and she used it, volunteering something nobody asked for:

> "I might be slow to speak up if something's bothering me... So if I go quiet in
> a scene, it's probably not a signal, I'm probably just listening."

That is a **false-negative warning**: an AI GM watching for distress would misread
her silence continuously. It surfaced only because the channel existed, was
private, and was framed as normal rather than exceptional.

**5. The canon-safety rule held under real generation.**
The lore page resolved enough to be usable (the coded text is genuine; the truth it
identifies is a deliberate forgery) and left the load-bearing question explicitly
open: "the exact nature of the original fabricators and their full intent remains
contested among scholars." That is precisely the behaviour the rule exists for.

**6. Context accumulation produced a connected world, not 15 pages.**
Every entity from the ninth onward referenced earlier ones by name. The creature
page cited **Seraphina Volkov** — a real generated NPC from three slots earlier,
not an invention. The quest tied the Loom Syndicate, the Aether-Motes and The
Question together. NPC 3 referenced both earlier NPCs.

**7. DNA fought the premise once and the decoder reconciled rather than broke.**
The creature genome rolled `#colossus` at threat 8 into a premise about people
coming back *subtly* changed. The decode: a creature "no larger than a miner's
thumbnail, yet possessing the ecological impact of a titanic beast." Neither the
DNA nor the canon was discarded. This is the project's central thesis working
without assistance.

**8. Declining to pre-seed worked.**
Elias asked that no NPC be pre-assigned a redemption arc — "I'll see the seams."
Nothing was seeded. His verdict on three generated NPCs: "None of the three reads
as pre-turned to me — good, that's what I asked for." **Some contract slots must
be deliberately left unfilled**, and that is a design property, not an omission.

---

## Defects the trial found

**1. A type quota is not a contract.** The per-slot briefs existed in
`CONTRACT` but were used only in a `print()` — they never reached a prompt. The
three factions still came out right because that requirement happened to be
spelled out in the shared agreements block. The one `regional_poi`, briefed only
as "the mine", generated **"The Arch of Whispers, a Dimensional Ruin"** on a
plateau. A count says how many; it does not say which. Fixed in
`build_context(brief=...)` and verified: the same genome type then produced "The
Deepstone Bastion Mine, known as The Maw."

**2. Generation order is part of the contract.** `linguistic` sat sixth, after
`world`, `region` and `settlement` — **the town was named before the naming rules
existed.** `regional_poi` sat fourth, before the factions, so it invented "tribal
factions" competing over it, duplicating a layer that was about to be generated
properly. Dependencies must order the contract; a flat list will not do.

**3. A type quota cannot express tone.** Chloe asked for warmth and room to
breathe. It was in the agreements block. Every entity still came out grim, and
she said so on the pitch: *"it does read as intense pretty much everywhere, even
the town part... I don't see an obvious 'just breathe' scene in this pitch yet."*
She is right. Faction, NPC, creature and lore genomes all trend toward conflict,
and **nothing in a type-and-count contract can ask for a place to have a meal.**
The contract needs tonal slots, not only entity slots.

**4. Two kinds of Session 0 output, and the contract only holds one.** Some
answers shape the *world* (Sarah's asymmetry, Marcus's veil). Others shape
*runtime GM behaviour* and cannot be generated into anything:
- Sarah: "Loom needs equal stage time or we drift into a two-sided fight with a
  paperwork bystander by session four."
- Chloe: impact should be **social** — "someone actually notices" — not mechanical.
- Chloe: silence is not a distress signal from her.
These belong in a session-time directive the GM agent reads, not in the world.

**5. Three decoders leak their own template labels as headers.** Found while
indexing the pages, not while reading them — which is why it was nearly missed.
The first heading of a page should be the entity's name. Three are not:

| File | First heading | Should be |
| :--- | :--- | :--- |
| `01_world.md` | `World Overview` | the world's name |
| `02_region.md` | `Region Name: The Saltspire Marches` | `The Saltspire Marches` |
| `15_quest.md` | `1. Quest Title` | `The Scholar's Descent` |

`world`, `region` and `quest` are all among the fourteen decoders that have never
had a refinement pass, and each prints a template field label into its output —
the same class of defect PROJECT_STATE §7 records for palette labels printed as
headers. **It is a pattern in the unrefined set, not one bad decoder**, which
means the remaining eleven should be assumed to do it until checked.

It also breaks extraction downstream. `ExpansionManager._extract_name` walks
heading patterns in order, so it would name the world "World Overview" and the
quest "1. Quest Title". The structured YAML tail saves this in practice — every
one of the 15 pages emitted a valid tail, and `parse_phenotype_tail` is the
primary path — but the regex fallback exists precisely for when a decoder omits
the tail, and on these three it would return a template label.

**6. `community` still routes to `npc`.** One decoder labelled a stub
`community`; `_resolve_stub_type` has no key for it, so it fell through the npc
default. Everything else routed correctly post-fix — including `regional_poi`,
which was unreachable until this morning. **A mine registered as a person would
have been this trial's headline bug.**

**7. `PlayerProfileManager` cannot represent what these players actually said.**
It stores one flat `lines_and_veils` list of strings. It cannot express: that
Marcus's animal Line is about *on-screen death* rather than content existence;
that Sarah's bigotry Line binds *worldbuilding* and not only scenes; that a Veil
means "refer to it, don't depict it" while a Line means "never"; or that Chloe
needs a private channel. Every one of those distinctions came out of the interview
and none of them survives the current data structure.

---

## Verdict

The pipeline works, and the parts that worked were the parts driven by the
interview rather than by defaults. The design holds.

The two things to fix before this becomes real are both cheap: **per-slot briefs
with a dependency order** (the contract is a graph, not a list), and **a Lines and
Veils structure that distinguishes a prohibition from a deferral** and reaches
generation rather than only filtering.

The thing to fix that is *not* cheap is the new-world branching factor. 3.67 is
the number that matters, and nothing currently bounds it.
