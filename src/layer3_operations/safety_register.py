"""
The table's Lines and Veils, in a shape that can hold what players actually say.

`PlayerProfileManager` stored one flat list of strings per player and merged
them with `aggregate_safety_boundaries`. The Session 0 trial produced four
distinctions in a single interview, and that structure could represent none of
them:

  - A LINE forbids; a VEIL defers. Merged into one list, the governor received
    "graphic torture" and "sexual violence" as indistinguishable text, with
    nothing to say whether the answer is "never" or "fade to black".
  - One player's animal Line was about ON-SCREEN DEATH, not about animals
    existing: "please don't make me watch a pet die on screen".
  - One player's bigotry Line bound the SETTING, not scenes: "even if no one's
    PC ever encounters it directly". A scene-level filter cannot catch that,
    because the offending culture page reads perfectly well on its own.
  - One player could not raise a Veil aloud at all, so who holds a constraint
    must never reach the page.

Hence: kind, scope, and a note, and holders recorded but never rendered.

This lives in Layer III beside the profiles and hands Layer V a finished
string, the same way the naming rules do. Layer V never imports Layer III.
"""

from dataclasses import dataclass, field
from typing import List, Sequence

LINE, VEIL = "line", "veil"
SCENE, SETTING = "scene", "setting"

_HEADER = (
    "## BINDING SAFETY CONSTRAINTS\n"
    "These outrank the DNA, the surrounding canon, and every other instruction\n"
    "in this prompt. Where anything below conflicts with anything above it,\n"
    "these win. They are not preferences and there is no budget under which\n"
    "they may be traded away."
)

_LINE_INTRO = (
    "**LINES — must never appear, in any form.** Not as an on-screen event, an\n"
    "implication, a historical fact, a rumour, or background texture. Do not\n"
    "write around them; write something else."
)

_VEIL_INTRO = (
    "**VEILS — may exist in the fiction, but must be referred to and never\n"
    "depicted.** Name the fact and cut away from the experience. Nobody has to\n"
    "ask for the transition; take it as given. When uncertain, cut earlier."
)


@dataclass(frozen=True)
class SafetyConstraint:
    text: str
    kind: str = LINE                 # LINE (forbid) or VEIL (defer)
    scope: str = SCENE               # SCENE (depiction) or SETTING (worldbuilding too)
    note: str = ""                   # the player's own qualification
    holders: Sequence[str] = ()      # recorded, NEVER rendered into a prompt

    def __post_init__(self):
        if self.kind not in (LINE, VEIL):
            raise ValueError(f"kind must be {LINE!r} or {VEIL!r}, got {self.kind!r}")
        if self.scope not in (SCENE, SETTING):
            raise ValueError(f"scope must be {SCENE!r} or {SETTING!r}, got {self.scope!r}")
        if not self.text.strip():
            raise ValueError("a constraint needs text")

    def rendered(self) -> str:
        body = self.text.strip().rstrip(".")
        if self.scope == SETTING:
            body += (". This binds the SETTING, not only scenes: it must not be "
                     "built into a culture, faction, history or place as "
                     "background flavour, even where no character encounters it")
        if self.note:
            body += f". {self.note.strip().rstrip('.')}"
        return f"- {body}."


@dataclass
class SafetyRegister:
    """Every constraint at the table, merged across players."""

    constraints: List[SafetyConstraint] = field(default_factory=list)

    def add(self, constraint: SafetyConstraint) -> "SafetyRegister":
        self.constraints.append(constraint)
        return self

    def lines(self) -> List[SafetyConstraint]:
        return [c for c in self.constraints if c.kind == LINE]

    def veils(self) -> List[SafetyConstraint]:
        return [c for c in self.constraints if c.kind == VEIL]

    def merged(self) -> "SafetyRegister":
        """
        One entry per distinct text, keeping the STRICTER reading of every
        difference: a Line beats a Veil, SETTING scope beats SCENE, and notes
        accumulate. Two players sharing a boundary must never weaken it --
        three of the four trial players listed sexual violence, and one of
        them qualified it further.
        """
        by_text = {}
        for c in self.constraints:
            key = " ".join(c.text.lower().split()).rstrip(".")
            prior = by_text.get(key)
            if prior is None:
                by_text[key] = c
                continue
            notes = [n for n in (prior.note, c.note) if n]
            by_text[key] = SafetyConstraint(
                text=prior.text,
                kind=LINE if LINE in (prior.kind, c.kind) else VEIL,
                scope=SETTING if SETTING in (prior.scope, c.scope) else SCENE,
                note=" ".join(dict.fromkeys(notes)),
                holders=tuple(dict.fromkeys(tuple(prior.holders) + tuple(c.holders))),
            )
        return SafetyRegister(list(by_text.values()))

    def render(self) -> str:
        """
        The block handed to ContextPackage.safety.

        Holders are deliberately absent. A veil is often private -- one trial
        player said outright she could not raise hers aloud -- and a prompt
        that names who asked for what puts it back in the room.
        """
        merged = self.merged()
        if not merged.constraints:
            return ""
        out = [_HEADER, "", _LINE_INTRO, ""]
        lines = merged.lines()
        out += [c.rendered() for c in lines] if lines else ["- (none recorded)"]
        out += ["", _VEIL_INTRO, ""]
        veils = merged.veils()
        out += [c.rendered() for c in veils] if veils else ["- (none recorded)"]
        return "\n".join(out)

    def fit(self, budget_chars: int) -> str:
        """
        If the block ever has to shrink, drop WHOLE constraints by priority --
        veils before lines, and scene-scope before setting-scope -- rather than
        cutting text. A character cap once severed the last taboo of the
        language block twice; half a Line is worse than none.

        This should not fire. ContextPackage.safety takes no share of
        budget_tokens. It exists so that if some caller ever imposes one, the
        failure is a dropped item and not a truncated sentence.
        """
        rendered = self.render()
        if len(rendered) <= budget_chars:
            return rendered

        def priority(c):
            return (0 if c.kind == LINE else 1,
                    0 if c.scope == SETTING else 1)

        ordered = sorted(self.merged().constraints, key=priority)
        keep = []
        for c in ordered:
            if len(SafetyRegister(keep + [c]).render()) > budget_chars:
                break
            keep.append(c)

        # The header and both intros are a fixed ~600 characters, so a small
        # enough budget fits NOTHING and this would return an empty block --
        # silently removing every constraint, which is the one outcome worse
        # than the overflow it was avoiding. Overspending a budget is
        # recoverable; a prompt with no Lines in it is not. So the Lines are a
        # floor: they go in whether they fit or not.
        if not any(c.kind == LINE for c in keep):
            lines = [c for c in ordered if c.kind == LINE]
            if lines:
                return SafetyRegister(lines).render()
        return SafetyRegister(keep).render()
