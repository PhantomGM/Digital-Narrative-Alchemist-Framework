"""
Event Ledger — Core state synchronization module for the DNA Framework.

Implements the Event Sourcing pattern: agents emit granular State Deltas
instead of passing full state objects. All agents pull context from the
same ordered ledger, eliminating state fragmentation.

Upgraded to use aiosqlite for true asynchronous, non-blocking disk I/O,
enabling multiple agents to emit and read parallel events without lock contention.
"""

import time
import uuid
import json
import asyncio
import aiosqlite
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class StateEvent:
    """A single atomic state change emitted by an agent."""

    event_type: str          # e.g. "UPDATE_ENTITY", "ADD_ENTITY", "REMOVE_ENTITY",
                             #      "UPDATE_HAZARD", "SCENE_TRANSITION", "PACING_SHIFT"
    target: str              # The entity or location being affected
    delta: Dict[str, Any]    # The actual change payload
    source_agent: str        # Which agent emitted this event
    location: str = ""       # The location/scene context this event applies to
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_context_string(self) -> str:
        """Render this event as a human-readable context line for LLM injection."""
        delta_summary = ", ".join(f"{k}: {v}" for k, v in self.delta.items())
        return f"[{self.source_agent}] {self.event_type} → {self.target}: {delta_summary}"

class EventLedger:
    """
    An ordered, append-only log of StateEvents backed by aiosqlite.

    All agents sequentially await emit calls. Any agent can await queries
    to the ledger to get an authoritative, chronologically ordered view of
    recent state changes across the parallel multi-agent environment without blocking.
    """

    def __init__(self, db_path: str = "dna_ledger.db", max_events: int = 500):
        self.db_path = db_path
        self._max_events = max_events

    async def initialize_db(self) -> None:
        """Initialize the SQLite Async Database to store events."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    delta TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    location TEXT,
                    timestamp REAL NOT NULL
                )
            """)
            await db.commit()
            print(f"[EventLedger] Asynchronous SQLite database initialized at {self.db_path}.")

    async def emit(self, event: StateEvent) -> None:
        """Append a new state delta directly to the database via async task."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO events (event_id, event_type, target, delta, source_agent, location, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event.event_id, event.event_type, event.target, json.dumps(event.delta), event.source_agent, event.location, event.timestamp)
            )
            await db.commit()
            print(f"[EventLedger] Recorded: {event.to_context_string()}")
            
            # Prune old events beyond max_events to bound the db cost
            await db.execute(f"DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY timestamp DESC LIMIT {self._max_events})")
            await db.commit()

    async def get_recent(self, n: int = 10) -> List[StateEvent]:
        """Return the last N events in chronological order directly from the database."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(f"SELECT * FROM events ORDER BY timestamp DESC LIMIT {n}") as cursor:
                rows = await cursor.fetchall()
                events = []
                for row in reversed(rows): # Reverse back to chronological order
                    events.append(StateEvent(
                        event_id=row[1],
                        event_type=row[2],
                        target=row[3],
                        delta=json.loads(row[4]),
                        source_agent=row[5],
                        location=row[6],
                        timestamp=row[7]
                    ))
                return events

    async def get_by_target(self, target_id: str) -> List[StateEvent]:
        """Return all events affecting a specific entity or location."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM events WHERE target = ? ORDER BY timestamp ASC", (target_id,)) as cursor:
                rows = await cursor.fetchall()
                return [StateEvent(
                        event_id=row[1],
                        event_type=row[2],
                        target=row[3],
                        delta=json.loads(row[4]),
                        source_agent=row[5],
                        location=row[6],
                        timestamp=row[7]
                    ) for row in rows]

    async def get_by_location(self, location: str) -> List[StateEvent]:
        """Return all events within a specific scene/location."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM events WHERE location = ? ORDER BY timestamp ASC", (location,)) as cursor:
                rows = await cursor.fetchall()
                return [StateEvent(
                        event_id=row[1],
                        event_type=row[2],
                        target=row[3],
                        delta=json.loads(row[4]),
                        source_agent=row[5],
                        location=row[6],
                        timestamp=row[7]
                    ) for row in rows]

    async def get_by_type(self, event_type: str) -> List[StateEvent]:
        """Return all events of a specific type."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM events WHERE event_type = ? ORDER BY timestamp ASC", (event_type,)) as cursor:
                rows = await cursor.fetchall()
                return [StateEvent(
                        event_id=row[1],
                        event_type=row[2],
                        target=row[3],
                        delta=json.loads(row[4]),
                        source_agent=row[5],
                        location=row[6],
                        timestamp=row[7]
                    ) for row in rows]

    async def get_since(self, timestamp: float) -> List[StateEvent]:
        """Return all events after a given timestamp (for Chronicler archival)."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM events WHERE timestamp > ? ORDER BY timestamp ASC", (timestamp,)) as cursor:
                rows = await cursor.fetchall()
                return [StateEvent(
                        event_id=row[1],
                        event_type=row[2],
                        target=row[3],
                        delta=json.loads(row[4]),
                        source_agent=row[5],
                        location=row[6],
                        timestamp=row[7]
                    ) for row in rows]

    async def snapshot(self, location: str = None) -> Dict[str, Any]:
        """
        Produce a flattened current-state dict by replaying all DB events.

        Returns a dict keyed by target entity/location, with merged delta values.
        """
        if location:
            events = await self.get_by_location(location)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT * FROM events ORDER BY timestamp ASC") as cursor:
                    rows = await cursor.fetchall()
                    events = [StateEvent(
                        event_id=row[1],
                        event_type=row[2],
                        target=row[3],
                        delta=json.loads(row[4]),
                        source_agent=row[5],
                        location=row[6],
                        timestamp=row[7]
                    ) for row in rows]

        state: Dict[str, Dict[str, Any]] = {}
        for event in events:
            if event.target not in state:
                state[event.target] = {}

            if event.event_type == "REMOVE_ENTITY":
                state[event.target]["_removed"] = True
            else:
                state[event.target].update(event.delta)

        return state

    async def render_context(self, n: int = 10) -> str:
        """
        Render the last N events from the DB as a formatted context block suitable
        for injection into an LLM prompt.
        """
        recent = await self.get_recent(n)
        if not recent:
            return "No recent state changes recorded."

        lines = ["=== RECENT STATE CHANGES ==="]
        for event in recent:
            lines.append(f"  • {event.to_context_string()}")
        lines.append("===========================")
        return "\n".join(lines)

    async def get_last_timestamp(self) -> float:
        """Timestamp of the most recent event in the DB, or 0.0 if empty."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT timestamp FROM events ORDER BY timestamp DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0.0
