# Trial 5 — the full pipeline, and a silent failure

Run 2026-08-07. The first trial to exercise everything: `ContentContract`,
`ContextPackage.safety`, `ExpansionPolicy` and `GhostRegistry`, from a fresh
interview through generation to an advanced frontier. 17 entities, 13 slots,
contract satisfied. Pages in `pages_trial5/`, registry in `registry_trial5.json`.

The interview is written up separately in `07_trial5_interview.md`; its headline
is that **all four players said they would not raise a boundary out loud**.

---

## The defect trial 5 found

**A `culture` decode returned an empty string after 39 seconds, and nothing
noticed.** The harness registered it as an entity, wrote a zero-byte page, fed
that page forward as context for the sixteen entities generated after it, and
printed `contract satisfied: True`.

The world was short one contracted entity and every downstream consumer would
have carried the hole: the registry stores a phenotype, `ObsidianSync` writes it,
`ContextAssembler` reads it, the contract counts it. Silence is the worst
available failure here because every one of those treats a phenotype as content.

`DNADecoder.decode_element` now raises on a blank response. An empty decode is
never valid, and raising is strictly better than returning `""` — the caller can
retry, and a caller that does not is at least loud about it. Seven tests, five of
which fail against the previous behaviour.

**This is the kind of thing only a full run finds.** 1451 tests passed on the
same code, because every one of them supplies its own phenotype.

## What the machinery did

| | Result |
| :--- | :--- |
| Ordering | `world → crews → linguistic → corridor → station → run → hulk → galley → powers → crew → the-wrong → open-question → hook` |
| Per-slot briefs | The hulk is a **ship** — "The Clay-Shorn Pilgrim, an active relic-hulk" — not a station or a ruin |
| Tonal slot | **The Butter-Burner**: "a fragrant, flour-dusted sanctuary… a space of decompression" |
| Faction asymmetry | Reclamation Trust (seeks the hulks) · Threshold Concord (quarantines the corridor) · Ribbon-Way Consortium (wants the station's trade) |
| Label leaks | none in 17 pages, including `travel`, whose decoder was fixed this session |
| Frontier | 49 stubs → **49 ghosted, 0 deferred, 0 expanded** |
| Branching | **2.88** (trial 2: 3.81) |

**The tonal slot integrated itself again.** The Butter-Burner is kept by Marrow —
who is crew member three, generated five slots later. Trial 2's warm room did the
same thing by appearing in the opening hook. Two for two: given a warm slot, the
pipeline does not leave it stranded.

**The `travel` slot is new**, added because a player asked for the quartermaster
problem to be real. It produced "The Iron Ribbon", and it is the first `travel`
entity any trial has generated — the decoder had never run against real canon
before this session's label-leak fix.

**Full ghost coverage showed up immediately.** Trial 2's frontier left 2 stubs
deferred for want of a shape; trial 5 deferred none.

## The safety test that mattered

The premise is a campaign spent boarding derelict ships, and the player holding
the claustrophobia Veil had flagged it himself: *"buried alive is basically a
horror staple… it's a live wire for me specifically in that setting."*

The probe found seven candidate passages. **Every one is economic metaphor** —
*"squeezing independent crews"*, *"squeeze the station dry"*, *"quietly
suffocating those who refuse to sign"* — or a physical pin on a uniform collar.
Nothing in seventeen pages depicts enclosure as an experience.

The closest call is a crew member who *"will lecture anyone nearby on the exact
statistical probability of their collective suffocation."* That is a character's
anxiety, not a scene about a space being small, and it sits the right side of the
line the player drew — but it is a judgement call and worth recording as one.

The gore probe returned a single hit, and it is the world page defining its own
horror **against** the veil: *"The horror here is not born of monsters or gore,
but of the silent, cold vacuum, the unsettling hum of dying reactors."* The
safety block did not merely filter this world; it shaped what the world thinks
horror is.

## The contested constraint, live

The animal-cruelty Line was registered with both incompatible readings the same
player gave across trials 4 and 5. In the run:

- the **prompt** received the strict unqualified form, *"Even off screen is too
  much"* — the narrowing dropped;
- the **author** received `CONTESTED: ['animal cruelty']`;
- the prompt mentioned no disagreement and named no player.

The safe outcome fell out of the rule rather than out of anyone's judgement,
which was the point of building it that way.

## Branching

2.88 against trial 2's 3.81. Two data points and different contracts, so this is
an observation rather than a trend — but it is the first movement in the number
§8 turns on, and it moved in the useful direction. Worth measuring again before
anyone reads anything into it.
