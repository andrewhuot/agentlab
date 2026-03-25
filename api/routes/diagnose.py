"""Diagnosis chat API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["diagnose"])

# In-memory session store (keyed by session_id).
_sessions: dict[str, "DiagnoseSession"] = {}  # type: ignore[type-arg]


class DiagnoseChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class DiagnoseChatResponse(BaseModel):
    response: str
    actions: list[dict]
    clusters: list[dict]
    session_id: str


@router.post("/diagnose/chat")
async def diagnose_chat(req: DiagnoseChatRequest, request: Request) -> dict:
    """Start or continue an interactive diagnosis session."""
    from optimizer.diagnose_session import DiagnoseSession

    if req.session_id and req.session_id in _sessions:
        session = _sessions[req.session_id]
    else:
        # Create a new session wired to app-level dependencies when available.
        session = DiagnoseSession(
            store=getattr(request.app.state, "conversation_store", None),
            observer=getattr(request.app.state, "observer", None),
            proposer=getattr(request.app.state, "proposer", None),
            eval_runner=getattr(request.app.state, "eval_runner", None),
            deployer=getattr(request.app.state, "deployer", None),
        )
        summary = session.start()
        _sessions[session.session_id] = session

        if not req.message or req.message.strip() == "":
            # Initial request — return the opening summary without processing a message.
            return {
                "response": summary,
                "actions": _get_actions(session),
                "clusters": [c.to_dict() for c in session.clusters],
                "session_id": session.session_id,
            }

    response = session.handle_input(req.message)

    return {
        "response": response,
        "actions": _get_actions(session),
        "clusters": [c.to_dict() for c in session.clusters],
        "session_id": session.session_id,
    }


def _get_actions(session) -> list[dict]:
    """Generate available action buttons based on current session state."""
    actions: list[dict] = []
    if session.focused_cluster:
        actions.append({"label": "Show Examples", "action": "show examples"})
        if session.pending_change:
            actions.append({"label": "Apply Fix", "action": "apply"})
        else:
            actions.append({"label": "Fix This", "action": "fix"})
        actions.append({"label": "Next Issue", "action": "next"})
        actions.append({"label": "Skip", "action": "skip"})
    return actions
