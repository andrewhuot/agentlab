"""NL config edit endpoint — translate natural language into config changes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from optimizer.nl_editor import NLEditor

router = APIRouter(prefix="/api", tags=["edit"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class EditRequest(BaseModel):
    description: str
    dry_run: bool = False


class EditResponse(BaseModel):
    intent: dict[str, Any]
    diff: str
    score_before: float
    score_after: float
    applied: bool


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/edit", response_model=EditResponse)
async def nl_edit(body: EditRequest, request: Request) -> EditResponse:
    """Apply a natural language config edit and optionally deploy."""
    # Resolve current config from app state
    current_config: dict | None = None

    deployer = getattr(request.app.state, "deployer", None)
    if deployer is not None:
        try:
            current_config = deployer.get_active_config()
        except Exception:
            current_config = None

    if current_config is None:
        version_manager = getattr(request.app.state, "version_manager", None)
        if version_manager is not None:
            try:
                current_config = version_manager.get_active_config()
            except Exception:
                current_config = None

    if current_config is None:
        current_config = {}

    eval_runner = getattr(request.app.state, "eval_runner", None)

    nl_editor = NLEditor(eval_runner=eval_runner)

    # Parse intent (needed for response even in dry_run)
    intent = nl_editor.parse_intent(body.description, current_config)

    # Full pipeline: parse → generate → eval
    result = nl_editor.apply_and_eval(
        description=body.description,
        current_config=current_config,
        eval_runner=eval_runner,
    )

    # Deploy unless dry_run
    if not body.dry_run and result.accepted and deployer is not None:
        try:
            scores_dict = {
                "composite": result.score_after,
            }
            deployer.deploy(result.new_config, scores_dict)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Deploy failed: {exc}") from exc

    return EditResponse(
        intent={
            "description": intent.description,
            "target_surfaces": intent.target_surfaces,
            "change_type": intent.change_type,
            "constraints": intent.constraints,
        },
        diff=result.diff_summary,
        score_before=result.score_before,
        score_after=result.score_after,
        applied=result.accepted and not body.dry_run,
    )
