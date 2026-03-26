"""CI/CD API endpoints for webhook integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/cicd", tags=["cicd"])


class GateWebhookPayload(BaseModel):
    """Webhook payload from CI/CD system."""

    repository: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch name")
    commit_sha: str = Field(..., description="Commit SHA")
    gate_passed: bool = Field(..., description="Whether gate passed")
    scores: dict[str, float] = Field(default_factory=dict, description="Evaluation scores")
    deltas: dict[str, float] = Field(default_factory=dict, description="Score deltas")
    violations: list[str] = Field(default_factory=list, description="Violations detected")


class GateStatusResponse(BaseModel):
    """Response for gate status query."""

    repository: str
    branch: str
    latest_commit: str
    gate_passed: bool
    timestamp: float
    details: dict


@router.post("/webhook")
async def receive_gate_webhook(request: Request, payload: GateWebhookPayload) -> dict:
    """
    Receive webhook notification from CI/CD system about gate results.

    This endpoint allows GitHub Actions or other CI/CD systems to notify
    AutoAgent about gate results for tracking and analytics.

    Args:
        payload: Gate result payload

    Returns:
        Acknowledgment response
    """
    event_log = request.app.state.event_log

    # Log the gate event
    event_log.log_event(
        event_type="cicd_gate",
        data={
            "repository": payload.repository,
            "branch": payload.branch,
            "commit_sha": payload.commit_sha,
            "gate_passed": payload.gate_passed,
            "scores": payload.scores,
            "deltas": payload.deltas,
            "violations": payload.violations,
        },
    )

    return {
        "status": "received",
        "message": "Gate result recorded",
        "commit_sha": payload.commit_sha,
    }


@router.get("/status/{repository}/{branch}")
async def get_gate_status(request: Request, repository: str, branch: str) -> dict:
    """
    Get latest CI/CD gate status for a repository/branch.

    Args:
        repository: Repository name
        branch: Branch name

    Returns:
        Latest gate status
    """
    event_log = request.app.state.event_log

    # Get recent gate events for this repo/branch
    events = event_log.list_events(event_type="cicd_gate", limit=100)

    # Filter for matching repo and branch
    matching_events = [
        e for e in events
        if e.get("data", {}).get("repository") == repository
        and e.get("data", {}).get("branch") == branch
    ]

    if not matching_events:
        raise HTTPException(
            status_code=404,
            detail=f"No gate results found for {repository}/{branch}",
        )

    # Get most recent
    latest = matching_events[0]
    data = latest.get("data", {})

    return {
        "repository": repository,
        "branch": branch,
        "latest_commit": data.get("commit_sha"),
        "gate_passed": data.get("gate_passed"),
        "timestamp": latest.get("timestamp"),
        "scores": data.get("scores", {}),
        "deltas": data.get("deltas", {}),
        "violations": data.get("violations", []),
    }


@router.get("/history/{repository}")
async def get_gate_history(
    request: Request,
    repository: str,
    limit: int = 50,
) -> dict:
    """
    Get gate history for a repository.

    Args:
        repository: Repository name
        limit: Maximum number of results

    Returns:
        Gate history
    """
    event_log = request.app.state.event_log

    # Get recent gate events
    events = event_log.list_events(event_type="cicd_gate", limit=limit * 2)

    # Filter for matching repo
    matching_events = [
        e for e in events
        if e.get("data", {}).get("repository") == repository
    ][:limit]

    # Transform to history format
    history = []
    for event in matching_events:
        data = event.get("data", {})
        history.append({
            "timestamp": event.get("timestamp"),
            "branch": data.get("branch"),
            "commit_sha": data.get("commit_sha"),
            "gate_passed": data.get("gate_passed"),
            "scores": data.get("scores", {}),
            "deltas": data.get("deltas", {}),
        })

    return {
        "repository": repository,
        "history": history,
        "count": len(history),
    }
