"""Generated eval suite review and acceptance API routes."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Body, HTTPException, Request

from api.models import (
    AcceptGeneratedEvalSuiteRequest,
    GenerateEvalSuiteRequest,
    GenerateEvalSuiteResponse,
    GeneratedEvalCasePatchRequest,
    GeneratedEvalListResponse,
    GeneratedEvalSuiteResponse,
    GeneratedEvalSuiteSummary,
)

router = APIRouter(prefix="/api/evals", tags=["generated-evals"])


def _get_generated_eval_store(request: Request):
    """Return the generated-suite store from app state.

    WHY: Generated evals are stored as shared artifacts used by API, UI, and
    CLI flows.
    """

    store = getattr(request.app.state, "generated_eval_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Generated eval store not configured")
    return store


def _get_auto_eval_generator(request: Request):
    """Return the auto-eval generator from app state.

    WHY: Route handlers should use the same configured generator instance as
    the rest of the application.
    """

    generator = getattr(request.app.state, "auto_eval_generator", None)
    if generator is None:
        raise HTTPException(status_code=503, detail="Auto eval generator not configured")
    return generator


def _suite_summary_payload(suite) -> dict[str, Any]:
    """Project a generated suite into a compact summary payload.

    WHY: The `/evals` list view only needs lightweight metadata.
    """

    return {
        "suite_id": suite.suite_id,
        "agent_name": suite.agent_name,
        "source_kind": suite.source_kind,
        "status": suite.status,
        "mock_mode": suite.mock_mode,
        "created_at": suite.created_at,
        "updated_at": suite.updated_at,
        "accepted_at": suite.accepted_at,
        "accepted_eval_path": suite.accepted_eval_path,
        "transcript_count": suite.transcript_count,
        "category_counts": suite.category_counts,
        "case_count": len(suite.cases),
    }


def _load_generation_inputs(
    request: Request,
    body: GenerateEvalSuiteRequest,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    """Resolve agent config and transcript inputs for generation.

    WHY: The generation endpoint accepts explicit payloads but also supports
    pulling current config and recent conversations by default.
    """

    if body.agent_config is not None:
        agent_config = body.agent_config
    elif body.config_path:
        path = Path(body.config_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Config file not found: {body.config_path}")
        with path.open("r", encoding="utf-8") as handle:
            agent_config = yaml.safe_load(handle) or {}
    else:
        version_manager = getattr(request.app.state, "version_manager", None)
        agent_config = version_manager.get_active_config() if version_manager is not None else {}
        if agent_config is None:
            agent_config = {}

    transcripts = body.transcripts
    if transcripts is None and body.from_transcripts:
        conversation_store = getattr(request.app.state, "conversation_store", None)
        if conversation_store is None:
            raise HTTPException(status_code=503, detail="Conversation store not configured")
        transcripts = [
            {
                "id": record.conversation_id,
                "messages": [
                    {"role": "user", "content": record.user_message},
                    {"role": "agent", "content": record.agent_response},
                ],
                "success": record.outcome == "success",
                "metadata": {
                    "outcome": record.outcome,
                    "specialist_used": record.specialist_used,
                    "tool_calls": record.tool_calls,
                },
            }
            for record in conversation_store.get_recent(limit=body.conversation_limit)
        ]

    return agent_config, transcripts


@router.post("/generate", response_model=GenerateEvalSuiteResponse, status_code=202)
async def generate_eval_suite(
    request: Request,
    body: GenerateEvalSuiteRequest,
) -> GenerateEvalSuiteResponse:
    """Start background generation of a structured generated eval suite."""

    task_manager = request.app.state.task_manager
    ws_manager = request.app.state.ws_manager
    generator = _get_auto_eval_generator(request)
    store = _get_generated_eval_store(request)

    agent_config, transcripts = _load_generation_inputs(request, body)

    def run_generation(task) -> dict[str, Any]:
        task.progress = 15
        suite = generator.generate(
            agent_name=body.agent_name,
            agent_config=agent_config,
            transcripts=transcripts,
        )
        task.progress = 85
        store.save_suite(suite)
        result = {
            "suite_id": suite.suite_id,
            "agent_name": suite.agent_name,
            "category_counts": suite.category_counts,
            "case_count": len(suite.cases),
            "mock_mode": suite.mock_mode,
        }
        task.result = result

        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                ws_manager.broadcast(
                    {
                        "type": "generated_eval_complete",
                        "task_id": task.task_id,
                        "suite_id": suite.suite_id,
                        "case_count": len(suite.cases),
                    }
                )
            )
            loop.close()
        except Exception:
            pass

        return result

    task = task_manager.create_task("generated_eval", run_generation)
    return GenerateEvalSuiteResponse(task_id=task.task_id, message="Generated eval synthesis started")


@router.get("/generated", response_model=GeneratedEvalListResponse)
async def list_generated_eval_suites(
    request: Request,
    limit: int = 20,
) -> GeneratedEvalListResponse:
    """List recently generated eval suites."""

    store = _get_generated_eval_store(request)
    suites = store.list_suites(limit=limit)
    return GeneratedEvalListResponse(
        suites=[GeneratedEvalSuiteSummary(**_suite_summary_payload(suite)) for suite in suites],
        count=len(suites),
    )


@router.get("/generated/{suite_id}")
async def get_generated_eval_suite(
    suite_id: str,
    request: Request,
) -> dict[str, GeneratedEvalSuiteResponse]:
    """Fetch one generated eval suite by ID."""

    store = _get_generated_eval_store(request)
    suite = store.get_suite(suite_id)
    if suite is None:
        raise HTTPException(status_code=404, detail=f"Generated eval suite not found: {suite_id}")
    return {"suite": GeneratedEvalSuiteResponse(**suite.to_dict())}


@router.post("/generated/{suite_id}/accept")
async def accept_generated_eval_suite(
    suite_id: str,
    request: Request,
    body: AcceptGeneratedEvalSuiteRequest = Body(default_factory=AcceptGeneratedEvalSuiteRequest),
) -> dict[str, Any]:
    """Accept a generated suite into the active eval corpus."""

    store = _get_generated_eval_store(request)
    try:
        suite = store.accept_suite(
            suite_id,
            eval_cases_dir=body.eval_cases_dir or "evals/cases",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "suite_id": suite.suite_id,
        "status": suite.status,
        "eval_file": suite.accepted_eval_path,
        "case_count": len(suite.cases),
    }


@router.patch("/generated/{suite_id}/cases/{case_id}")
async def patch_generated_eval_case(
    suite_id: str,
    case_id: str,
    request: Request,
    body: GeneratedEvalCasePatchRequest,
) -> dict[str, GeneratedEvalSuiteResponse]:
    """Apply an inline edit to one generated eval case."""

    store = _get_generated_eval_store(request)
    try:
        suite = store.update_case(
            suite_id,
            case_id,
            body.model_dump(exclude_none=True),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"suite": GeneratedEvalSuiteResponse(**suite.to_dict())}


@router.delete("/generated/{suite_id}/cases/{case_id}")
async def delete_generated_eval_case(
    suite_id: str,
    case_id: str,
    request: Request,
) -> dict[str, GeneratedEvalSuiteResponse]:
    """Remove one generated eval case from a suite."""

    store = _get_generated_eval_store(request)
    try:
        suite = store.delete_case(suite_id, case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"suite": GeneratedEvalSuiteResponse(**suite.to_dict())}
