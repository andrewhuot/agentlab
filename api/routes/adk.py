"""ADK (Agent Development Kit) API routes — import, export, deploy."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/adk", tags=["adk"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AdkImportRequest(BaseModel):
    path: str
    output_dir: str = "."

class AdkImportResponse(BaseModel):
    config_path: str
    snapshot_path: str
    agent_name: str
    surfaces_mapped: list[str]
    tools_imported: int

class AdkExportRequest(BaseModel):
    config: dict
    snapshot_path: str
    output_dir: str
    dry_run: bool = False

class AdkExportResponse(BaseModel):
    output_path: str | None
    changes: list[dict]
    files_modified: int

class AdkDeployRequest(BaseModel):
    path: str
    target: str  # "cloud-run" or "vertex-ai"
    project: str
    region: str = "us-central1"

class AdkDeployResponse(BaseModel):
    target: str
    url: str
    status: str
    deployment_info: dict = Field(default_factory=dict)

class AdkStatusResponse(BaseModel):
    agent_name: str
    model: str
    tools_count: int
    sub_agents: list[str]
    has_config: bool

class AdkDiffResponse(BaseModel):
    changes: list[dict]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/import", response_model=AdkImportResponse, status_code=201)
async def import_adk_agent(body: AdkImportRequest) -> AdkImportResponse:
    """Import an ADK agent from local directory."""
    from adk import AdkParser, AdkMapper, AdkImporter
    try:
        parser = AdkParser()
        mapper = AdkMapper()
        importer = AdkImporter(parser, mapper)
        result = importer.import_agent(
            agent_path=body.path,
            output_dir=body.output_dir,
        )
        return AdkImportResponse(
            config_path=result.config_path,
            snapshot_path=result.snapshot_path,
            agent_name=result.agent_name,
            surfaces_mapped=result.surfaces_mapped,
            tools_imported=result.tools_imported,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/export", response_model=AdkExportResponse)
async def export_adk_agent(body: AdkExportRequest) -> AdkExportResponse:
    """Export optimized config back to ADK source."""
    from adk import AdkParser, AdkMapper, AdkExporter
    try:
        parser = AdkParser()
        mapper = AdkMapper()
        exporter = AdkExporter(parser, mapper)
        result = exporter.export_agent(
            config=body.config,
            snapshot_path=body.snapshot_path,
            output_dir=body.output_dir,
            dry_run=body.dry_run,
        )
        return AdkExportResponse(
            output_path=result.output_path,
            changes=result.changes,
            files_modified=result.files_modified,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/deploy", response_model=AdkDeployResponse)
async def deploy_adk_agent(body: AdkDeployRequest) -> AdkDeployResponse:
    """Deploy ADK agent to Cloud Run or Vertex AI."""
    from adk import AdkDeployer
    try:
        if body.target not in ["cloud-run", "vertex-ai"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target: {body.target}. Must be 'cloud-run' or 'vertex-ai'."
            )
        deployer = AdkDeployer(project=body.project, region=body.region)
        if body.target == "cloud-run":
            result = deployer.deploy_to_cloud_run(body.path)
        else:
            result = deployer.deploy_to_vertex_ai(body.path)
        return AdkDeployResponse(
            target=result.target,
            url=result.url,
            status=result.status,
            deployment_info=result.deployment_info,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/status", response_model=AdkStatusResponse)
async def get_adk_status(path: str) -> AdkStatusResponse:
    """Get agent structure summary."""
    from pathlib import Path
    from adk import AdkParser
    try:
        if not path:
            raise HTTPException(status_code=400, detail="path is required")
        parser = AdkParser()
        tree = parser.parse_agent_directory(Path(path))
        return AdkStatusResponse(
            agent_name=tree.root.name,
            model=tree.root.model or "gemini-2.0-flash",
            tools_count=len(tree.root.tools),
            sub_agents=[sa.name for sa in tree.root.sub_agents],
            has_config=bool(tree.root.generate_config),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/diff", response_model=AdkDiffResponse)
async def preview_adk_diff(config_path: str, snapshot_path: str) -> AdkDiffResponse:
    """Preview export changes."""
    import yaml
    from pathlib import Path
    from adk import AdkParser, AdkMapper, AdkExporter
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid config: {exc}")

    try:
        parser = AdkParser()
        mapper = AdkMapper()
        exporter = AdkExporter(parser, mapper)
        changes = exporter.preview_changes(config, snapshot_path)
        return AdkDiffResponse(changes=changes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
