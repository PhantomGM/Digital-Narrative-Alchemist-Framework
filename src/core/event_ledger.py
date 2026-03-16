"""
Event Ledger — Core state synchronization module for the DNA Framework.

Implements the Event Sourcing pattern: agents emit granular State Deltas
instead of passing full state objects. All agents pull context from the
same ordered ledger, eliminating state fragmentation.

Solves: Bottleneck B3 (Distributed State Fragmentation)
Enhancement: E4 (Contextual Delta State / Event Sourcing)
"""

import time
import uuid
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
    An ordered, append-only log of StateEvents.

    All agents emit deltas here. Any agent can query the ledger to get
    an authoritative, chronologically ordered view of recent state changes.
    This ensures the NPC Engine, Narrative Weaver, and Session Director
    all operate from the exact same indisputable truth.
    """

    def __init__(self, max_events: int = 500):
        self._events: List[StateEvent] = []
        self._max_events = max_events

    def emit(self, event: StateEvent) -> None:
        """Append a new state delta to the ledger."""
        self._events.append(event)
        print(f"[EventLedger] Recorded: {event.to_context_string()}")

        # Prevent unbounded growth — old events are pruned
        # (the Chronicler should archive them before this happens)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def get_recent(self, n: int = 10) -> List[StateEvent]:
        """Return the last N events in chronological order."""
        return self._events[-n:]

    def get_by_target(self, target_id: str) -> List[StateEvent]:
        """Return all events affecting a specific entity or location."""
        return [e for e in self._events if e.target == target_id]

    def get_by_location(self, location: str) -> List[StateEvent]:
        """Return all events within a specific scene/location."""
        return [e for e in self._events if e.location == location]

    def get_by_type(self, event_type: str) -> List[StateEvent]:
        """Return all events of a specific type."""
        return [e for e in self._events if e.event_type == event_type]

    def get_since(self, timestamp: float) -> List[StateEvent]:
        """Return all events after a given timestamp (for Chronicler archival)."""
        return [e for e in self._events if e.timestamp > timestamp]

    def snapshot(self, location: str = None) -> Dict[str, Any]:
        """
        Produce a flattened current-state dict by replaying all events.

        If a location is specified, only events for that location are replayed.
        Events are applied in chronological order, so later events override earlier ones.

        Returns a dict keyed by target entity/location, with merged delta values.
        """
        events = self.get_by_location(location) if location else self._events
        state: Dict[str, Dict[str, Any]] = {}

        for event in events:
            if event.target not in state:
                state[event.target] = {}

            if event.event_type == "REMOVE_ENTITY":
                state[event.target]["_removed"] = True
            else:
                state[event.target].update(event.delta)

        return state

    def render_context(self, n: int = 10) -> str:
        """
        Render the last N events as a formatted context block suitable
        for injection into an LLM prompt.
        """
        recent = self.get_recent(n)
        if not recent:
            return "No recent state changes recorded."

        lines = ["=== RECENT STATE CHANGES ==="]
        for event in recent:
            lines.append(f"  • {event.to_context_string()}")
        lines.append("===========================")
        return "\n".join(lines)

    @property
    def event_count(self) -> int:
        """Total number of events in the ledger."""
        return len(self._events)

    @property
    def last_timestamp(self) -> float:
        """Timestamp of the most recent event, or 0.0 if empty."""
        return self._events[-1].timestamp if self._events else 0.0
