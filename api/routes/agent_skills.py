"""Agent skill generation API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/agent-skills", tags=["agent-skills"])


def _get_skill_store(request: Request):
    store = getattr(request.app.state, "agent_skill_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Agent skill store not configured")
    return store


@router.get("/gaps")
async def list_gaps(request: Request) -> dict[str, Any]:
    """List identified skill gaps."""
    store = _get_skill_store(request)
    gaps = store.list_gaps()
    return {"gaps": gaps, "count": len(gaps)}


@router.post("/analyze")
async def analyze_gaps(request: Request) -> dict[str, Any]:
    """Trigger gap analysis on current blame data."""
    from agent_skills.gap_analyzer import GapAnalyzer

    store = _get_skill_store(request)
    analyzer = GapAnalyzer()

    # Try to get blame clusters from observer
    blame_clusters: list = []
    opportunities: list = []

    # Get opportunities from opportunity queue if available
    opp_queue = getattr(request.app.state, "opportunity_queue", None)
    if opp_queue:
        try:
            opportunities = opp_queue.list_open(limit=50)
        except Exception:
            pass

    gaps = analyzer.analyze(blame_clusters, opportunities)

    # Save gaps to store
    for gap in gaps:
        store.save_gap(gap)

    return {"gaps": [g.to_dict() for g in gaps], "count": len(gaps)}


@router.post("/generate")
async def generate_skills(request: Request) -> dict[str, Any]:
    """Generate skills for identified gaps."""
    from agent_skills.generator import AgentSkillGenerator

    body = await request.json()
    gap_id = body.get("gap_id")

    store = _get_skill_store(request)
    generator = AgentSkillGenerator()

    # If gap_id specified, generate for that gap only
    if gap_id:
        gaps = [g for g in store.list_gaps() if g.get("gap_id") == gap_id]
    else:
        gaps = store.list_gaps()

    if not gaps:
        return {"skills": [], "count": 0, "message": "No gaps found to generate skills for"}

    generated: list[dict[str, Any]] = []
    for gap_data in gaps:
        from agent_skills.types import SkillGap
        gap = SkillGap(**{k: v for k, v in gap_data.items() if k in SkillGap.__dataclass_fields__})
        skill = generator.generate(gap)
        store.save(skill)
        generated.append(skill.to_dict())

    return {"skills": generated, "count": len(generated)}


@router.get("/")
async def list_skills(
    request: Request,
    status: str | None = Query(None),
    platform: str | None = Query(None),
) -> dict[str, Any]:
    """List generated agent skills."""
    store = _get_skill_store(request)
    skills = store.list(status=status, platform=platform)
    return {"skills": [s.to_dict() for s in skills], "count": len(skills)}


@router.get("/{skill_id}")
async def get_skill(request: Request, skill_id: str) -> dict[str, Any]:
    """Get a specific generated skill with source code."""
    store = _get_skill_store(request)
    skill = store.get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return {"skill": skill.to_dict()}


@router.post("/{skill_id}/approve")
async def approve_skill(request: Request, skill_id: str) -> dict[str, Any]:
    """Approve a generated skill for deployment."""
    store = _get_skill_store(request)
    if not store.approve(skill_id):
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return {"skill_id": skill_id, "status": "approved"}


@router.post("/{skill_id}/reject")
async def reject_skill(request: Request, skill_id: str) -> dict[str, Any]:
    """Reject a generated skill."""
    body = await request.json()
    reason = body.get("reason", "")
    store = _get_skill_store(request)
    if not store.reject(skill_id, reason):
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return {"skill_id": skill_id, "status": "rejected", "reason": reason}


@router.post("/{skill_id}/apply")
async def apply_skill(request: Request, skill_id: str) -> dict[str, Any]:
    """Apply an approved skill to the agent directory."""
    body = await request.json()
    target = body.get("target", ".")

    store = _get_skill_store(request)
    skill = store.get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    if skill.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Skill must be approved before applying (current: {skill.status})",
        )

    # Write files to target directory
    import os

    files_written: list[str] = []
    for f in skill.files:
        full_path = os.path.join(target, f.path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as fh:
            fh.write(f.content)
        files_written.append(full_path)

    return {
        "skill_id": skill_id,
        "status": "applied",
        "files_written": files_written,
    }
