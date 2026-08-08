# Trial 2 — do the fixes work?

Run 2026-08-07. Same four players, **same transcripts**, same premise. The only
variable is the machinery: trial 1 used a hand-rolled `(type, count)` list and a
safety block pasted into a prompt string; trial 2 uses `ContentContract` and
`ContextPackage.safety`. Holding the interview constant is deliberate — every
fix was in the generation half, so a difference here is attributable to the fix
rather than to different answers.

16 entities, 12 slots, contract satisfied. Pages in `pages_trial2/`, registry in
`registry_trial2.json`. Trial 1's pages are untouched; they are the evidence.
Reproduce with `compare_trials.py`.

---

## Every trial 1 defect, retested

| # | Defect | Trial 1 | Trial 2 |
| :--- | :--- | :--- | :--- |
| 1 | Per-slot brief | Dimensional arch on a plateau; needed a hand-fix mid-run | **The Glimmerfall Descent, a working mine** — first time |
| 2 | Contract is a graph | `linguistic` 6th, town named before its language | **`linguistic` 2nd, town 4th** |
| 3 | Quota cannot express tone | No warm slot could even be requested | **25 warm cues, 0 dark cues** |
| 5 | Decoders leak template labels | 3 pages opened with a label | **0** |
| 6 | `community` → npc | Fell through to the default | Routes to `culture` |

**The tonal slot is the strongest single result.** Trial 1 could not ask for
warmth at all; the request sat in the shared agreements block and every genome
overrode it. Trial 2's `Slot.tone` produced **The Cog & Kettle** — roasted root
vegetables, charming automatons, a proprietor called Ellie Stone, and no secret
under the floorboards. Zero dark cues in the whole page.

Better still, it did not stay an island. The opening quest hook begins with a
shift boss gripping a mug of cold chicory *in the back corner of the Cog &
Kettle*. The warm room became the place the plot walks into, which is exactly
what "neither is downtime" was asking for.

## Regressions — nothing lost

**Faction asymmetry reproduced independently.** Different names, same required
shape: the **Chthonic Cartographers** (Keepers of the Deep's Memory — the
seekers), the **Custodians of the Breach** (Preservationist Containment
Authority — the sealers), the **Hearthkeepers** (Civic Benefactors / Covert
Assimilators — the town, indifferent to the mine). Sarah's "asymmetric in kind,
not merely in motive" survived a completely different roll of the genome.

**Cross-referencing improved: 10/14 → 15/15.** Every page after the first names
an earlier entity.

**Safety held.** The probe surfaced two candidate passages and reading cleared
both. One is `"pinned the blame"` — the wrong sense of the word. The other is an
explicit **negation**: *"it didn't sound like a cave-in. It didn't sound like
water. It sounded like a wind blowing through a pine forest."* The speaker is
ruling a cave-in out to establish that something stranger is happening. Marcus's
own test was "is the scene ABOUT the space being small" — this scene is about a
sound that should not exist. And the hook is again a rescue, which serves the
support player's wish, but the missing men are *missing*, not pinned under
rubble: better than trial 1's "recent rockfalls trapped her".

**The routing fix paid off in a real run.** Trial 2's stubs include
`regional_poi`, `establishment` and `agency` — five stubs that would have been
silently registered as people and filed under Characters before `72ccdde`.

---

## The finding trial 2 adds

**The contract does not reduce branching, and was never going to.**

| | Stubs implied per entity |
| :--- | :--- |
| Trial 1 | 3.67 |
| Trial 2 | **3.81** |

Essentially unchanged, marginally higher. This is not a failure of the contract
— it is a clarification of what a contract is. **It bounds what gets
GENERATED, not what gets IMPLIED.** Sixteen entities still name sixty-one more,
because every decoder is asked for 2–4 Unmade Connections and the contract has
no opinion about that.

So the contract is a stop condition, not a brake. It answers "is this
deliverable finished?" — decisively, and `contract satisfied` printed at the end
of this run. It does not answer "is this world going to stop growing?", and
nothing in the pipeline currently does. The 3.67 super-critical measurement in
PROJECT_STATE §8 stands untouched, and the depth-limit and Ghost-Registry work
is still entirely outstanding.

Worth stating plainly because it would be easy to read `contract satisfied` as
"the runaway problem is solved". It is not. It is bounded at one end only.

**Since addressed** — `src/layer5_dna_substrate/expansion_policy.py` puts the
bound on the expansion side, where it belongs. Measured against this trial's own
frontier: trial 2's 16 entities implied **58 stubs** (61 mentions, 3 deduped onto
entities that already existed), and at `free_depth=0` every one of them defers
rather than generating.

The measurement also exposed something the design had not accounted for. With
trial 2's seeds left as **draft**, the compose tier answers **nothing** — 0
compose, 58 defer. Promote the same 16 seeds to canon and it answers **30 of 58**.
`CanonComposer` reads only records tagged `canonized`, so on a brand-new world
Tier 2 is inert until the author promotes something. That is correct rather than
broken — composing from drafts would propagate unapproved content as established
fact — but it means the 40%-free figure measured on the live world does not
transfer to a fresh one, and a new world's bound is *defer*, not *compose*.

---

## Verdict

Five of five retested defects fixed, no regressions, and one new negative result
that sharpens the design rather than undermining it. The machinery does what the
scaffolding proved it should.

The next thing to test is the half this trial deliberately held constant: a
fresh interview, to see whether Session 0 reproduces its own findings from
different answers — and whether the `RuntimeDirectives` captured here survive
contact with an actual session.
