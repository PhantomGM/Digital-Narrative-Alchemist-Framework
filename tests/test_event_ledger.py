"""
Unit tests for the Event Ledger (Bucket C).
Tests state delta emission, retrieval, filtering, and snapshot reconstruction.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.event_ledger import EventLedger, StateEvent


def test_emit_and_get_recent():
    """Events can be emitted and retrieved in chronological order."""
    ledger = EventLedger()

    for i in range(5):
        ledger.emit(StateEvent(
            event_type="UPDATE_ENTITY",
            target=f"entity_{i}",
            delta={"hp": 100 - i * 10},
            source_agent="TestAgent",
            location="TestRoom"
        ))

    assert ledger.event_count == 5
    recent_3 = ledger.get_recent(3)
    assert len(recent_3) == 3
    assert recent_3[0].target == "entity_2"
    assert recent_3[2].target == "entity_4"
    print("✓ test_emit_and_get_recent passed")


def test_get_by_target():
    """Events can be filtered by target entity."""
    ledger = EventLedger()

    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="goblin", delta={"hp": 50}, source_agent="A", location="cave"))
    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="player", delta={"hp": 100}, source_agent="A", location="cave"))
    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="goblin", delta={"hp": 30}, source_agent="A", location="cave"))

    goblin_events = ledger.get_by_target("goblin")
    assert len(goblin_events) == 2
    assert all(e.target == "goblin" for e in goblin_events)
    print("✓ test_get_by_target passed")


def test_get_by_location():
    """Events can be filtered by location."""
    ledger = EventLedger()

    ledger.emit(StateEvent(event_type="X", target="a", delta={}, source_agent="A", location="cave"))
    ledger.emit(StateEvent(event_type="X", target="b", delta={}, source_agent="A", location="tavern"))
    ledger.emit(StateEvent(event_type="X", target="c", delta={}, source_agent="A", location="cave"))

    cave_events = ledger.get_by_location("cave")
    assert len(cave_events) == 2
    print("✓ test_get_by_location passed")


def test_snapshot():
    """Snapshot replays events into a flattened state dict."""
    ledger = EventLedger()

    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="goblin", delta={"hp": 50, "status": "alive"}, source_agent="A", location="cave"))
    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="goblin", delta={"hp": 30}, source_agent="A", location="cave"))
    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="player", delta={"hp": 100}, source_agent="A", location="cave"))

    snap = ledger.snapshot(location="cave")
    assert snap["goblin"]["hp"] == 30  # Latest value wins
    assert snap["goblin"]["status"] == "alive"  # Earlier value preserved
    assert snap["player"]["hp"] == 100
    print("✓ test_snapshot passed")


def test_remove_entity_in_snapshot():
    """REMOVE_ENTITY events mark entities as removed in snapshot."""
    ledger = EventLedger()

    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="goblin", delta={"hp": 50}, source_agent="A", location="cave"))
    ledger.emit(StateEvent(event_type="REMOVE_ENTITY", target="goblin", delta={}, source_agent="A", location="cave"))

    snap = ledger.snapshot(location="cave")
    assert snap["goblin"].get("_removed") is True
    print("✓ test_remove_entity_in_snapshot passed")


def test_render_context():
    """render_context() produces a formatted string."""
    ledger = EventLedger()

    ledger.emit(StateEvent(event_type="UPDATE_ENTITY", target="goblin", delta={"hp": 30}, source_agent="CombatResolver", location="cave"))

    ctx = ledger.render_context(5)
    assert "RECENT STATE CHANGES" in ctx
    assert "CombatResolver" in ctx
    assert "goblin" in ctx
    print("✓ test_render_context passed")


def test_max_events_pruning():
    """Ledger prunes old events beyond max_events."""
    ledger = EventLedger(max_events=5)

    for i in range(10):
        ledger.emit(StateEvent(event_type="X", target=f"e{i}", delta={}, source_agent="A", location="L"))

    assert ledger.event_count == 5
    assert ledger.get_recent(5)[0].target == "e5"  # First 5 were pruned
    print("✓ test_max_events_pruning passed")


if __name__ == "__main__":
    test_emit_and_get_recent()
    test_get_by_target()
    test_get_by_location()
    test_snapshot()
    test_remove_entity_in_snapshot()
    test_render_context()
    test_max_events_pruning()
    print("\n✅ All EventLedger tests passed!")
