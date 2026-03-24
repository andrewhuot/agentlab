"""AutoFix Copilot API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/autofix", tags=["autofix"])


@router.post("/suggest")
async def suggest(request: Request) -> dict[str, Any]:
    """Generate AutoFix proposals without applying them."""
    engine = request.app.state.autofix_engine
    deployer = request.app.state.deployer
    current_config = deployer.get_active_config() or {}

    body = await request.json() if request.headers.get("content-length", "0") != "0" else {}
    failures = body.get("failures", [])

    proposals = engine.suggest(failures, current_config)
    return {
        "proposals": [p.to_dict() for p in proposals],
        "count": len(proposals),
    }


@router.get("/proposals")
async def list_proposals(
    request: Request,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List AutoFix proposals, optionally filtered by status."""
    engine = request.app.state.autofix_engine
    proposals = engine.history(limit=limit)
    if status:
        proposals = [p for p in proposals if p.status == status]
    return {
        "proposals": [p.to_dict() for p in proposals],
        "count": len(proposals),
    }


@router.post("/apply/{proposal_id}")
async def apply_proposal(proposal_id: str, request: Request) -> dict[str, Any]:
    """Apply a specific AutoFix proposal."""
    engine = request.app.state.autofix_engine
    deployer = request.app.state.deployer
    current_config = deployer.get_active_config() or {}

    try:
        new_config, status_message = engine.apply(proposal_id, current_config)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    event_log = request.app.state.event_log
    event_log.append(
        event_type="autofix_applied",
        payload={"proposal_id": proposal_id, "status": status_message},
    )

    return {
        "proposal_id": proposal_id,
        "status": status_message,
        "config_applied": new_config is not None,
    }


@router.get("/history")
async def history(request: Request, limit: int = 50) -> dict[str, Any]:
    """Get past AutoFix proposals with outcomes."""
    engine = request.app.state.autofix_engine
    proposals = engine.history(limit=limit)
    return {
        "proposals": [p.to_dict() for p in proposals],
        "count": len(proposals),
    }
