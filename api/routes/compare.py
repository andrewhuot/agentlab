"""API routes for pairwise eval comparisons."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Request

from api.models import (
    CompareListItem,
    CompareListResponse,
    CompareRequest,
    CompareResponse,
    CompareRunAcceptedResponse,
)
from evals.pairwise import PairwiseComparisonStore, PairwiseEvalEngine

router = APIRouter(prefix="/api/evals/compare", tags=["evals"])


@router.post("", response_model=CompareRunAcceptedResponse, status_code=201)
async def create_comparison(body: CompareRequest, request: Request) -> CompareRunAcceptedResponse:
    """Run and persist a pairwise comparison."""
    eval_runner = getattr(request.app.state, "eval_runner", None)
    if eval_runner is None:
        raise HTTPException(status_code=503, detail="Eval runner is not configured")

    store = getattr(request.app.state, "pairwise_store", None)
    if store is None:
        store = PairwiseComparisonStore()
        request.app.state.pairwise_store = store

    config_a = _load_config(body.config_a_path)
    config_b = _load_config(body.config_b_path)
    label_a = body.label_a or _label_for_config(body.config_a_path, fallback="A")
    label_b = body.label_b or _label_for_config(body.config_b_path, fallback="B")
    dataset_name = Path(body.dataset_path).name if body.dataset_path else "default"

    engine = PairwiseEvalEngine(eval_runner=eval_runner, store=store)
    result = engine.compare(
        config_a=config_a,
        config_b=config_b,
        label_a=label_a,
        label_b=label_b,
        dataset_path=body.dataset_path,
        dataset_name=dataset_name,
        split=body.split,
        judge_strategy=body.judge_strategy,
    )
    return CompareRunAcceptedResponse(
        comparison_id=result.comparison_id,
        message="Pairwise comparison completed",
        summary=_list_item(result),
    )


@router.get("/{comparison_id}", response_model=CompareResponse)
async def get_comparison(comparison_id: str, request: Request) -> CompareResponse:
    """Fetch one stored pairwise comparison."""
    store = getattr(request.app.state, "pairwise_store", None)
    if store is None:
        raise HTTPException(status_code=404, detail="Pairwise comparison store is not configured")
    result = store.get(comparison_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Pairwise comparison not found: {comparison_id}")
    return CompareResponse(**result.to_dict())


@router.get("", response_model=CompareListResponse)
async def list_comparisons(request: Request, limit: int = 20) -> CompareListResponse:
    """List recent pairwise comparisons."""
    store = getattr(request.app.state, "pairwise_store", None)
    if store is None:
        return CompareListResponse(comparisons=[], count=0)
    results = store.list(limit=limit)
    items = [_list_item(result) for result in results]
    return CompareListResponse(comparisons=items, count=len(items))


def _load_config(path: str | None) -> dict | None:
    """Load a YAML config file when a path is supplied."""
    if not path:
        return None
    config_path = Path(path)
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"Config file not found: {path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _label_for_config(path: str | None, *, fallback: str) -> str:
    """Build a compact user-facing label from a config path."""
    if not path:
        return fallback
    return Path(path).stem


def _list_item(result) -> CompareListItem:
    """Convert a full comparison result into a compact list payload."""
    return CompareListItem(
        comparison_id=result.comparison_id,
        created_at=result.created_at,
        dataset_name=result.dataset_name,
        label_a=result.label_a,
        label_b=result.label_b,
        judge_strategy=result.judge_strategy,
        winner=result.analysis.winner,
        total_cases=result.summary.total_cases,
        left_wins=result.summary.left_wins,
        right_wins=result.summary.right_wins,
        ties=result.summary.ties,
        pending_human=result.summary.pending_human,
        p_value=result.analysis.p_value,
        is_significant=result.analysis.is_significant,
    )
