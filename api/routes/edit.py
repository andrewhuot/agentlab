"""Natural-language edit API endpoint."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from optimizer.memory import OptimizationAttempt
from optimizer.nl_editor import NLEditor

router = APIRouter(prefix="/api/edit", tags=["edit"])


def _ensure_active_config(deployer: Any) -> dict[str, Any]:
    """Return current active config or bootstrap from base if needed."""
    from pathlib import Path

    from agent.config.loader import load_config

    current = deployer.get_active_config()
    if current is not None:
        return current

    base_path = Path(__file__).parent.parent.parent / "agent" / "config" / "base_config.yaml"
    config = load_config(str(base_path)).model_dump()
    deployer.version_manager.save_version(config, scores={"composite": 0.0}, status="active")
    return config


def _score_dict(score_obj: Any) -> dict[str, float]:
    return {
        "quality": float(getattr(score_obj, "quality", 0.0)),
        "safety": float(getattr(score_obj, "safety", 0.0)),
        "latency": float(getattr(score_obj, "latency", 0.0)),
        "cost": float(getattr(score_obj, "cost", 0.0)),
        "composite": float(getattr(score_obj, "composite", 0.0)),
    }


@router.post("")
async def apply_edit(request: Request) -> dict[str, Any]:
    """Apply a natural-language config edit and return proposal + score deltas."""
    body = await request.json()
    description = str(body.get("description", "")).strip()
    dry_run = bool(body.get("dry_run", False))
    if not description:
        raise HTTPException(status_code=400, detail="Field 'description' is required")

    eval_runner = request.app.state.eval_runner
    deployer = request.app.state.deployer
    observer = request.app.state.observer
    memory = request.app.state.optimization_memory

    editor = NLEditor(use_mock=True)
    current_config = _ensure_active_config(deployer)
    intent = editor.parse_intent(description, current_config)
    result = editor.apply_and_eval(
        description=description,
        current_config=current_config,
        eval_runner=eval_runner,
        deployer=deployer,
        auto_apply=(not dry_run),
    )

    applied = bool(result.accepted and not dry_run)
    attempt: dict[str, Any] | None = None
    if applied:
        report = observer.observe()
        logged = OptimizationAttempt(
            attempt_id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            change_description=description,
            config_diff=result.diff_summary,
            status="accepted",
            config_section="nl_edit",
            score_before=result.score_before,
            score_after=result.score_after,
            significance_p_value=1.0,
            significance_delta=result.score_after - result.score_before,
            significance_n=0,
            health_context=json.dumps(report.metrics.to_dict()),
        )
        memory.log(logged)
        attempt = {
            "attempt_id": logged.attempt_id,
            "status": logged.status,
            "score_before": logged.score_before,
            "score_after": logged.score_after,
        }

        project_memory = getattr(request.app.state, "project_memory", None)
        if project_memory is not None:
            try:
                project_memory.update_with_intelligence(
                    report=report,
                    eval_score=result.score_after,
                    recent_changes=[logged],
                    skill_gaps=[],
                )
            except Exception:
                pass

    return {
        "intent": {
            "description": intent.description,
            "target_surfaces": intent.target_surfaces,
            "change_type": intent.change_type,
            "constraints": intent.constraints,
        },
        "diff": result.diff_summary,
        "score_before": result.score_before,
        "score_after": result.score_after,
        "applied": applied,
        "accepted": result.accepted,
        "dry_run": dry_run,
        "scores": _score_dict(eval_runner.run(config=result.new_config)),
        "attempt": attempt,
    }
