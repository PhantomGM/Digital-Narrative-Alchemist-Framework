# Trial 3 — a fresh interview, and what reproduced

Run 2026-08-07. **Identical questionnaire, identical profile prompts, fresh
agents with no memory of trial 1.** Trial 2 held the interview constant to test
the generation half; trial 3 inverts it. The question is whether Session 0
reproduces its own findings from independent answers.

**It splits.** The safety findings reproduce almost exactly. The creative
findings barely reproduce at all. That distinction has a direct design
consequence, and it is the result of this trial.

---

## What reproduced

**Sarah's bigotry Line binds the setting.** Trial 1: *"it applies to the setting
itself, not only scenes involving my PC… built into the world's cultures as
background flavor."* Trial 3: *"it's also about the ambient worldbuilding — I
don't want made-up factions or cultures that are transparently real-world
bigotry with the serial numbers filed off."* Same constraint, independent
wording. This is the one `SafetyGovernor` structurally cannot enforce.

**Marcus's animal Line is about on-screen death.** Trial 1: *"please don't make
me watch a pet or companion creature die on screen."* Trial 3: *"It's
specifically pets/familiars/animal companions getting hurt on-screen."*

**Chloe cannot use the out-loud channel — and trial 3 goes further.** Trial 1:
*"I'd probably freeze up."* Trial 3: *"that feels like a lot of pressure. Maybe a
quick message to the GM **after the session**, or if there's a **Discord**…
something I could give without everyone looking at me."*

That is a **new requirement**: not merely private, but **asynchronous**. Trial 1
produced a private channel offered in-session; trial 3 says the channel may need
to work *after* play, in another medium entirely. The safety design has to reach
outside the session.

**Lethality, unanimously.** Death on the table, following visibly from a choice.
Chloe is more cautious this time — *"it takes a few things going wrong in a row,
and I can see it coming"* — which sharpens rather than contradicts.

## What did not reproduce

**Three of four wish-list answers changed completely.**

| | Trial 1 | Trial 3 |
| :--- | :--- | :--- |
| Elias | A redemption arc for a distrusted **NPC** | A **PC** who starts compromised and earns their way back |
| Sarah | A three-sided faction conflict with mechanical consequences | A **heist/infiltration arc** where planning matters as much as execution |
| Marcus | Slow-burn body horror | **Dying partway through**, with the death rippling through the campaign |
| Chloe | A clutch healer moment | A clutch healer moment ✓ |

These are the answers that shaped trial 1's contract most: Sarah's three-sided
requirement is why the faction count went from 2 to 3, and it is simply **not
present** in trial 3. A contract derived from these transcripts would want a
heist structure, a compromised PC, and a mid-campaign death — almost none of
which the Hollow Assay contract provides.

**The genre tension changed shape and got sharper.** Trial 1's conflict was that
no genre was shared by all four. Trial 3's is a direct tonal collision, stated in
opposition: Marcus wants it *"dangerous, not cozy"*; Chloe *"just don't want it to
be super grim the whole time."* Sarah has also gone genre-agnostic — *"I'm easy
on genre as long as there's a strong central conflict"* — where trial 1 wanted
density. Same four profiles, materially different negotiation.

**Two new runtime directives appeared.** Elias: *"Please don't let me disappear
without someone noticing."* Chloe: *"if it got really heavy without anyone
checking in."* Both are `RuntimeDirectives` material and neither surfaced in
trial 1.

---

## The methodological caveat, which matters

**Three of the four reproduced safety findings were prompted by the
questionnaire.** The profile prompts told Sarah her Line *"is about the
WORLD-BUILDING as much as about scenes, and that distinction is worth making
explicit"*, told Marcus his animal Line was *"worth explaining rather than just
stating"*, and told Chloe that *"a new player may find it hard to raise a
boundary out loud… question 5 is exactly where that would show."*

So their reproduction is **partly an artifact of prompt design, not pure
elicitation**. The prompts were reused verbatim precisely to make trial 3 a fair
comparison, and that same choice carried the hints along with them.

What survives the caveat: Chloe's *asynchronous* requirement was not hinted at
and is new, and the wish-list divergence is unhinted in both directions. The
right next test is a trial 4 with those three hints stripped, to see whether the
safety findings survive without them. Until then the honest claim is narrower:
**Session 0 reproduces safety findings when asked well, and does not reproduce
creative findings even when asked identically.**

---

## The design consequence

**A safety register can be cached per group. A contract cannot.**

The Lines and Veils came back the same across two independent interviews, which
is what a persistent player profile needs to be worth storing —
`SafetyRegister` is stable enough to build on and to carry between campaigns.

The contract is not. Three of four wish-list answers changed, and those answers
are exactly what shaped trial 1's slot counts and briefs. **A contract must be
re-derived per campaign**, from that campaign's Session 0, and a system that
reuses a stored contract will build the wrong world for the right table.

That also sharpens what Session 0 is *for*. The safety half is elicitation of
something stable that already exists in the player. The creative half is not
elicitation at all — it is closer to improvisation, and it will answer
differently on a different evening. Both are worth capturing; only one is worth
caching.
