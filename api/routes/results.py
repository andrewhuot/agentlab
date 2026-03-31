"""API routes for structured eval results exploration."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from api.models import (
    ResultAnnotationRequest,
    ResultDiffResponse,
    ResultExamplesResponse,
    ResultExampleResponse,
    ResultRunListItem,
    ResultRunListResponse,
    ResultRunResponse,
    ResultSummary,
)
from evals.results_model import Annotation

router = APIRouter(prefix="/api/evals/results", tags=["evals"])


@router.get("", response_model=ResultRunListResponse)
async def list_result_runs(request: Request, limit: int = 20) -> ResultRunListResponse:
    """List recent structured eval runs."""
    store = _results_store(request)
    rows = [
        ResultRunListItem(**payload)
        for payload in store.list_runs(limit=limit)
    ]
    return ResultRunListResponse(runs=rows, count=len(rows))


@router.get("/{run_id}", response_model=ResultRunResponse)
async def get_result_run(run_id: str, request: Request) -> ResultRunResponse:
    """Fetch one full structured eval run."""
    store = _results_store(request)
    result_set = store.get_run(run_id)
    if result_set is None:
        raise HTTPException(status_code=404, detail=f"Eval results not found: {run_id}")
    return ResultRunResponse(**result_set.to_dict())


@router.get("/{run_id}/summary", response_model=ResultSummary)
async def get_result_summary(run_id: str, request: Request) -> ResultSummary:
    """Return aggregate summary stats for one run."""
    store = _results_store(request)
    summary = store.get_summary(run_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Eval results not found: {run_id}")
    return ResultSummary(**summary.to_dict())


@router.get("/{run_id}/examples", response_model=ResultExamplesResponse)
async def get_result_examples(
    run_id: str,
    request: Request,
    page: int = 1,
    page_size: int = 50,
    passed: bool | None = None,
    metric: str | None = None,
    below: float | None = None,
    above: float | None = None,
) -> ResultExamplesResponse:
    """Return a paginated slice of structured example results."""
    store = _results_store(request)
    examples, total = store.get_examples(
        run_id,
        page=page,
        page_size=page_size,
        passed=passed,
        metric=metric,
        below=below,
        above=above,
    )
    if total == 0 and store.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Eval results not found: {run_id}")
    return ResultExamplesResponse(
        run_id=run_id,
        page=page,
        page_size=page_size,
        total=total,
        examples=[ResultExampleResponse(**example.to_dict()) for example in examples],
    )


@router.get("/{run_id}/examples/{example_id}", response_model=ResultExampleResponse)
async def get_result_example(run_id: str, example_id: str, request: Request) -> ResultExampleResponse:
    """Return one structured example result."""
    store = _results_store(request)
    example = store.get_example(run_id, example_id)
    if example is None:
        raise HTTPException(status_code=404, detail=f"Eval example not found: {run_id}/{example_id}")
    return ResultExampleResponse(**example.to_dict())


@router.post(
    "/{run_id}/examples/{example_id}/annotate",
    response_model=ResultExampleResponse,
    status_code=201,
)
async def annotate_result_example(
    run_id: str,
    example_id: str,
    body: ResultAnnotationRequest,
    request: Request,
) -> ResultExampleResponse:
    """Append a human annotation to one result example."""
    store = _results_store(request)
    existing = store.get_example(run_id, example_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Eval example not found: {run_id}/{example_id}")

    annotation = Annotation(
        author=body.author,
        timestamp=datetime.now(timezone.utc).isoformat(),
        type=body.type,
        content=body.content,
        score_override=body.score_override,
    )
    store.add_annotation(run_id, example_id, annotation)
    updated = store.get_example(run_id, example_id)
    if updated is None:  # pragma: no cover - defensive after successful write
        raise HTTPException(status_code=500, detail="Annotation stored but example could not be reloaded")
    return ResultExampleResponse(**updated.to_dict())


@router.get("/{run_id}/export", response_class=PlainTextResponse)
async def export_result_run(run_id: str, request: Request, format: str = "json") -> PlainTextResponse:
    """Export one structured eval run in a requested format."""
    store = _results_store(request)
    try:
        payload = store.export_run(run_id, format=format)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    media_type = "application/json" if format.lower() == "json" else "text/plain"
    return PlainTextResponse(payload, media_type=media_type)


@router.get("/{run_id}/diff", response_model=ResultDiffResponse)
async def diff_result_run(run_id: str, request: Request, candidate_run_id: str) -> ResultDiffResponse:
    """Compare two stored eval runs and return changed examples."""
    store = _results_store(request)
    try:
        diff = store.diff_runs(run_id, candidate_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResultDiffResponse(**diff)


def _results_store(request: Request):
    """Resolve the shared structured results store from application state."""
    store = getattr(request.app.state, "results_store", None)
    if store is None:
        eval_runner = getattr(request.app.state, "eval_runner", None)
        store = getattr(eval_runner, "results_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Eval results store is not configured")
    return store
