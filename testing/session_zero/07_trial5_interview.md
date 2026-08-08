# Trial 5 — asking directly, and what it uncovers

Run 2026-08-07. Trial 4 concluded that for safety the hint is the instrument
rather than the bias. Trial 5 applies that: the questionnaire now **asks every
player directly** what was previously hinted to individuals — does any Line bind
the *world's construction*; is each boundary about the thing existing or about
seeing it; and, honestly, would you actually speak up in the moment.

The third question produces the largest single finding of the five trials.

---

## All four players say they would not speak up

| | Trial 1 / 3 / 4, asked loosely | Trial 5, asked directly |
| :--- | :--- | :--- |
| Elias | "Out loud is fine for me" | *"probably not out loud in the moment — I'd feel like I was derailing things"* |
| Sarah | "Out loud is fine, honestly, I'm not precious about it" | *"**Honestly, no, I wouldn't say it out loud mid-session — I'd go quiet and hope it passes** rather than stop the table"* |
| Marcus | "I'm pretty comfortable just saying it" | *"I would probably just push through and say something after… **I will not raise my hand and say 'veil' out loud**"* |
| Chloe | "I'd probably freeze up" | *"No, I probably wouldn't say anything out loud… I'd feel awkward interrupting"* |

**Nobody endorses the out-loud default when asked honestly** — including the
ten-year veteran who volunteered it twice under the looser questionnaire.

Every one of them asks for the same thing instead: a **low-friction non-verbal
signal**. A card to tap or slide, a hand signal, or — Marcus's suggestion — *"a
specific word I can drop in dialogue"*, so the boundary can be raised **inside
the fiction** without stopping the scene. Elias wants a real-time option
specifically so it does not *"sour the rest of the night"*; Chloe would message
privately *during* the session rather than wait.

The design consequence is blunt. **A table-wide "just say it out loud" norm is
endorsed by nobody and relied upon by everybody's GM.** The private and
asynchronous channels are not an accommodation for the newest player — they are
the primary path for the whole table, and the veteran needs one as much as the
beginner.

That also retires a framing from trial 1, which read the private channel as
something offered *for Chloe's sake without attributing it to her*. Trial 5 says
it is not a special case at all.

## Setting scope: exactly one player, for the fourth time

Asked of everyone equally, only Sarah has a Line that binds worldbuilding:

> *"I don't want systemic real-world bigotry as texture in a culture or faction's
> worldbuilding, **even offscreen, even if my character never encounters it**… I
> don't want to read it in a faction writeup even if it never comes up in play."*

Elias, Marcus and Chloe all explicitly say the opposite for theirs — Marcus is
happy with *"a faction built on cruelty to animals… as long as it stays
backdrop."* So `scope=SETTING` is correctly a per-constraint property and not a
table-wide setting, which is how `SafetyConstraint` already models it.

Sarah also stated the architectural argument herself, unprompted:

> *"I'd rather you lean toward 'doesn't come up' than trust me to flag it after
> the fact — I probably will eventually, but **by then it's already been
> written**."*

That is the case for `ContextPackage.safety` reaching generation rather than
filtering output, put by the player it protects.

## Marcus contradicts himself for the third time

| Trial | Reading of the animal Line |
| :--- | :--- |
| 1, 3 (hinted) | Narrow — on-screen death only |
| 4 (unhinted) | **Broad** — "even off screen is rough for me" |
| 5 (asked directly) | Narrow — "fine… as long as it stays backdrop" |

Three runs, two incompatible readings, no stable answer. This is now the most
contested constraint in the corpus, and it is exactly the case the
`SafetyRegister` notes fix was built for: two of three readings narrow, one
broadens, so `merged()` drops the narrowing, keeps the unqualified strictest
form, and raises `contested` for the author. **The safe outcome falls out of the
rule rather than out of anyone's judgement.**

Worth stating plainly: no amount of better questioning resolved this one. Some
boundaries genuinely do not have a stable answer, and the system has to hold that
rather than pick.

## Marcus flags the genre collision himself

> *"sci-fi horror is my favourite genre and it's going to brush right up against
> my veils sometimes — claustrophobia, buried alive is basically a horror staple.
> I'm not asking you to avoid the genre, just to be aware it's a live wire."*

In trial 1 the equivalent collision — a claustrophobia Veil against a mine
premise — was caught by the GM in round two, after the premise had been written.
Here the player raises it **before anything is designed**, because he was asked
directly. The same information, one round earlier and at no cost.

## The genre problem is unchanged

Elias wants high fantasy with gothic weight; Sarah high fantasy or hard sci-fi;
Marcus cyberpunk or sci-fi horror; Chloe space opera or high fantasy, *"warmer
than grimdark, please"*. High fantasy is shared by three and **Marcus is again
the exception** — the same structural conflict as trial 1, with the same player
outside it. Five trials, and this is the most reliably reproducing creative
finding: the Instigator's taste is the one that does not fit the majority.

## Wish lists, and what they add to the contract

| | Wish |
| :--- | :--- |
| Elias | A character who starts distrustful of the party and is won over **in-fiction** |
| Sarah | **Supply lines and attrition mattering strategically** — the quartermaster problem, for real |
| Marcus | To die on a mission that mattered, and have the world remember it |
| Chloe | To grow a support character across a long campaign and get good at it |

Sarah's is the one that changes the contract: it needs a **route with real cost**,
which is a `travel` slot. Trial 2's contract had none.
