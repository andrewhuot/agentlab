"""Builder Demo API routes.

Endpoints to seed, reset, and query the Builder Workspace demo data.
These routes are used by the BuilderDemo guided walkthrough page.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from builder.demo_data import (
    DEMO_ACTS,
    DEMO_PROJECT_IDS,
    reset_builder_demo,
    seed_builder_demo,
)

router = APIRouter(prefix="/api/builder/demo", tags=["builder-demo"])


@router.post("/seed")
async def seed_demo(request: Request):
    """Seed all demo data into the builder store.

    Idempotent: skips if demo projects already exist.
    Pass ?force=true to re-seed regardless.
    """
    force = request.query_params.get("force", "false").lower() == "true"
    store = request.app.state.builder_store
    count = seed_builder_demo(store, force=force)
    return {
        "seeded": count > 0,
        "objects_written": count,
        "message": (
            f"Seeded {count} demo objects."
            if count > 0
            else "Demo data already present. Pass ?force=true to re-seed."
        ),
    }


@router.post("/reset")
async def reset_demo(request: Request):
    """Delete all demo data from the builder store."""
    store = request.app.state.builder_store
    count = reset_builder_demo(store)
    return {
        "deleted": count,
        "message": f"Deleted {count} demo objects.",
    }


@router.get("/acts")
async def get_acts():
    """Return the 5 demo act definitions for the guided walkthrough."""
    return {"acts": DEMO_ACTS}


@router.post("/acts/{act_id}/play")
async def play_act(act_id: str, request: Request):
    """Activate a specific demo act.

    Ensures demo data is seeded, then returns the act definition and
    the primary project/session IDs to load in the BuilderWorkspace.
    """
    act = next((a for a in DEMO_ACTS if a["act_id"] == act_id), None)
    if act is None:
        raise HTTPException(status_code=404, detail=f"Act '{act_id}' not found.")

    store = request.app.state.builder_store
    # Auto-seed demo data if not already present
    seed_builder_demo(store, force=False)

    featured = act.get("featured_objects", {})
    project_ids = featured.get("projects", DEMO_PROJECT_IDS)
    session_ids = featured.get("sessions", [])
    task_ids = featured.get("tasks", [])

    return {
        "act": act,
        "load": {
            "project_id": project_ids[0] if project_ids else None,
            "session_id": session_ids[0] if session_ids else None,
            "task_id": task_ids[0] if task_ids else None,
        },
    }


@router.get("/status")
async def demo_status(request: Request):
    """Check whether demo data is loaded in the builder store."""
    store = request.app.state.builder_store
    projects = store.list_projects(archived=False)
    demo_loaded = any(p.project_id in DEMO_PROJECT_IDS for p in projects)

    demo_projects = []
    for project_id in DEMO_PROJECT_IDS:
        project = store.get_project(project_id)
        if project is not None:
            sessions = store.list_sessions(project_id=project_id)
            tasks = store.list_tasks(project_id=project_id)
            demo_projects.append(
                {
                    "project_id": project.project_id,
                    "name": project.name,
                    "session_count": len(sessions),
                    "task_count": len(tasks),
                }
            )

    return {
        "demo_loaded": demo_loaded,
        "demo_projects": demo_projects,
        "act_count": len(DEMO_ACTS),
    }
