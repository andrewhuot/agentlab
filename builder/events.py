"""Streaming event helpers for Builder Workspace."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Deque, Iterator

from builder.types import now_ts, new_id


class BuilderEventType(str, Enum):
    """Allowed builder streaming events."""

    MESSAGE_DELTA = "message.delta"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    PLAN_READY = "plan.ready"
    ARTIFACT_UPDATED = "artifact.updated"
    EVAL_STARTED = "eval.started"
    EVAL_COMPLETED = "eval.completed"
    APPROVAL_REQUESTED = "approval.requested"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"


@dataclass
class BuilderEvent:
    """One event emitted by builder backend services."""

    event_id: str = field(default_factory=new_id)
    event_type: BuilderEventType = BuilderEventType.TASK_PROGRESS
    session_id: str = ""
    task_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=now_ts)


class EventBroker:
    """In-memory event broker used by SSE and websocket publishers."""

    def __init__(self, max_events: int = 2000) -> None:
        self._events: Deque[BuilderEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def publish(
        self,
        event_type: BuilderEventType,
        session_id: str,
        task_id: str | None,
        payload: dict[str, Any],
    ) -> BuilderEvent:
        """Store and return a new event."""

        event = BuilderEvent(
            event_type=event_type,
            session_id=session_id,
            task_id=task_id,
            payload=payload,
        )
        with self._lock:
            self._events.append(event)
        return event

    def list_events(
        self,
        session_id: str | None = None,
        task_id: str | None = None,
        limit: int = 200,
    ) -> list[BuilderEvent]:
        """Return recent events filtered by session/task."""

        with self._lock:
            events = list(self._events)
        filtered: list[BuilderEvent] = []
        for event in reversed(events):
            if session_id and event.session_id != session_id:
                continue
            if task_id and event.task_id != task_id:
                continue
            filtered.append(event)
            if len(filtered) >= limit:
                break
        return list(reversed(filtered))

    def iter_events(
        self,
        session_id: str | None = None,
        task_id: str | None = None,
        since_timestamp: float | None = None,
    ) -> Iterator[BuilderEvent]:
        """Yield events matching the filter from the in-memory buffer."""

        events = self.list_events(session_id=session_id, task_id=task_id, limit=10_000)
        for event in events:
            if since_timestamp is not None and event.timestamp <= since_timestamp:
                continue
            yield event


def serialize_sse_event(event: BuilderEvent) -> str:
    """Serialize a builder event into SSE wire format."""

    payload = {
        "id": event.event_id,
        "type": event.event_type.value,
        "session_id": event.session_id,
        "task_id": event.task_id,
        "timestamp": event.timestamp,
        "payload": event.payload,
    }
    return f"id: {event.event_id}\nevent: {event.event_type.value}\ndata: {json.dumps(payload)}\n\n"


def event_to_dict(event: BuilderEvent) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one event."""

    data = asdict(event)
    data["event_type"] = event.event_type.value
    return data
