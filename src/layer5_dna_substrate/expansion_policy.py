"""
When to invent, when to compose from canon, and when to leave a stub alone.

The measured problem (docs/PROJECT_STATE.md §8): a NEW world implies 3.67
entities for every entity it makes. Fifteen entities implied fifty-five stubs;
sixteen implied sixty-one. Expand those and they imply two hundred more. The
mature world's 0.97 is sub-critical only because `find_by_name` dedupe needs a
populated registry to bite, and a fresh world has nothing to dedupe against.

The contract does not solve this. Trial 2 measured 3.81 with a contract in
force, because a contract bounds what is GENERATED and has no opinion about
what is IMPLIED. So the bound has to live here, on the expansion side.

Three outcomes for any stub:

  EXPAND    Tier 1. Roll DNA, call the model, write a real page. Costs money.
  COMPOSE   Tier 2. Canon already says enough; assemble a page from it with no
            DNA and no model call. CanonComposer measured 17 of 42 pending
            stubs answerable this way on the live world -- 40%, free.
  DEFER     Tier 2, and canon cannot answer. The stub stays a stub. This is a
            success, not a failure: a stub costs one registry row, and
            context_assembler.py:314 excludes stubs from retrieval, so it can
            never leak into a prompt and be described into existence.

The depth cut-off is deliberately shallow. A player's mentor gets a page; the
mentor's rival gets a row. That is the whole brake -- everything past the
frontier is either free or postponed, and neither costs a model call.
"""

from dataclasses import dataclass
from typing import Dict, Optional

EXPAND = "expand"
COMPOSE = "compose"
GHOST = "ghost"
DEFER = "defer"

# Cheapest-first, and that is also strictest-first in what each is allowed to
# assert. COMPOSE states only what canon already says. GHOST states only what
# the type guarantees. DEFER states nothing. EXPAND is the one that invents,
# and it is the one that costs.
_ORDER = (COMPOSE, GHOST, EXPAND, DEFER)


def stub_depth(registry, entity_id: str) -> int:
    """
    Hops from a seed. Entities the contract generated directly are 0; a stub
    they named is 1; a stub named by that stub's page is 2.

    Reads the stored value, falling back to walking `source_id` for records
    written before depth was recorded. The walk is bounded, because a corrupt
    parent chain must not hang a run.
    """
    record = registry.get_element(entity_id)
    if not record:
        return 0
    if "depth" in record:
        return int(record["depth"])

    depth, seen, current = 0, {entity_id}, record
    while depth < 64:
        source = (current.get("stub_metadata") or {}).get("source_id")
        if not source or source in seen:
            return depth
        seen.add(source)
        current = registry.get_element(source)
        if not current:
            return depth
        depth += 1
        if "depth" in current:
            return int(current["depth"]) + depth
    return depth


def measure_branching(registry) -> float:
    """
    Stubs ever created per entity actually made — the number §8 turns on.

    Counts stub records ever created (pending plus already expanded) against
    made entities, which is what was measured to get 0.97 on the live world and
    3.67 on a new one. Returns 0.0 for an empty registry rather than dividing
    by zero, so a fresh world reads as "no evidence" and not as "mature".
    """
    made = stubs = 0
    for record in registry._records.values():
        tags = record.get("tags") or []
        if "stub" in tags:
            stubs += 1
        else:
            made += 1
            if "expanded" in tags:
                stubs += 1
    return stubs / made if made else 0.0


@dataclass(frozen=True)
class ExpansionPolicy:
    """
    free_depth       How many hops from a seed may be freely invented. 1 means
                     the things a seeded entity names get pages; the things
                     THOSE name do not. Trial 2's sixteen entities named 61
                     stubs; at free_depth=1 that is the whole invention budget
                     and the generation after it costs nothing.

    mature_branching Below this measured branching factor, the world dedupes
                     faster than it grows and the brake can come off. The
                     figure is 1.0 because that is the critical threshold of a
                     branching process, not because a world "feels" mature --
                     PROJECT_STATE deliberately does not hardcode an entity
                     count, since two data points do not locate a crossover.

    min_sample       Do not trust a branching measurement taken on almost
                     nothing. A world with three entities can read 0.0 and is
                     not mature; it is empty.

    use_ghosts       Whether a stub beyond the frontier that canon cannot
                     answer should get a type-shaped placeholder rather than
                     nothing. On a NEW world this is the difference between a
                     usable frontier and an empty one: measured on trial 2,
                     canon composed 0 of 58 stubs, because CanonComposer reads
                     only `canonized` records and a fresh world has none.
    """

    free_depth: int = 1
    mature_branching: float = 1.0
    min_sample: int = 40
    use_ghosts: bool = True

    def is_mature(self, registry) -> bool:
        made = sum(1 for r in registry._records.values()
                   if "stub" not in (r.get("tags") or []))
        if made < self.min_sample:
            return False
        return measure_branching(registry) < self.mature_branching

    def decide(self, depth: int, canon_ready: bool, mature: bool = False,
               ghostable: bool = False) -> str:
        """
        EXPAND inside the free frontier or once the world is self-limiting.
        Beyond it: COMPOSE where canon can answer, GHOST where the type can,
        and DEFER where neither can.

        Canon outranks the type because canon is about *this* entity while a
        ghost is only about its kind. A ghost is the floor, not a substitute.
        """
        if mature or depth <= self.free_depth:
            return EXPAND
        if canon_ready:
            return COMPOSE
        if ghostable and self.use_ghosts:
            return GHOST
        return DEFER

    def plan(self, registry, composer, stub_ids, ghosts=None) -> Dict[str, str]:
        """
        Decide for many stubs at once, without generating anything.

        Cheap by construction: `CanonComposer.assess` makes no model call and
        neither does a ghost, so a whole frontier can be planned and costed
        before a penny is spent.
        """
        mature = self.is_mature(registry)
        out: Dict[str, str] = {}
        for stub_id in stub_ids:
            record = registry.get_element(stub_id)
            if not record:
                continue
            depth = stub_depth(registry, stub_id)
            ready = ghostable = False
            if not mature and depth > self.free_depth:
                if composer is not None:
                    ready = composer.assess(record)["strategy"] == "compose"
                if not ready and ghosts is not None:
                    ghostable = ghosts.can_ghost(record.get("type") or "")
            out[stub_id] = self.decide(depth, ready, mature, ghostable)
        return out


def summarise(plan: Dict[str, str]) -> Dict[str, int]:
    counts = {EXPAND: 0, COMPOSE: 0, GHOST: 0, DEFER: 0}
    for decision in plan.values():
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def order_cheapest_first(plan: Dict[str, str]):
    """Stub ids grouped so the free work happens before the paid work."""
    return [i for step in _ORDER for i, d in plan.items() if d == step]
