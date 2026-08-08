"""
What a deliverable needs, and in what order — the stop condition for generation.

World completeness is unreachable, so it is useless as a stop condition. A
contract is reachable and checkable: generation ends when every slot is filled,
and the AI canonizer is asked "does the contract still have unfilled slots?"
rather than "is this good?", which is unbounded and always answers yes.

The Session 0 trial (testing/session_zero/) built its contract as a list of
(type, count) and found three defects, each fixed by a field here:

  brief       A count says how many; it does not say which. The one
              regional_poi, briefed only as "the mine" in a print statement
              that never reached a prompt, generated a dimensional arch on a
              plateau.

  depends_on  A contract is a graph, not a list. `linguistic` sat sixth and
              `settlement` third, so the town was named before the naming
              rules existed; `regional_poi` sat before the factions and
              invented its own rival groups.

  tone        A type-and-count quota cannot ask for a place to have a meal.
              Warmth was requested in Session 0, was present in the shared
              agreements block, and every entity still came out grim, because
              faction, npc, creature and lore genomes all trend to conflict.

RuntimeDirectives holds the other half of what Session 0 produces: answers that
shape how the GM behaves at the table rather than what exists in the world.
"Give this faction equal stage time." "Recognise this player socially, not
mechanically." "This player's silence is not a distress signal." None of that
can be generated into an entity, and the trial had nowhere to put it.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Slot:
    """One requirement of the deliverable."""

    type: str                       # element type the forge can generate
    brief: str                      # what THIS slot is for, in the author's words
    count: int = 1
    depends_on: Tuple[str, ...] = ()  # slot keys that must exist first
    tone: str = ""                  # tonal mandate, where the genome will not supply one
    key: str = ""                   # identifier; defaults to `type`

    @property
    def name(self) -> str:
        return self.key or self.type

    def __post_init__(self):
        if not self.type.strip():
            raise ValueError("a slot needs a type")
        if not self.brief.strip():
            raise ValueError(
                f"slot {self.name!r} has no brief. A count says how many; it "
                f"does not say which, and an unbriefed slot is a free roll.")
        if self.count < 1:
            raise ValueError(f"slot {self.name!r} has count {self.count}")


@dataclass
class RuntimeDirectives:
    """
    Session 0 output that shapes GM behaviour rather than world content.

    Deliberately not part of the contract's slots: nothing here is generated,
    nothing here is "filled", and a directive is never done. It rides alongside.
    """

    pacing: List[str] = field(default_factory=list)
    spotlight: List[str] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    watchlist: List[str] = field(default_factory=list)

    def render(self) -> str:
        blocks = [("Pacing", self.pacing), ("Spotlight", self.spotlight),
                  ("Signals", self.signals), ("Watch for", self.watchlist)]
        out = []
        for label, items in blocks:
            if items:
                out.append(f"**{label}.**")
                out += [f"- {i}" for i in items]
                out.append("")
        return "\n".join(out).strip()

    def is_empty(self) -> bool:
        return not any((self.pacing, self.spotlight, self.signals, self.watchlist))


class ContractError(ValueError):
    pass


@dataclass
class ContentContract:
    """A deliverable's requirements, orderable and checkable."""

    deliverable: str
    slots: List[Slot] = field(default_factory=list)
    directives: RuntimeDirectives = field(default_factory=RuntimeDirectives)
    # Constraints that ride inside EVERY slot's brief.
    #
    # Trial 5 found why a shared context block is not enough. The table had
    # asked for room to breathe and relationships before stakes; that sat in
    # the global agreements block. The quest slot's brief asked for a hook that
    # puts the party in danger within the hour. The brief won, and two of four
    # players objected to the pace on reading the pitch.
    #
    # A brief is local and specific; a shared block is global and general, and
    # specific wins. So a constraint that must not be overridden has to compete
    # at the same level of specificity -- inside the brief, and stated as
    # outranking it.
    invariants: List[str] = field(default_factory=list)

    # ── shape ───────────────────────────────────────────────

    def by_name(self) -> Dict[str, Slot]:
        return {s.name: s for s in self.slots}

    def total_entities(self) -> int:
        return sum(s.count for s in self.slots)

    def validate(self, known_types: Optional[Sequence[str]] = None) -> None:
        names = [s.name for s in self.slots]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise ContractError(
                f"duplicate slot name(s) {sorted(duplicates)}; give one a `key`")
        known = set(names)
        for slot in self.slots:
            missing = [d for d in slot.depends_on if d not in known]
            if missing:
                raise ContractError(
                    f"slot {slot.name!r} depends on {missing}, which no slot provides")
        if known_types is not None:
            unknown = sorted({s.type for s in self.slots} - set(known_types))
            if unknown:
                raise ContractError(
                    f"no generator for type(s) {unknown}; a contract cannot "
                    f"require what the forge cannot make")
        self.ordered()  # raises on a cycle

    # ── order ───────────────────────────────────────────────

    def ordered(self) -> List[Slot]:
        """
        Dependency order, ties broken by declaration order so two runs of the
        same contract generate in the same sequence. Reproducibility is the
        point: an unstable order makes two runs incomparable, and the trial
        exists to be re-run against its own output.
        """
        slots = self.by_name()
        state: Dict[str, int] = {}   # 0 = visiting, 1 = done
        out: List[Slot] = []

        def visit(name: str, trail: Tuple[str, ...]):
            if state.get(name) == 1:
                return
            if state.get(name) == 0:
                cycle = " -> ".join(trail + (name,))
                raise ContractError(f"dependency cycle: {cycle}")
            state[name] = 0
            for dep in slots[name].depends_on:
                visit(dep, trail + (name,))
            state[name] = 1
            out.append(slots[name])

        for slot in self.slots:
            visit(slot.name, ())
        return out

    # ── completion ──────────────────────────────────────────

    def unfilled(self, made: Dict[str, int]) -> Dict[str, int]:
        """
        Slot name -> how many still owed. THE stop condition: generation is
        finished when this is empty, not when the world feels done.
        """
        return {s.name: s.count - made.get(s.name, 0)
                for s in self.slots if made.get(s.name, 0) < s.count}

    def is_satisfied(self, made: Dict[str, int]) -> bool:
        return not self.unfilled(made)

    # ── prompt fragment ─────────────────────────────────────

    def brief_for(self, slot: Slot, index: int = 0) -> str:
        """The per-slot block that goes into the decode context."""
        parts = [
            "## WHAT THIS PARTICULAR ENTITY IS FOR",
            "This is a specific slot in the campaign contract, not a free roll:",
            "",
            slot.brief.strip(),
        ]
        if slot.count > 1:
            parts.append(
                f"\nThis is number {index + 1} of {slot.count} in this slot. "
                f"It must be clearly distinct from the others, not a variation "
                f"on the same idea.")
        if slot.tone:
            parts.append(
                f"\n**Tonal requirement, which outranks the genome's default "
                f"pull toward conflict:** {slot.tone.strip()}")
        parts.append(
            "\nThe DNA supplies texture, variety and detail. Where the DNA and "
            "this brief disagree about WHAT THE THING IS, the brief wins and "
            "the DNA is read as flavour for it.")
        if self.invariants:
            parts.append(
                "\n### STANDING RULES — these outrank the brief above\n"
                "The brief says what this entity is. These say what it may not "
                "cost the table, and they win wherever the two pull apart. If "
                "satisfying the brief would break one of these, satisfy the "
                "rule and find another way to satisfy the brief.\n")
            parts += [f"- {rule.strip()}" for rule in self.invariants]
        return "\n".join(parts)
