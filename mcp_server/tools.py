"""AutoAgent MCP tool implementations.

Each tool function takes keyword arguments and returns a dict result.
These functions are standalone — they create their own stores/components
so the MCP server is self-contained.
"""
from __future__ import annotations
import os
from typing import Any

# Lazy imports to avoid circular dependencies
DB_PATH = os.environ.get("AUTOAGENT_DB", "conversations.db")
CONFIGS_DIR = os.environ.get("AUTOAGENT_CONFIGS", "configs")
MEMORY_DB = os.environ.get("AUTOAGENT_MEMORY_DB", "optimizer_memory.db")


def autoagent_status(**kwargs: Any) -> dict[str, Any]:
    """Get current agent health, scores, and failure summary."""
    from logger.store import ConversationStore
    from observer import Observer
    from deployer.canary import Deployer
    from optimizer.memory import OptimizationMemory

    store = ConversationStore(db_path=DB_PATH)
    observer = Observer(store)
    deployer = Deployer(configs_dir=CONFIGS_DIR, store=store)
    memory = OptimizationMemory(db_path=MEMORY_DB)

    report = observer.observe()
    metrics = report.metrics
    dep_status = deployer.status()
    attempts = memory.recent(limit=1)

    return {
        "config_version": dep_status.get("active_version"),
        "conversations": store.count(),
        "eval_score": attempts[0].score_after if attempts else None,
        "safety_violation_rate": metrics.safety_violation_rate,
        "success_rate": metrics.success_rate,
        "avg_latency_ms": metrics.avg_latency_ms,
        "failure_buckets": report.failure_buckets,
    }


def autoagent_explain(**kwargs: Any) -> dict[str, Any]:
    """Get a plain-English summary of the agent's current state."""
    from logger.store import ConversationStore
    from observer import Observer

    store = ConversationStore(db_path=DB_PATH)
    observer = Observer(store)
    report = observer.observe()
    metrics = report.metrics

    sr = metrics.success_rate
    if sr >= 0.9:
        health = "Excellent"
    elif sr >= 0.75:
        health = "Good"
    elif sr >= 0.5:
        health = "Needs Work"
    else:
        health = "Critical"

    buckets = report.failure_buckets or {}
    top = max(buckets, key=buckets.get) if buckets else None

    return {
        "health": health,
        "success_rate": sr,
        "top_failure": top,
        "failure_buckets": buckets,
        "summary": f"Agent health is {health} ({sr:.0%} success rate). Top failure: {top or 'none'}.",
    }


def autoagent_diagnose(**kwargs: Any) -> dict[str, Any]:
    """Run failure analysis and return clustered issues."""
    from optimizer.diagnose_session import DiagnoseSession
    session = DiagnoseSession()
    session.start()
    return session.to_dict()


def autoagent_get_failures(failure_family: str = "", limit: int = 5, **kwargs: Any) -> list[dict]:
    """Get sample conversations for a specific failure type."""
    from logger.store import ConversationStore
    store = ConversationStore(db_path=DB_PATH)
    records = store.get_failures(limit=limit)
    return [
        {
            "conversation_id": getattr(r, 'conversation_id', ''),
            "user_message": r.user_message,
            "outcome": r.outcome,
            "error_message": r.error_message,
        }
        for r in records
        if not failure_family or failure_family in (r.error_message or "")
    ][:limit]


def autoagent_suggest_fix(description: str = "", **kwargs: Any) -> dict[str, Any]:
    """Suggest a config fix based on NL description."""
    from optimizer.nl_editor import NLEditor
    editor = NLEditor()
    config = {}
    try:
        from deployer.canary import Deployer
        from logger.store import ConversationStore
        store = ConversationStore(db_path=DB_PATH)
        deployer = Deployer(configs_dir=CONFIGS_DIR, store=store)
        config = deployer.get_active_config() or {}
    except Exception:
        pass
    result = editor.apply_and_eval(description, config)
    return result.to_dict()


def autoagent_edit(description: str = "", auto_apply: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Apply a natural language edit to the agent config."""
    from optimizer.nl_editor import NLEditor
    editor = NLEditor()
    config = {}
    try:
        from deployer.canary import Deployer
        from logger.store import ConversationStore
        store = ConversationStore(db_path=DB_PATH)
        deployer = Deployer(configs_dir=CONFIGS_DIR, store=store)
        config = deployer.get_active_config() or {}
    except Exception:
        pass
    result = editor.apply_and_eval(description, config)
    return result.to_dict()


def autoagent_eval(config_path: str | None = None, **kwargs: Any) -> dict[str, Any]:
    """Run eval suite and return scores."""
    from evals.runner import EvalRunner
    from agent.config.runtime import load_runtime_config
    runtime = load_runtime_config()
    runner = EvalRunner(history_db_path=runtime.eval.history_db_path)
    config = None
    if config_path:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
    score = runner.run(config=config)
    return {
        "quality": score.quality,
        "safety": score.safety,
        "latency": score.latency,
        "cost": score.cost,
        "composite": score.composite,
        "passed_cases": score.passed_cases,
        "total_cases": score.total_cases,
    }


def autoagent_eval_compare(config_a: str = "", config_b: str = "", **kwargs: Any) -> dict[str, Any]:
    """Compare two configs via eval."""
    from evals.runner import EvalRunner
    from agent.config.runtime import load_runtime_config
    import yaml
    runtime = load_runtime_config()
    runner = EvalRunner(history_db_path=runtime.eval.history_db_path)

    with open(config_a) as f:
        ca = yaml.safe_load(f)
    with open(config_b) as f:
        cb = yaml.safe_load(f)

    score_a = runner.run(config=ca)
    score_b = runner.run(config=cb)
    winner = "a" if score_a.composite >= score_b.composite else "b"
    return {
        "config_a_score": score_a.composite,
        "config_b_score": score_b.composite,
        "winner": winner,
        "delta": abs(score_a.composite - score_b.composite),
    }


def autoagent_skill_gaps(**kwargs: Any) -> list[dict]:
    """Identify capabilities the agent is missing."""
    try:
        from agent_skills.gap_analyzer import GapAnalyzer
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[], opportunities=[])
        return [{"description": g.description, "priority": g.priority} for g in gaps]
    except Exception:
        return []


def autoagent_skill_recommend(**kwargs: Any) -> list[dict]:
    """Recommend optimization skills."""
    try:
        from registry.skill_store import SkillStore
        store = SkillStore(db_path=os.environ.get("AUTOAGENT_REGISTRY_DB", "registry.db"))
        skills = store.recommend()
        result = [
            {"name": s.name, "category": s.category, "description": s.description}
            for s in skills
        ]
        store.close()
        return result
    except Exception:
        return []


def autoagent_replay(limit: int = 10, **kwargs: Any) -> list[dict]:
    """Get optimization history."""
    from optimizer.memory import OptimizationMemory
    memory = OptimizationMemory(db_path=MEMORY_DB)
    attempts = memory.recent(limit=limit)
    return [
        {
            "version": i + 1,
            "score_before": a.score_before,
            "score_after": a.score_after,
            "status": a.status,
            "change_description": a.change_description,
            "timestamp": a.timestamp,
        }
        for i, a in enumerate(reversed(attempts))
    ]


def autoagent_diff(version_a: int = 0, version_b: int = 0, **kwargs: Any) -> str:
    """Get diff between two config versions."""
    try:
        from deployer.versioning import ConfigVersionManager
        vm = ConfigVersionManager(configs_dir=CONFIGS_DIR)
        config_a = vm.load_version(version_a)
        config_b = vm.load_version(version_b)
        if config_a and config_b:
            from agent.config.schema import validate_config, config_diff
            va = validate_config(config_a)
            vb = validate_config(config_b)
            return config_diff(va, vb)
    except Exception:
        pass
    return "Could not compute diff."


# Tool registry — maps tool name to (function, MCPToolDef)
TOOL_REGISTRY: dict[str, tuple] = {}

def _register_tools():
    from mcp_server.types import MCPToolDef, MCPToolParam
    global TOOL_REGISTRY
    TOOL_REGISTRY = {
        "autoagent_status": (autoagent_status, MCPToolDef(
            name="autoagent_status",
            description="Get current agent health, scores, and failure summary.",
        )),
        "autoagent_explain": (autoagent_explain, MCPToolDef(
            name="autoagent_explain",
            description="Get a plain-English summary of the agent's current state.",
        )),
        "autoagent_diagnose": (autoagent_diagnose, MCPToolDef(
            name="autoagent_diagnose",
            description="Run failure analysis and return clustered issues with root causes.",
        )),
        "autoagent_get_failures": (autoagent_get_failures, MCPToolDef(
            name="autoagent_get_failures",
            description="Get sample conversations for a specific failure type.",
            parameters=[
                MCPToolParam(name="failure_family", description="Failure type to filter by", required=True),
                MCPToolParam(name="limit", description="Max results", type="integer"),
            ],
        )),
        "autoagent_suggest_fix": (autoagent_suggest_fix, MCPToolDef(
            name="autoagent_suggest_fix",
            description="Suggest a config fix based on natural language description.",
            parameters=[
                MCPToolParam(name="description", description="NL description of the fix", type="string", required=True),
            ],
        )),
        "autoagent_edit": (autoagent_edit, MCPToolDef(
            name="autoagent_edit",
            description="Apply a natural language edit to the agent config.",
            parameters=[
                MCPToolParam(name="description", description="NL description of the edit", type="string", required=True),
                MCPToolParam(name="auto_apply", description="Auto-apply without confirmation", type="boolean"),
            ],
        )),
        "autoagent_eval": (autoagent_eval, MCPToolDef(
            name="autoagent_eval",
            description="Run eval suite and return scores.",
            parameters=[
                MCPToolParam(name="config_path", description="Optional config YAML path", type="string"),
            ],
        )),
        "autoagent_eval_compare": (autoagent_eval_compare, MCPToolDef(
            name="autoagent_eval_compare",
            description="Compare two configs via eval and return winner.",
            parameters=[
                MCPToolParam(name="config_a", description="Path to first config", type="string", required=True),
                MCPToolParam(name="config_b", description="Path to second config", type="string", required=True),
            ],
        )),
        "autoagent_skill_gaps": (autoagent_skill_gaps, MCPToolDef(
            name="autoagent_skill_gaps",
            description="Identify capabilities the agent is missing based on failure analysis.",
        )),
        "autoagent_skill_recommend": (autoagent_skill_recommend, MCPToolDef(
            name="autoagent_skill_recommend",
            description="Recommend optimization skills based on current failure patterns.",
        )),
        "autoagent_replay": (autoagent_replay, MCPToolDef(
            name="autoagent_replay",
            description="Get optimization history showing config evolution.",
            parameters=[
                MCPToolParam(name="limit", description="Max entries to return", type="integer"),
            ],
        )),
        "autoagent_diff": (autoagent_diff, MCPToolDef(
            name="autoagent_diff",
            description="Get unified diff between two config versions.",
            parameters=[
                MCPToolParam(name="version_a", description="First version number", type="integer", required=True),
                MCPToolParam(name="version_b", description="Second version number", type="integer", required=True),
            ],
        )),
    }

_register_tools()
