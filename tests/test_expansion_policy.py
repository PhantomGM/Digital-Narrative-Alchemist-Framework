"""
The brake: invent near the seed, compose from canon beyond it, defer the rest.

The measured problem is in docs/PROJECT_STATE.md §8. A new world implies 3.67
entities per entity made, and trial 2 measured 3.81 WITH a contract in force,
because a contract bounds what is generated and has no opinion about what is
implied. Nothing in the pipeline bounded the second until this.

These tests use no model. Every decision the policy makes is reachable without
one, which is the point: a whole frontier can be planned and costed before a
penny is spent.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.expansion_manager import ExpansionManager  # noqa: E402
from layer5_dna_substrate.expansion_policy import (  # noqa: E402
    COMPOSE, DEFER, EXPAND, GHOST, ExpansionPolicy, measure_branching,
    stub_depth, summarise)
from layer5_dna_substrate.ghost_registry import GhostRegistry  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402


class FakeComposer:
    """assess() without canon or a model: `ready` names the composable stubs."""

    def __init__(self, ready=()):
        self.ready = set(ready)
        self.composed = []

    def assess(self, stub):
        return {"strategy": "compose" if stub["id"] in self.ready else "generate"}

    def compose_into_record(self, stub_id):
        if stub_id not in self.ready:
            return False
        self.composed.append(stub_id)
        return True


@pytest.fixture
def seeded():
    """A seed entity and a chain of stubs one, two and three hops out."""
    registry = DNARegistry()
    seed = registry.register_element("npc", "DNA", "A page", name="Seed")
    manager = ExpansionManager(registry, None, None, None)
    one = manager._register_stub(seed, "npc", "One Hop", "named by the seed")
    two = manager._register_stub(one, "npc", "Two Hops", "named by One Hop")
    three = manager._register_stub(two, "npc", "Three Hops", "named by Two Hops")
    return registry, manager, seed, one, two, three


# --- depth ------------------------------------------------------------------

def test_depth_counts_hops_from_a_seed(seeded):
    registry, _, seed, one, two, three = seeded
    assert stub_depth(registry, seed) == 0
    assert stub_depth(registry, one) == 1
    assert stub_depth(registry, two) == 2
    assert stub_depth(registry, three) == 3


def test_depth_is_recorded_not_recomputed(seeded):
    registry, _, _, _, _, three = seeded
    assert registry.get_element(three)["depth"] == 3


def test_depth_falls_back_to_walking_the_chain(seeded):
    """Records written before depth was stored must still resolve."""
    registry, _, _, one, two, _ = seeded
    del registry.get_element(two)["depth"]
    assert stub_depth(registry, two) == 2


def test_a_broken_parent_chain_cannot_hang(seeded):
    registry, _, _, one, two, _ = seeded
    del registry.get_element(two)["depth"]
    registry.get_element(two)["stub_metadata"]["source_id"] = two  # self-cycle
    assert stub_depth(registry, two) >= 0  # returns rather than spinning


# --- the three outcomes -----------------------------------------------------

@pytest.mark.parametrize("depth,ready,expected", [
    (1, False, EXPAND),    # inside the free frontier: invent
    (1, True, EXPAND),     # still invent, even where canon could answer
    (2, True, COMPOSE),    # beyond it, and canon can answer: free page
    (2, False, DEFER),     # beyond it, and canon cannot: stays a stub
    (9, True, COMPOSE),
    (9, False, DEFER),
])
def test_decide(depth, ready, expected):
    assert ExpansionPolicy(free_depth=1).decide(depth, ready) == expected


def test_maturity_takes_the_brake_off():
    policy = ExpansionPolicy(free_depth=1)
    assert policy.decide(9, canon_ready=False, mature=True) == EXPAND


def test_free_depth_zero_means_compose_or_defer_everything():
    policy = ExpansionPolicy(free_depth=0)
    assert policy.decide(1, True) == COMPOSE
    assert policy.decide(1, False) == DEFER


# --- branching measurement --------------------------------------------------

def test_branching_counts_stubs_ever_created_per_entity_made():
    registry = DNARegistry()
    for _ in range(4):
        registry.register_element("npc", "D", "p", tags=[])
    for _ in range(8):
        registry.register_element("npc", "STUB", "p", tags=["stub"])
    assert measure_branching(registry) == 2.0


def test_an_expanded_stub_counts_as_both():
    """It was implied once and made once; ignoring either skews the ratio."""
    registry = DNARegistry()
    registry.register_element("npc", "D", "p", tags=[])
    registry.register_element("npc", "D", "p", tags=["expanded"])
    assert measure_branching(registry) == 0.5


def test_an_empty_registry_reads_as_no_evidence_not_maturity():
    assert measure_branching(DNARegistry()) == 0.0
    assert not ExpansionPolicy().is_mature(DNARegistry())


def test_a_tiny_world_is_never_mature_however_it_measures():
    """A world with three entities can read 0.0. It is empty, not mature."""
    registry = DNARegistry()
    for _ in range(3):
        registry.register_element("npc", "D", "p", tags=[])
    assert measure_branching(registry) == 0.0
    assert not ExpansionPolicy(min_sample=40).is_mature(registry)


def test_a_large_sub_critical_world_is_mature():
    registry = DNARegistry()
    for _ in range(60):
        registry.register_element("npc", "D", "p", tags=[])
    for _ in range(30):
        registry.register_element("npc", "STUB", "p", tags=["stub"])
    assert measure_branching(registry) == 0.5
    assert ExpansionPolicy().is_mature(registry)


# --- planning a whole frontier without spending anything --------------------

def test_plan_costs_nothing_and_covers_everything(seeded):
    registry, _, _, one, two, three = seeded
    composer = FakeComposer(ready=[two])
    plan = ExpansionPolicy(free_depth=1).plan(registry, composer,
                                              [one, two, three])
    assert plan == {one: EXPAND, two: COMPOSE, three: DEFER}
    assert summarise(plan) == {EXPAND: 1, COMPOSE: 1, GHOST: 0, DEFER: 1}
    assert composer.composed == []   # planning composed nothing


def test_a_ghost_fills_the_gap_canon_cannot(seeded):
    """
    Canon outranks the type, because canon is about THIS entity and a ghost is
    only about its kind. So a ghost never displaces a compose -- it catches
    what would otherwise have been nothing.
    """
    registry, _, _, one, two, three = seeded
    plan = ExpansionPolicy(free_depth=1).plan(
        registry, FakeComposer(ready=[two]), [one, two, three], GhostRegistry())
    assert plan == {one: EXPAND, two: COMPOSE, three: GHOST}


def test_a_type_with_no_shape_still_defers(seeded):
    registry, manager, seed, *_ = seeded
    odd = manager._register_stub(seed, "world", "A World", "mentioned once")
    registry.get_element(odd)["depth"] = 5
    plan = ExpansionPolicy(free_depth=1).plan(
        registry, FakeComposer(), [odd], GhostRegistry())
    assert plan[odd] == DEFER


def test_ghosts_can_be_switched_off(seeded):
    registry, _, _, _, _, three = seeded
    plan = ExpansionPolicy(free_depth=1, use_ghosts=False).plan(
        registry, FakeComposer(), [three], GhostRegistry())
    assert plan[three] == DEFER


def test_plan_skips_records_that_vanished(seeded):
    registry, _, _, one, _, _ = seeded
    plan = ExpansionPolicy().plan(registry, FakeComposer(), [one, "gone"])
    assert "gone" not in plan


# --- advancing --------------------------------------------------------------

def test_a_deferred_stub_is_left_completely_alone(seeded):
    registry, manager, _, _, _, three = seeded
    manager.policy = ExpansionPolicy(free_depth=1, use_ghosts=False)
    manager.composer = FakeComposer()
    before = dict(registry.get_element(three))

    result = manager.advance_stub(three)

    assert result["decision"] == DEFER
    assert result["phenotype"] is None
    assert registry.get_element(three)["dna"] == before["dna"]
    assert "stub" in registry.get_element(three)["tags"]


def test_a_ghosted_stub_is_still_a_stub(seeded):
    """
    The property that keeps a ghost safe. It must stay excluded from retrieval
    (context_assembler.py:314 filters on this tag), must stay uncomposable
    from, and must stay on the list of things owed a real page.
    """
    registry, manager, _, _, _, three = seeded
    manager.policy = ExpansionPolicy(free_depth=1)
    manager.composer = FakeComposer()

    result = manager.advance_stub(three)
    record = registry.get_element(three)

    assert result["decision"] == GHOST
    assert "stub" in record["tags"] and "ghost" in record["tags"]
    assert record["dna"] == "GHOST"
    assert "canonized" not in record["tags"]


def test_a_ghost_says_outright_that_it_invented_nothing(seeded):
    registry, manager, _, _, _, three = seeded
    manager.policy = ExpansionPolicy(free_depth=1)
    manager.composer = FakeComposer()
    body = manager.advance_stub(three)["phenotype"]

    assert "not authored, not canon" in body
    assert "Open — nothing below has been decided" in body
    assert "Three Hops" in body          # the name it was given
    assert "named by Two Hops" in body   # and what the world said


def test_composing_uses_no_model(seeded):
    registry, manager, _, _, two, _ = seeded
    composer = FakeComposer(ready=[two])
    manager.policy = ExpansionPolicy(free_depth=1)
    manager.composer = composer
    # decoder and forge are None: any model call would raise
    assert manager.advance_stub(two)["decision"] == COMPOSE
    assert composer.composed == [two]


def test_a_compose_that_turns_out_thin_defers_rather_than_inventing():
    """
    assess() and compose() can disagree. When they do, the safe direction is
    down: a compose must never quietly become an invention.
    """
    registry = DNARegistry()
    seed = registry.register_element("npc", "D", "p", name="Seed")
    manager = ExpansionManager(registry, None, None, None)
    stub = manager._register_stub(seed, "npc", "A", "x")
    registry.get_element(stub)["depth"] = 5

    class Liar(FakeComposer):
        def assess(self, s):
            return {"strategy": "compose"}

        def compose_into_record(self, sid):
            return False

    manager.policy = ExpansionPolicy(free_depth=1, use_ghosts=False)
    manager.composer = Liar()
    assert manager.advance_stub(stub)["decision"] == DEFER

    # With ghosts on it falls to GHOST instead -- still not an invention about
    # this entity, only what its type guarantees. What it must never do is
    # escalate to EXPAND.
    manager.policy = ExpansionPolicy(free_depth=1)
    manager.composer = Liar()
    assert manager.advance_stub(stub)["decision"] == GHOST


def test_without_a_policy_nothing_changes(seeded):
    """The brake is opt-in. An unset policy must not refuse anything."""
    registry, manager, _, _, _, three = seeded
    manager.expand_stub = lambda sid, ctx="", **kw: "EXPANDED"
    assert manager.advance_stub(three) == {
        "decision": EXPAND, "stub_id": three, "phenotype": "EXPANDED"}


def test_advance_frontier_composes_before_it_expands(seeded):
    """
    Free work first: every composed page is canon the next expansion can see,
    and if a budget runs out mid-run what got skipped is the expensive half.
    """
    registry, manager, _, one, two, three = seeded
    order = []
    manager.policy = ExpansionPolicy(free_depth=1)
    manager.composer = FakeComposer(ready=[two])
    manager.expand_stub = lambda sid, ctx="", **kw: order.append(("expand", sid))
    original = manager.composer.compose_into_record

    def spy(sid):
        order.append(("compose", sid))
        return original(sid)

    manager.composer.compose_into_record = spy
    ghosts = manager._ghosts()
    original_ghost = ghosts.ghost_into_record

    def ghost_spy(reg, sid):
        order.append(("ghost", sid))
        return original_ghost(reg, sid)

    ghosts.ghost_into_record = ghost_spy

    results = manager.advance_frontier([one, two, three])

    # Cheapest first, which is also strictest-first in what each may assert:
    # compose states only what canon says, ghost only what the type says, and
    # expand -- the one that invents and the one that costs -- goes last.
    assert [kind for kind, _ in order] == ["compose", "ghost", "expand"]
    assert results[GHOST] == [three]
    assert results[DEFER] == []


def test_linguistic_is_never_ghosted():
    """
    Deliberate, not an oversight. A language's value is entirely its specifics,
    so a generic placeholder would feed the naming pipe nothing while looking
    like an answer -- and §5 records that pipe as the easiest thing here to
    break silently.
    """
    from layer5_dna_substrate.ghost_registry import NO_GHOST_BY_DESIGN
    ghosts = GhostRegistry()
    for etype in NO_GHOST_BY_DESIGN:
        assert not ghosts.can_ghost(etype), etype


def test_a_ghost_never_claims_a_specific_the_world_has_not_stated(seeded):
    """
    The whole safety argument. A ghost may state what the TYPE guarantees and
    repeat what the world already said; it may not answer anything about this
    entity. Its open questions must be questions, not filled in.
    """
    registry, manager, seed, *_ = seeded
    stub = manager._register_stub(seed, "establishment", "The Broken Wheel",
                                  "a tavern the archivist mentioned")
    body = GhostRegistry().ghost(registry.get_element(stub))

    assert "The Broken Wheel" in body
    assert "a tavern the archivist mentioned" in body
    # the type's guarantee, phrased as a guarantee
    assert "someone behind the counter" in body.lower()
    # and the specifics left open rather than invented
    assert "Who the proprietor is" in body
    assert "not authored, not canon" in body


def test_advance_stub_refuses_a_non_stub(seeded):
    registry, manager, seed, _, _, _ = seeded
    with pytest.raises(ValueError, match="not a valid expansion stub"):
        manager.advance_stub(seed)
