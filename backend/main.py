from contextlib import asynccontextmanager
from datetime import UTC, datetime
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.agents import BaseAgent, DevelopmentSupervisor, GlobalOrchestrator
from app.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    create_access_token,
    create_user_repository,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_password,
)
from app.database import create_pipeline_repository
from app.schemas import PipelineRequest
from app.tools.preview_manager import PreviewManager

load_dotenv(Path(__file__).with_name(".env"))


class ControlledBugCodingAgent(BaseAgent):
    """Writes real code with a controlled bug to verify real failure detection and autonomous self-healing."""
    name = "Coding Agent"

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        workspace = context["workspace"]
        code = (
            "def calculate_total(items: list[int]) -> int:\n"
            "    # Intentional defect: subtracting 1 causes test assertion failure\n"
            "    return sum(items) - 1\n"
        )
        test = (
            "import unittest\n"
            "from app_logic import calculate_total\n\n"
            "class TestCalculation(unittest.TestCase):\n"
            "    def test_calculate_total(self):\n"
            "        self.assertEqual(calculate_total([10, 20, 30]), 60)\n"
        )
        workspace.write_file("app_logic.py", code)
        workspace.write_file("tests/test_logic.py", test)
        return {
            "summary": "Generated module with intentional logic defect to verify autonomous self-healing",
            "files_written": [
                {"path": "app_logic.py", "lines": 4},
                {"path": "tests/test_logic.py", "lines": 7},
            ],
            "files_to_create": [
                {"path": "app_logic.py", "language": "python", "code": code, "purpose": "Calculation module"},
                {"path": "tests/test_logic.py", "language": "python", "code": test, "purpose": "Unit test suite"},
            ],
        }



# Backward-compatible alias for existing test imports
SimulatedFailingBuildAgent = ControlledBugCodingAgent


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.pipeline_repository = create_pipeline_repository()
    application.state.user_repository = create_user_repository()
    application.state.preview_manager = PreviewManager()
    await application.state.pipeline_repository.init()
    if hasattr(application.state.user_repository, "init_indexes"):
        try:
            await application.state.user_repository.init_indexes()
        except Exception:
            pass
    yield
    try:
        application.state.preview_manager.stop_all()
    except Exception:
        pass
    await application.state.pipeline_repository.close()
    await application.state.user_repository.close()


app = FastAPI(
    title="Autonomous DevOps Swarm API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Autonomous DevOps Swarm Backend Running",
        "version": "1.0.0",
    }


@app.get("/api/database/status")
async def get_database_status(request: Request):
    """Return live MongoDB connectivity health, collections, document counts, and instructions."""
    repo = request.app.state.pipeline_repository
    return await repo.get_status()


# =====================================================================
# Authentication & User Safety Routes
# =====================================================================

@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, request: Request):
    """Register a new user account with salted password hashing and issue a JWT token."""
    user_repo = request.app.state.user_repository
    existing = await user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    user_id = str(uuid4())
    now_iso = datetime.now(UTC).isoformat()
    hashed_pw = hash_password(payload.password)

    user_record = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": payload.email.lower().strip(),
        "hashed_password": hashed_pw,
        "created_at": now_iso,
    }

    created_user = await user_repo.create_user(user_record)
    user_response = UserResponse(
        id=created_user["id"],
        name=created_user["name"],
        email=created_user["email"],
        created_at=created_user["created_at"],
    )

    token = create_access_token({
        "sub": created_user["id"],
        "email": created_user["email"],
        "name": created_user["name"],
        "created_at": created_user["created_at"],
    })

    return TokenResponse(access_token=token, token_type="bearer", user=user_response)


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, request: Request):
    """Authenticate with email and password, returning JWT bearer token."""
    user_repo = request.app.state.user_repository
    user = await user_repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_response = UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )

    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "created_at": user["created_at"],
    })

    return TokenResponse(access_token=token, token_type="bearer", user=user_response)


@app.get("/api/auth/me", response_model=UserResponse)
async def get_my_profile(current_user: dict[str, Any] = Depends(get_current_user)):
    """Retrieve current authenticated user profile."""
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user["created_at"],
    )


# =====================================================================
# Pipeline Routes (with User Data Safety)
# =====================================================================

@app.post("/api/pipelines/development")
async def start_development_pipeline(payload: PipelineRequest, request: Request):
    """Run the development workflow (Planning, Coding, Build, Testing) and return observable history."""
    repo = request.app.state.pipeline_repository
    user = await get_optional_user(request)
    user_id = user["id"] if user else (payload.user_id or "anonymous")

    task = payload.to_mission_task(fallback_user_id=user_id)
    return await DevelopmentSupervisor(repository=repo).run_pipeline(task["request"], task=task)


@app.post("/api/pipelines")
async def start_swarm_pipeline(payload: PipelineRequest, request: Request, background: bool = False):
    """Run the observable development-to-operations swarm with authenticated user data binding."""
    repo = request.app.state.pipeline_repository
    user = await get_optional_user(request)
    user_id = user["id"] if user else (payload.user_id or "anonymous")

    task = payload.to_mission_task(fallback_user_id=user_id)
    dev_supervisor = DevelopmentSupervisor(repository=repo)
    orchestrator = GlobalOrchestrator(repository=repo, development_supervisor=dev_supervisor)

    if background:
        import asyncio
        initial_pipeline = orchestrator._result(
            task, "running", [], [],
            [{"pipeline_id": task["id"], "agent": "Global Orchestrator", "event": "PIPELINE_STARTED", "timestamp": datetime.now(UTC).isoformat()}],
            "Planning Agent",
        )
        await repo.create(initial_pipeline)

        async def _exec():
            try:
                await orchestrator.run_pipeline(task["request"], task=task, user_id=user_id)
            except Exception:
                pass

        asyncio.create_task(_exec())
        return initial_pipeline

    return await orchestrator.run_pipeline(task["request"], task=task, user_id=user_id)


@app.post("/api/pipelines/simulate-failure")
async def simulate_failure_and_self_heal(payload: PipelineRequest, request: Request, background: bool = False):
    """Run an intentional failure test to demonstrate real failure detection & autonomous self-healing."""
    from app.agents import BuildAgent, TestingAgent
    repo = request.app.state.pipeline_repository
    user = await get_optional_user(request)
    user_id = user["id"] if user else (payload.user_id or "anonymous")

    task = payload.to_mission_task(fallback_user_id=user_id)
    task["request"] = f"{payload.request} (Self-Healing Verification Test)"
    
    failing_pipeline = [
        DevelopmentSupervisor()._resolve_pipeline("")[0],  # Planning Agent
        ControlledBugCodingAgent(),                        # Writes code with intentional logic defect
        BuildAgent(),                                      # Build Agent
        TestingAgent(),                                    # Testing Agent (fails, triggering self-healing)
    ]
    dev_supervisor = DevelopmentSupervisor(pipeline=failing_pipeline, repository=repo)
    orchestrator = GlobalOrchestrator(repository=repo, development_supervisor=dev_supervisor)

    if background:
        import asyncio
        initial_pipeline = orchestrator._result(
            task, "running", [], [],
            [{"pipeline_id": task["id"], "agent": "Global Orchestrator", "event": "PIPELINE_STARTED", "timestamp": datetime.now(UTC).isoformat()}],
            "Planning Agent",
        )
        await repo.create(initial_pipeline)

        async def _exec():
            try:
                await orchestrator.run_pipeline(task["request"], task=task, user_id=user_id)
            except Exception:
                pass

        asyncio.create_task(_exec())
        return initial_pipeline

    return await orchestrator.run_pipeline(task["request"], task=task, user_id=user_id)





@app.get("/api/pipelines")
async def list_pipelines(request: Request, limit: int = 20):
    """Return recent delivery missions. If user is authenticated, isolates their pipelines to keep user data safe."""
    safe_limit = min(max(limit, 1), 100)
    repository = request.app.state.pipeline_repository
    user = await get_optional_user(request)
    user_id = user["id"] if user else None

    pipelines = await repository.list(safe_limit, user_id=user_id)
    return {
        "storage": repository.storage_name,
        "user_isolated": bool(user_id),
        "pipelines": pipelines,
    }


@app.get("/api/failures")
async def list_failures(request: Request, limit: int = 50):
    """Return stored failure memory and self-healing resolution logs from Database."""
    repository = request.app.state.pipeline_repository
    failures = await repository.list_failure_memory(limit)
    return {
        "storage": repository.storage_name,
        "total_failures_healed": len(failures),
        "failures": failures,
    }


@app.get("/api/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str, request: Request):
    pipeline = await request.app.state.pipeline_repository.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@app.post("/api/pipelines/{pipeline_id}/approve")
async def approve_pipeline(pipeline_id: str, request: Request):
    """Operator approval gate to unblock production deployment."""
    repo = request.app.state.pipeline_repository
    supervisor = DevelopmentSupervisor(repository=repo)
    result = await supervisor.approve_pipeline(pipeline_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found or not awaiting approval.")
    return {"status": "approved", "pipeline": result}


@app.post("/api/pipelines/{pipeline_id}/reject")
async def reject_pipeline(pipeline_id: str, request: Request):
    """Operator rejection gate to cancel production deployment."""
    repo = request.app.state.pipeline_repository
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    reason = body.get("reason", "Operator rejected") if isinstance(body, dict) else "Operator rejected"

    supervisor = DevelopmentSupervisor(repository=repo)
    result = await supervisor.reject_pipeline(pipeline_id, reason=reason)
    if not result:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found.")
    return {"status": "cancelled", "reason": reason, "pipeline": result}


@app.post("/api/pipelines/{pipeline_id}/resume")
async def resume_pipeline(pipeline_id: str, request: Request):
    """Crash recovery: Resume execution of an interrupted or failed pipeline from where it stopped."""
    repo = request.app.state.pipeline_repository
    supervisor = DevelopmentSupervisor(repository=repo)
    try:
        result = await supervisor.resume_pipeline(pipeline_id)
        return {"status": "resumed", "pipeline": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/telemetry")
async def get_telemetry():
    """Return aggregated LLM token usage, request counts, latency, and estimated cost."""
    from app.llm import LLMClient
    client = LLMClient()
    metrics = client.get_metrics()
    return {
        "provider": client.provider_name,
        "model": client.model,
        "configured": client.is_configured,
        "metrics": metrics,
    }


# =====================================================================
# Live Website Preview & Mission Workspace APIs
# =====================================================================

def _resolve_mission_workspace_dir(pipeline_id: str, pipeline_doc: dict[str, Any] | None = None) -> Path:
    """Safely locate the mission workspace directory on disk."""
    preview_mgr = PreviewManager()
    server = preview_mgr.get_server(pipeline_id)
    if server and server.workspace_dir and server.workspace_dir.exists():
        return server.workspace_dir.resolve()

    if pipeline_doc:
        ws_p = pipeline_doc.get("workspace_path") or pipeline_doc.get("teams", {}).get("development", {}).get("workspace_path")
        if ws_p:
            p = Path(ws_p).resolve()
            if p.exists() and p.is_dir():
                return p

    ws_root = Path(os.getenv("WORKSPACE_ROOT", Path(__file__).resolve().parent / "workspaces")).resolve()
    safe_mission = re.sub(r"[^a-zA-Z0-9_\-]", "_", pipeline_id)

    if ws_root.exists():
        # Search all user folders for this mission
        matches = list(ws_root.glob(f"*/{safe_mission}"))
        if matches and matches[0].is_dir():
            return matches[0].resolve()
        if (ws_root / safe_mission).is_dir():
            return (ws_root / safe_mission).resolve()

    # Default fallback
    target = ws_root / "anonymous" / safe_mission
    target.mkdir(parents=True, exist_ok=True)
    return target.resolve()


@app.get("/api/pipelines/{pipeline_id}/preview/files")
async def list_preview_files(pipeline_id: str, request: Request):
    """List real files generated in the mission workspace with structure and categories."""
    repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
    pipeline_doc = None
    try:
        if hasattr(repo, "get"):
            pipeline_doc = await repo.get(pipeline_id)
    except Exception:
        pipeline_doc = None
    ws_dir = _resolve_mission_workspace_dir(pipeline_id, pipeline_doc)

    preview_mgr = getattr(request.app.state, "preview_manager", None) or PreviewManager()
    files = preview_mgr.list_workspace_files(ws_dir)
    detection = preview_mgr.detect_frontend(ws_dir)

    categories = {
        "frontend": [f for f in files if f.get("category") == "frontend"],
        "backend": [f for f in files if f.get("category") == "backend"],
        "database": [f for f in files if f.get("category") == "database"],
        "tests": [f for f in files if f.get("category") == "tests"],
        "config": [f for f in files if f.get("category") == "config"],
        "devops": [f for f in files if f.get("category") == "devops"],
        "other": [f for f in files if f.get("category") not in ("frontend", "backend", "database", "tests", "config", "devops")],
    }
    return {
        "pipeline_id": pipeline_id,
        "mission_id": pipeline_id,
        "workspace_path": str(ws_dir),
        "framework": detection.get("framework", "HTML5 / Web App"),
        "entry_point": detection.get("entry_point", "index.html"),
        "files": files,
        "categories": categories,
        "total_files": len([f for f in files if not f["is_dir"]]),
    }


@app.get("/api/pipelines/{pipeline_id}/preview/file")
async def read_preview_file(pipeline_id: str, path: str, request: Request):
    """Read actual source file content with syntax metadata, protecting against path traversal."""
    if not path or not path.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'path' is required.")

    repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
    pipeline_doc = None
    try:
        if hasattr(repo, "get"):
            pipeline_doc = await repo.get(pipeline_id)
    except Exception:
        pipeline_doc = None
    ws_dir = _resolve_mission_workspace_dir(pipeline_id, pipeline_doc)

    preview_mgr = getattr(request.app.state, "preview_manager", None) or PreviewManager()
    try:
        file_info = preview_mgr.read_workspace_file(ws_dir, path)
        file_info["pipeline_id"] = pipeline_id
        return file_info
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {exc}") from exc


@app.post("/api/pipelines/{pipeline_id}/preview/start")
async def start_mission_preview(pipeline_id: str, request: Request):
    """Start the mission-specific preview server process and return the live URL."""
    repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
    user = await get_optional_user(request)
    user_id = user["id"] if user else "anonymous"

    pipeline_doc = None
    try:
        if hasattr(repo, "get"):
            pipeline_doc = await repo.get(pipeline_id)
    except Exception:
        pipeline_doc = None
    ws_dir = _resolve_mission_workspace_dir(pipeline_id, pipeline_doc)

    preview_mgr = getattr(request.app.state, "preview_manager", None) or PreviewManager()
    try:
        result = preview_mgr.start_preview(
            mission_id=pipeline_id,
            workspace_dir=ws_dir,
            user_id=user_id,
            timeout_seconds=12.0,
        )

        # Persist preview metadata in database
        if hasattr(repo, "save_preview_metadata"):
            db_record = {
                "mission_id": pipeline_id,
                "workspace_path": str(ws_dir),
                "preview_url": result["preview_url"],
                "port": result["port"],
                "process_id": result["pid"],
                "preview_status": "running",
                "framework": result["framework"],
                "entry_point": result["entry_point"],
            }
            try:
                await repo.save_preview_metadata(db_record)
            except Exception:
                pass

        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start preview server: {exc}") from exc


@app.get("/api/pipelines/{pipeline_id}/preview/status")
async def get_mission_preview_status(pipeline_id: str, request: Request):
    """Get status of the mission preview server."""
    preview_mgr = getattr(request.app.state, "preview_manager", None) or PreviewManager()
    status = preview_mgr.get_status(pipeline_id)

    # If stopped in memory, check if database has record
    if status["status"] == "stopped":
        repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
        if hasattr(repo, "get_preview_metadata"):
            try:
                db_meta = await repo.get_preview_metadata(pipeline_id)
                if db_meta:
                    status["framework"] = db_meta.get("framework") or status.get("framework")
                    status["entry_point"] = db_meta.get("entry_point") or status.get("entry_point")
            except Exception:
                pass

    return status


@app.get("/api/pipelines/{pipeline_id}/preview/logs")
async def get_mission_preview_logs(pipeline_id: str, request: Request):
    """Retrieve collected preview startup and runtime logs."""
    preview_mgr = getattr(request.app.state, "preview_manager", None) or PreviewManager()
    logs = preview_mgr.get_logs(pipeline_id)
    return {"mission_id": pipeline_id, "logs": logs}


@app.post("/api/pipelines/{pipeline_id}/preview/stop")
async def stop_mission_preview(pipeline_id: str, request: Request):
    """Stop the mission preview server process."""
    preview_mgr = getattr(request.app.state, "preview_manager", None) or PreviewManager()
    result = preview_mgr.stop_preview(pipeline_id)

    repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
    if hasattr(repo, "save_preview_metadata"):
        try:
            await repo.save_preview_metadata({
                "mission_id": pipeline_id,
                "preview_status": "stopped",
            })
        except Exception:
            pass

    return result

