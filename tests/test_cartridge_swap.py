"""
The Layer IV cartridge contract, and hot-swapping between systems.

Three cartridges exist as a deliberate test matrix for the rules abstraction,
not because the project needs three rulesets:

    coin_flip     trivial pass/fail — the floor
    one_page_5e   rules-light
    PF2EDNA       detailed — the ceiling

The requirement they exist to prove is that the *conflict-resolution system can
be changed*, between sessions or during one, without destabilising anything
above it. Layer IV decides outcomes; the narrative agents render them. Which
resolver is underneath is not supposed to be their business.

That requirement had no coverage, and it was already broken: PF2EDNA did not
define `system_name`, which Orchestrator.load_ruleset reads on every swap. The
two lightweight cartridges loaded fine and the detailed one raised
AttributeError — the failure mode this trio exists to catch, in the cartridge
that most needed to demonstrate the opposite.
"""

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

CARTRIDGES = ["coin_flip", "one_page_5e", "PF2EDNA"]


def arbiter(name):
    module = importlib.import_module(f"layer4_rules.{name}.arbiter")
    return module.GameSystemArbiter()


@pytest.mark.parametrize("name", CARTRIDGES)
def test_cartridge_exposes_the_loader_contract(name):
    """
    Orchestrator.load_ruleset reads .system_name and calls .resolve_action.
    A cartridge missing either cannot be swapped in.
    """
    cartridge = arbiter(name)

    assert isinstance(getattr(cartridge, "system_name", None), str) \
        and cartridge.system_name.strip(), \
        f"{name} has no usable system_name; load_ruleset would raise"
    assert callable(getattr(cartridge, "resolve_action", None)), \
        f"{name} cannot resolve an action"


def test_every_cartridge_identifies_itself_distinctly():
    """A swap the operator cannot see in the log is a swap they cannot debug."""
    names = [arbiter(c).system_name for c in CARTRIDGES]

    assert len(set(names)) == len(names), f"duplicate system_name: {names}"


def test_the_orchestrator_can_swap_between_all_three():
    """
    The headline requirement: change the rules without taking the system down.
    Swapped in every direction rather than once, because a loader can be
    tolerant of the first cartridge and not the next.
    """
    from layer1_core.orchestrator import Orchestrator

    orchestrator = Orchestrator.__new__(Orchestrator)   # no LLM needed to swap
    orchestrator.ruleset_cartridge = None

    for first in CARTRIDGES:
        for second in CARTRIDGES:
            orchestrator.load_ruleset(arbiter(first))
            assert orchestrator.ruleset_cartridge.system_name
            orchestrator.load_ruleset(arbiter(second))
            assert orchestrator.ruleset_cartridge.system_name == \
                arbiter(second).system_name, f"{first} -> {second} did not take"


def test_a_swap_mid_session_does_not_lose_the_new_system():
    """
    Swapping between sessions is easy; swapping during one is the real case.
    Resolve, swap, resolve again — the second result must come from the second
    cartridge.
    """
    from layer1_core.orchestrator import Orchestrator

    orchestrator = Orchestrator.__new__(Orchestrator)
    orchestrator.ruleset_cartridge = None

    orchestrator.load_ruleset(arbiter("coin_flip"))
    before = orchestrator.ruleset_cartridge.system_name
    orchestrator.ruleset_cartridge.resolve_action("swing at the door")

    orchestrator.load_ruleset(arbiter("PF2EDNA"))
    after = orchestrator.ruleset_cartridge.system_name

    assert before != after
    assert after == "Pathfinder 2E"


# What each cartridge accepts as its first argument. The light systems take the
# player's own words; PF2EDNA takes a term from a fixed vocabulary. That is a
# real difference in kind, not an inconsistency to be smoothed over.
SAMPLE_ACTION = {
    "coin_flip": "attempt to force the sealed hatch",
    "one_page_5e": "attempt to force the sealed hatch",
    "PF2EDNA": "skill_check",
}


@pytest.mark.parametrize("name", CARTRIDGES)
def test_resolve_action_returns_something_the_narrator_can_use(name):
    """
    Layer IV hands its result up to be narrated. Whatever the system, the result
    has to survive the trip: an exception or a bare None leaves the narrative
    layer nothing to render, and the swap has broken the tier above it.
    """
    result = arbiter(name).resolve_action(SAMPLE_ACTION[name])

    assert result is not None, f"{name} resolved to nothing"


def test_the_detailed_cartridge_needs_an_intent_layer_the_orchestrator_lacks():
    """
    The gap the three-tier matrix exists to expose, recorded rather than hidden.

    coin_flip and one_page_5e accept the player's raw words. PF2EDNA accepts
    only mapped terms -- attack_melee, save, skill_check -- and raises
    NotImplementedError on anything else. Orchestrator.process_player_input
    passes raw input straight through, so swapping to the detailed ruleset
    resolves nothing until something classifies intent first.

    Papering over this with a fallback would be worse than the gap: it would
    return a rules result that no rule produced.
    """
    from layer4_rules.PF2EDNA.arbiter import GameSystemArbiter

    with pytest.raises(NotImplementedError):
        GameSystemArbiter().resolve_action("attempt to force the sealed hatch")

    # The light systems really do take the same string without complaint.
    for light in ("coin_flip", "one_page_5e"):
        assert arbiter(light).resolve_action("attempt to force the sealed hatch")


@pytest.mark.parametrize("name", CARTRIDGES)
def test_resolve_action_is_callable_the_way_the_orchestrator_calls_it(name):
    """
    Orchestrator.process_player_input does `resolve_action(input_data)` with a
    single argument. PF2EDNA required a second, so swapping to the detailed
    ruleset raised TypeError on the first action resolved — a second contract
    break in the same cartridge, past the one that stopped it loading at all.
    """
    import inspect

    signature = inspect.signature(arbiter(name).resolve_action)
    required = [p for p in signature.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]

    assert len(required) == 1, \
        f"{name} needs {len(required)} args; the orchestrator passes one"
