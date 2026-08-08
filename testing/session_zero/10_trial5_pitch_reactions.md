# Trial 5 — the pitch, and what four readers found that probes did not

All four players accepted. The useful part is what they objected to, because
three of the four objections are defects no automated check in this repo would
have caught.

---

## Accepted, with the contract's promises kept

**Sarah — the quartermaster problem is real, not dressing.** *"The Low-Draw Lane
versus faster routes is exactly the trade I asked for, distance-as-cost with the
consequence living six days downstream of the choice that caused it."* The
`travel` slot existed only because she asked for it in the interview, and it is
the first `travel` entity any trial has produced.

She also confirmed the asymmetry, and named why it works: *"nobody's a bystander
because Ribbon-Way doesn't even care about my job; they're squeezing the table I
eat at regardless of what I do out in the drift."*

**Elias — the structure survived the genre change.** He asked for high fantasy
with gothic weight and got science fiction. *"It survived better than I
expected… a sector that got written off by people who ran the numbers and decided
the survivors weren't worth the fuel is exactly that, just with vacuum instead of
moors. **I didn't lose the vibe, I lost the word 'kingdom'.**"*

That is the strongest evidence yet that what Session 0 elicits is **structure**,
and genre is the skin over it. Trial 1 built a mining town; trial 5 built a
salvage station; both came out as *a warm room, a dark place below, and three
powers that want incompatible things*. Same shape, different words.

## Three defects the readers found

### 1. "No pre-assigned arcs" failed, and only a reader could tell

The NPC brief said no arc may be visibly pre-assigned. Trial 2's Elias confirmed
it held — *"none of the three reads as pre-turned."* Trial 5's Elias says one of
them does:

> *"Finch reads a little pre-loaded — three erased names and stained fingers is a
> lot of neon for a first mention, feels like the GM's already picked who I'm
> supposed to suspect."*

No probe detects this. There is no token to grep for; the page is well written
and the defect is that it is *too* legible. It needs a reader, and it is the
clearest case in five trials for keeping human review in the loop rather than
trusting the checks.

### 2. The opening hook was flagged by two of four, independently

- Elias: *"the hourly ticking clock is a very optimization-brained hook for a
  table that wants to sit in a booth and talk."*
- Chloe: *"a lot of 'everyone's going to be furious with us' stacked into hour
  one… I'm quietly hoping our first real choice isn't already making three
  factions mad before I've learned anyone's name."*

The `quest` slot's brief asked for a hook that puts the crew aboard a hulk in the
first hour. It got one. What it did **not** carry was the table's stated pacing —
room to breathe, relationships before stakes — even though that was in the shared
agreements block. **A slot brief can pull against a table agreement and win**,
because the brief is local and specific and the agreements are global and
general. That is a contract-design finding: pacing constraints need to reach the
slots that can violate them.

### 3. One warm room is not a warm ratio

Chloe accepted the Butter-Burner and then put the problem precisely:

> *"The warmth is one room and everything outside it is debt ledgers and cartels
> that wrote us off… I just hope we get to be in that room a lot and not just
> pass through it between bad news."*

`Slot.tone` fixed the *absence* of warmth, which was trial 1's defect. It does
not address **proportion** — one warm slot among seventeen is present and
outnumbered. Tone may need to be a property of the contract as a whole rather
than only of individual slots.

## Marcus refines the veil, and the block over-corrected

This is the most operationally useful response in the trial. The safety block
forbade *"any scene whose tension is whether they can get out"*, and the
generation obeyed completely — zero enclosure passages in seventeen pages.
Marcus's actual want is narrower than that:

> *"Boarding sealed derelicts is basically the premise, and I'm not asking you to
> cut that, I **want** that. What I need is: when I'm crawling through a collapsed
> corridor with the hull groaning and no way back — that's the moment to check in,
> maybe dial the sensory detail down a notch, keep the scene moving rather than
> lingering in the tight dark. **Doesn't need a big pause, just don't marinate in
> it.**"*

So this veil is about **duration and emphasis**, not about existence
(`scope=SETTING`) or visibility (on-screen versus off). It is a third kind:
*the thing may happen, may be shown, and must not be dwelt upon.* Neither
`scope` nor `narrows` expresses that, and the current register can only encode it
as prose in `note` — which is what it did, and which worked, but by luck rather
than by structure.

It is also a **runtime** constraint as much as a generation one: "check in with
me at that moment" is something a GM does, not something a world contains. It
belongs in `RuntimeDirectives` as well as in the safety block.

## Sarah asks for the canon-safety rule by name

Unprompted, about the lore page:

> *"The Song of the Cold Hearth is doing careful work and I want it to stay
> careful — 'protective blanket laid by something that loved them' is a folk
> explanation, not confirmed lore, and I'd like it to keep being **contested
> rather than revealed as simply true**."*

That is PROJECT_STATE's canon-safety rule — *never resolve a question the setting
leaves open* — requested by a player who has never seen it. It currently sits in
only a handful of decoders. This is an argument for propagating it, and for
carrying it as a runtime directive too, since the risk continues for as long as
the campaign does.

## The frontier

49 stubs, all ghosted, none deferred, and every one of them still carries its
`stub` tag, still has `dna == "GHOST"`, and none is canonized — so none can leak
into retrieval or be composed from. Sample, for The Butter-Burner's own ghost:

> *"Nothing here was written about this entity. It records what being an
> `establishment` guarantees… Do not cite it as evidence for anything."*
