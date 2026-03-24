"""Human control API endpoints (pause/resume/reject/inject/pin/unpin)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from optimizer.human_control import HumanControlState

router = APIRouter(prefix="/api/control", tags=["control"])


def _state_to_dict(state: HumanControlState) -> dict[str, Any]:
    """Serialize control state for API responses."""
    return {
        "paused": state.paused,
        "immutable_surfaces": state.immutable_surfaces,
        "rejected_experiments": state.rejected_experiments,
        "last_injected_mutation": state.last_injected_mutation,
        "updated_at": state.updated_at,
    }


@router.get("/state")
async def get_control_state(request: Request) -> dict[str, Any]:
    """Get the current human-control state."""
    store = request.app.state.control_store
    return _state_to_dict(store.get_state())


@router.post("/pause")
async def pause(request: Request) -> dict[str, Any]:
    """Pause optimization activity."""
    store = request.app.state.control_store
    state = store.pause()
    request.app.state.event_log.append(event_type="human_pause", payload={"paused": True})
    return _state_to_dict(state)


@router.post("/resume")
async def resume(request: Request) -> dict[str, Any]:
    """Resume optimization activity."""
    store = request.app.state.control_store
    return _state_to_dict(store.resume())


@router.post("/pin/{surface}")
async def pin_surface(surface: str, request: Request) -> dict[str, Any]:
    """Mark a surface immutable."""
    store = request.app.state.control_store
    return _state_to_dict(store.pin_surface(surface))


@router.post("/unpin/{surface}")
async def unpin_surface(surface: str, request: Request) -> dict[str, Any]:
    """Remove an immutable surface marker."""
    store = request.app.state.control_store
    return _state_to_dict(store.unpin_surface(surface))


@router.post("/reject/{experiment_id}")
async def reject_experiment(experiment_id: str, request: Request) -> dict[str, Any]:
    """Reject experiment and rollback active canary when present."""
    store = request.app.state.control_store
    state = store.reject_experiment(experiment_id)

    deployer = request.app.state.deployer
    canary = deployer.version_manager.manifest.get("canary_version")
    rollback = None
    if canary is not None:
        deployer.version_manager.rollback(canary)
        rollback = f"Rolled back canary v{canary:03d}"
        request.app.state.event_log.append(
            event_type="rollback_triggered",
            payload={"canary_version": canary, "reason": "human_reject"},
            experiment_id=experiment_id,
        )

    payload = _state_to_dict(state)
    payload["rollback"] = rollback
    request.app.state.event_log.append(
        event_type="human_reject",
        payload={"experiment_id": experiment_id, "rollback": rollback},
        experiment_id=experiment_id,
    )
    return payload


@router.post("/inject")
async def inject(
    request: Request,
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    """Inject a manual mutation payload and deploy as canary."""
    if not body:
        raise HTTPException(status_code=400, detail="Mutation payload required")

    store = request.app.state.control_store
    deployer = request.app.state.deployer
    eval_runner = request.app.state.eval_runner
    current = deployer.get_active_config() or {}

    def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = {**base}
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    candidate = body.get("config")
    if not isinstance(candidate, dict):
        candidate = deep_merge(current, body)

    score = eval_runner.run(config=candidate)
    deploy_message = deployer.deploy(
        candidate,
        {
            "quality": score.quality,
            "safety": score.safety,
            "latency": score.latency,
            "cost": score.cost,
            "composite": score.composite,
        },
    )
    state = store.mark_injected("api_payload")
    request.app.state.event_log.append(
        event_type="human_inject",
        payload={"deploy_message": deploy_message, "composite": score.composite},
    )
    payload = _state_to_dict(state)
    payload["deploy_message"] = deploy_message
    payload["composite"] = score.composite
    return payload
