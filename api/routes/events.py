"""System event log API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
async def list_events(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    event_type: str | None = Query(None),
) -> dict:
    """List append-only system events."""
    event_log = request.app.state.event_log
    events = event_log.list_events(limit=limit, event_type=event_type)
    return {"events": events}
