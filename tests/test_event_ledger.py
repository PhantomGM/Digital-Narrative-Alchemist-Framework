"""
Unit tests for the Event Ledger (Bucket C).
Tests state delta emission, retrieval, filtering, and snapshot reconstruction.

The ledger is async and aiosqlite-backed. These tests were originally written
against a synchronous in-memory implementation and called the coroutines without
awaiting them, so every assertion ran against a coroutine object. Each test now
gets its own database file — the default is a "dna_ledger.db" in the working
directory, which would leak state between tests and into the repo.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer2_narrative.event_ledger import EventLedger, StateEvent  # noqa: E402

pytestmark = pytest.mark.anyio


@pytest.fixture
async def ledger(tmp_path):
    """A fresh, initialized ledger backed by an isolated database file."""
    led = EventLedger(db_path=str(tmp_path / "ledger.db"))
    await led.initialize_db()
    return led


def event(target="goblin", event_type="UPDATE_ENTITY", delta=None,
          agent="TestAgent", location="cave"):
    return StateEvent(
        event_type=event_type,
        target=target,
        delta={} if delta is None else delta,
        source_agent=agent,
        location=location,
    )


# --- emission and retrieval -------------------------------------------------

async def test_emit_and_get_recent(ledger):
    """Events can be emitted and retrieved in chronological order."""
    for i in range(5):
        await ledger.emit(event(target=f"entity_{i}", delta={"hp": 100 - i * 10}))

    assert await ledger.event_count() == 5

    recent_3 = await ledger.get_recent(3)
    assert len(recent_3) == 3
    assert recent_3[0].target == "entity_2"
    assert recent_3[2].target == "entity_4"


async def test_get_recent_is_insertion_ordered(ledger):
    """
    Ordering must not depend on time.time(), which collides under rapid emits
    and would make the sequence non-deterministic.
    """
    for i in range(10):
        await ledger.emit(event(target=f"e{i}"))

    targets = [e.target for e in await ledger.get_recent(10)]
    assert targets == [f"e{i}" for i in range(10)]


async def test_emit_round_trips_all_fields(ledger):
    original = event(target="goblin", delta={"hp": 30, "status": "bleeding"},
                     agent="CombatResolver", location="cave")
    await ledger.emit(original)

    (stored,) = await ledger.get_recent(1)
    assert stored.event_id == original.event_id
    assert stored.event_type == original.event_type
    assert stored.target == original.target
    assert stored.delta == {"hp": 30, "status": "bleeding"}
    assert stored.source_agent == "CombatResolver"
    assert stored.location == "cave"
    assert stored.timestamp == pytest.approx(original.timestamp)


async def test_empty_ledger_returns_nothing(ledger):
    assert await ledger.get_recent(10) == []
    assert await ledger.event_count() == 0
    assert await ledger.get_last_timestamp() == 0.0


# --- filtering --------------------------------------------------------------

async def test_get_by_target(ledger):
    """Events can be filtered by target entity."""
    await ledger.emit(event(target="goblin", delta={"hp": 50}))
    await ledger.emit(event(target="player", delta={"hp": 100}))
    await ledger.emit(event(target="goblin", delta={"hp": 30}))

    goblin_events = await ledger.get_by_target("goblin")
    assert len(goblin_events) == 2
    assert all(e.target == "goblin" for e in goblin_events)
    assert [e.delta["hp"] for e in goblin_events] == [50, 30]


async def test_get_by_location(ledger):
    """Events can be filtered by location."""
    await ledger.emit(event(target="a", event_type="X", location="cave"))
    await ledger.emit(event(target="b", event_type="X", location="tavern"))
    await ledger.emit(event(target="c", event_type="X", location="cave"))

    assert len(await ledger.get_by_location("cave")) == 2


async def test_get_by_type(ledger):
    await ledger.emit(event(target="a", event_type="UPDATE_ENTITY"))
    await ledger.emit(event(target="b", event_type="REMOVE_ENTITY"))
    await ledger.emit(event(target="c", event_type="UPDATE_ENTITY"))

    assert len(await ledger.get_by_type("UPDATE_ENTITY")) == 2
    assert len(await ledger.get_by_type("SCENE_TRANSITION")) == 0


async def test_get_since(ledger):
    await ledger.emit(event(target="early"))
    cutoff = await ledger.get_last_timestamp()
    await ledger.emit(event(target="late", delta={"n": 1}))

    later = await ledger.get_since(cutoff)
    assert [e.target for e in later] == ["late"]


# --- snapshot ---------------------------------------------------------------

async def test_snapshot(ledger):
    """Snapshot replays events into a flattened state dict."""
    await ledger.emit(event(target="goblin", delta={"hp": 50, "status": "alive"}))
    await ledger.emit(event(target="goblin", delta={"hp": 30}))
    await ledger.emit(event(target="player", delta={"hp": 100}))

    snap = await ledger.snapshot(location="cave")
    assert snap["goblin"]["hp"] == 30       # Latest value wins
    assert snap["goblin"]["status"] == "alive"  # Earlier value preserved
    assert snap["player"]["hp"] == 100


async def test_snapshot_without_location_covers_everything(ledger):
    await ledger.emit(event(target="goblin", delta={"hp": 50}, location="cave"))
    await ledger.emit(event(target="barkeep", delta={"mood": "wary"}, location="tavern"))

    snap = await ledger.snapshot()
    assert set(snap) == {"goblin", "barkeep"}


async def test_snapshot_is_scoped_by_location(ledger):
    await ledger.emit(event(target="goblin", delta={"hp": 50}, location="cave"))
    await ledger.emit(event(target="barkeep", delta={"mood": "wary"}, location="tavern"))

    assert set(await ledger.snapshot(location="cave")) == {"goblin"}


async def test_remove_entity_in_snapshot(ledger):
    """REMOVE_ENTITY events mark entities as removed in snapshot."""
    await ledger.emit(event(target="goblin", delta={"hp": 50}))
    await ledger.emit(event(target="goblin", event_type="REMOVE_ENTITY"))

    snap = await ledger.snapshot(location="cave")
    assert snap["goblin"].get("_removed") is True


async def test_snapshot_replays_in_insertion_order(ledger):
    """The last write must win even when timestamps collide."""
    for hp in (90, 60, 30):
        await ledger.emit(event(target="goblin", delta={"hp": hp}))

    snap = await ledger.snapshot(location="cave")
    assert snap["goblin"]["hp"] == 30


# --- rendering --------------------------------------------------------------

async def test_render_context(ledger):
    """render_context() produces a formatted string."""
    await ledger.emit(event(target="goblin", delta={"hp": 30},
                            agent="CombatResolver"))

    ctx = await ledger.render_context(5)
    assert "RECENT STATE CHANGES" in ctx
    assert "CombatResolver" in ctx
    assert "goblin" in ctx


async def test_render_context_when_empty(ledger):
    assert await ledger.render_context(5) == "No recent state changes recorded."


async def test_context_string_is_ascii():
    """
    emit() prints this string. On Windows a piped stdout uses cp1252, where a
    non-encodable character raises UnicodeEncodeError and every emit() fails.
    """
    line = event(target="goblin", delta={"hp": 30}).to_context_string()
    line.encode("cp1252")  # must not raise
    assert "->" in line


async def test_emit_survives_non_ascii_payloads(ledger, capsys):
    """Vault-sourced content carries em dashes and emoji; emit must not die."""
    await ledger.emit(event(target="Kaelen — the Archivist",
                            delta={"note": "sigil \U0001f9ec"}))
    assert await ledger.event_count() == 1


# --- pruning ----------------------------------------------------------------

async def test_max_events_pruning(tmp_path):
    """Ledger prunes old events beyond max_events."""
    ledger = EventLedger(db_path=str(tmp_path / "pruned.db"), max_events=5)
    await ledger.initialize_db()

    for i in range(10):
        await ledger.emit(event(target=f"e{i}"))

    assert await ledger.event_count() == 5
    recent = await ledger.get_recent(5)
    assert recent[0].target == "e5"   # First 5 were pruned
    assert recent[-1].target == "e9"


async def test_pruning_keeps_the_newest_not_an_arbitrary_set(tmp_path):
    """
    Pruning ordered by timestamp could drop the wrong rows when timestamps tie.
    """
    ledger = EventLedger(db_path=str(tmp_path / "pruned.db"), max_events=3)
    await ledger.initialize_db()

    for i in range(6):
        await ledger.emit(event(target=f"e{i}"))

    targets = [e.target for e in await ledger.get_recent(10)]
    assert targets == ["e3", "e4", "e5"]


# --- isolation --------------------------------------------------------------

async def test_ledger_uses_the_given_db_path(tmp_path):
    """The default path writes into the working directory; tests must not."""
    path = tmp_path / "explicit.db"
    ledger = EventLedger(db_path=str(path))
    await ledger.initialize_db()
    await ledger.emit(event())

    assert path.exists()
    assert not os.path.exists("dna_ledger.db")


async def test_state_persists_across_instances(tmp_path):
    path = str(tmp_path / "shared.db")
    first = EventLedger(db_path=path)
    await first.initialize_db()
    await first.emit(event(target="goblin", delta={"hp": 10}))

    second = EventLedger(db_path=path)
    assert await second.event_count() == 1


async def test_initialize_db_is_idempotent(tmp_path):
    ledger = EventLedger(db_path=str(tmp_path / "twice.db"))
    await ledger.initialize_db()
    await ledger.emit(event())
    await ledger.initialize_db()

    assert await ledger.event_count() == 1
