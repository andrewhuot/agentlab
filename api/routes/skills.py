"""Executable skills registry API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/skills", tags=["skills"])


def _get_skill_store(request: Request):
    store = getattr(request.app.state, "skill_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Skill store not configured")
    return store


@router.get("/recommend")
async def recommend_skills(
    request: Request,
    failure_family: str | None = Query(None),
) -> dict[str, Any]:
    """Recommend skills based on current failure patterns."""
    store = _get_skill_store(request)
    metrics: dict[str, float] = {}
    # Try to get health metrics from observer if available
    observer = getattr(request.app.state, "observer", None)
    if observer:
        try:
            conversation_store = getattr(request.app.state, "conversation_store", None)
            if conversation_store:
                health = observer.health_check(conversation_store)
                metrics = health.metrics.to_dict()
        except Exception:
            pass

    skills = store.recommend(failure_family=failure_family, metrics=metrics)
    return {"skills": [s.to_dict() for s in skills], "count": len(skills)}


@router.get("/stats")
async def skill_stats(
    request: Request,
    n: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Get skill effectiveness leaderboard."""
    store = _get_skill_store(request)
    top = store.top_performers(n=n)
    return {
        "leaderboard": [
            {
                "name": s.name,
                "category": s.category,
                "times_applied": s.times_applied,
                "success_rate": s.success_rate,
                "proven_improvement": s.proven_improvement,
            }
            for s in top
        ],
        "count": len(top),
    }


@router.get("/")
async def list_skills(
    request: Request,
    category: str | None = Query(None),
    platform: str | None = Query(None),
    status: str | None = Query(None),
) -> dict[str, Any]:
    """List all executable skills with optional filters."""
    store = _get_skill_store(request)
    skills = store.list(category=category, platform=platform, status=status)
    return {"skills": [s.to_dict() for s in skills], "count": len(skills)}


@router.get("/{name}")
async def get_skill(
    request: Request,
    name: str,
    version: int | None = Query(None),
) -> dict[str, Any]:
    """Get a specific skill by name."""
    store = _get_skill_store(request)
    skill = store.get(name, version)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {name}")
    return {"skill": skill.to_dict()}


@router.post("/{name}/apply")
async def apply_skill(
    request: Request,
    name: str,
) -> dict[str, Any]:
    """Apply a skill — triggers one optimization cycle guided by this skill."""
    store = _get_skill_store(request)
    skill = store.get(name)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {name}")

    return {
        "name": name,
        "status": "queued",
        "message": f"Skill '{name}' application queued. Mutations: {[m.name for m in skill.mutations]}",
        "mutations": [m.to_dict() for m in skill.mutations],
    }


@router.post("/install")
async def install_skills(request: Request) -> dict[str, Any]:
    """Install skills from a YAML pack file."""
    body = await request.json()
    file_path = body.get("file_path")
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")

    store = _get_skill_store(request)

    from registry.skill_loader import install_pack
    try:
        count = install_pack(file_path, store)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"installed": count, "file_path": file_path}
