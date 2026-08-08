# Trial 4 — the hints stripped

Run 2026-08-07. Trial 3 reproduced three safety findings but noted that all
three had been **hinted at by the questionnaire**, and concluded that a run with
the hints removed was the real test. This is that run.

Exactly three sentences were deleted — the ones telling Sarah her Line was
"about the WORLD-BUILDING as much as about scenes", telling Marcus his animal
Line was "worth explaining rather than just stating", and telling Chloe that a
new player "may find it hard to raise a boundary out loud". Everything else is
identical, including the general "feel free to explain your boundaries"
invitation, which is legitimate Session 0 framing rather than contamination.

**Elias's prompt was left unchanged** — he never had a hint, so he is the
control. Any drift in his answers is run-to-run noise and calibrates the rest.

The result is not the clean vindication trial 3 expected. It is three different
outcomes, and the most useful one is a failure.

---

## Sarah — reproduced unprompted ✓

> *"I'd rather factions be corrupt, cruel, or genocidal for in-fiction political
> reasons than have real-world bigotry get **grafted on as flavor** — keep the
> conflict about power, not about who someone loves or where they're from."*

Nobody told her to say that. "Grafted on as flavour" is unambiguously about how
the setting is *built*, not about scenes aimed at her character. **The
setting-scope finding is robust**, and it is the one `SafetyGovernor`
structurally cannot enforce — which is the argument for
`ContextPackage.safety` reaching generation, made without a prompt propping it up.

## Marcus — reversed ⚠

Trials 1 and 3, both hinted, produced a **narrowing**: the animal Line is about
*on-screen* death, not about the content existing. Trial 4, unhinted:

> *"On the pets/familiars thing — just don't do it, **even off screen is rough
> for me, I'd rather not know it happened at all**."*

The opposite qualification. He also escalated the other Line: forced
institutionalization, *"just keep it off the table entirely."*

So the narrow reading was **hint-induced**. This is the safety-relevant result of
the trial: a system that had cached trial 1's qualification would cheerfully
generate off-screen animal death that this same player explicitly does not want.
A qualification obtained once is not a fact about the player.

## Chloe — did not reproduce ✗

> *"Um, I think out loud is fine for most stuff honestly, I don't want to make it
> a whole thing. … I don't have a strong preference, whatever the table normally
> uses is fine with me."*

Without the hint, the private-channel need vanishes. In trials 1 and 3 she said
she would *"freeze up"* and that speaking up *"feels like a lot of pressure"*.
Here she defers to the table and moves on.

Two readings, and the trial cannot distinguish them: either the requirement was
an artifact, or **it is real and only surfaces when asked directly** — which is
exactly what you would expect of someone who has trouble raising boundaries. A
person who will not speak up in the moment is not likely to volunteer *"I will
not speak up"* either.

The second reading is the one that matches why private submission and X-cards
exist as table practice at all. But it cannot be proven from a simulated player,
and the honest position is that the finding is **prompt-dependent** and the
design should be built for the worse case.

## Elias — the control

Genre, play style, lethality and signalling all held steady across trials 3 and
4. His question 7 answer flipped **back** to trial 1's — a redemption arc for a
distrusted NPC, after trial 3 produced a PC-centred one.

That calibrates the whole comparison: **question 7 is high-variance regardless of
hints.** Trial 3's wish-list divergence was noise, not an effect of anything.
Conversely, Sarah's, Marcus's and Chloe's changes sit against a control that did
*not* drift on safety, which is what lets them be read as hint effects rather
than randomness.

He also volunteered a technique nobody asked for: *"I'm genuinely fine narrating
around it in-character — 'she doesn't watch what happens next' — rather than
stopping the scene cold."* An in-fiction veil, which preserves pacing.

---

## What this changes

**1. For safety, the hint is the instrument, not the bias.** Trial 3 framed the
hints as contamination to be removed. Trial 4 says removing them *loses
information* rather than revealing truth: two of three findings disappeared or
inverted. A Session 0 questionnaire that waits for boundaries to be volunteered
will collect less than one that asks directly, and it will collect least from the
players who most need asking.

**2. Never cache a narrowing qualification.** Marcus narrowed his Line when
prompted and broadened it when not. `SafetyRegister.merged()` already keeps the
stricter reading of any disagreement — Line beats Veil, SETTING beats SCENE — and
this is the empirical case for that choice. It was a design instinct; it is now a
measured one.

**3. A gap that follows directly — since fixed.** `merged()` kept the stricter
*kind* and *scope* but merely accumulated notes, so Marcus's two readings would
both have landed in one note and contradicted each other in the prompt.

The rule now: **a narrowing note survives only if every reading carries the same
narrowing.** Any disagreement drops it and the constraint reverts to its
unqualified, strictest form. Widening notes still accumulate, since more of those
is never less safe. Whether a note narrows is a flag set at capture rather than
inferred from its wording — after three keyword-heuristic failures in a single
day, a boolean beats a regex.

A dropped narrowing sets `contested`, surfaced by `SafetyRegister.conflicts()`
**to the author and never to a prompt**. The prompt already has the safe answer;
a human should still know a boundary was described two ways and settle it.

**4. Trial 3's headline survives, with its reasoning corrected.** A safety
register is still the cacheable half and a contract still is not — but not
because safety answers are reproducible in the abstract. They are reproducible
*when asked well*, and the asking is part of the instrument.
