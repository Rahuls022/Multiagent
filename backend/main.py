from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import re
import sqlite3
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, status
from app.database.settings_repository import create_settings_repository
from app.settings_service import SettingsService
from fastapi.middleware.cors import CORSMiddleware

from app.agents import BaseAgent, DevelopmentSupervisor, GlobalOrchestrator
from app.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserSignupRequest,
    UserResponse,
    create_access_token,
    create_user_repository,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_password,
)
from app.database import DuplicateUserError, create_pipeline_repository
from app.schemas import (
    PipelineRequest,
    WorkspaceFileUpdateRequest,
    WorkspaceGenerateRequest,
)
from app.tools.preview_manager import PreviewManager
from app.workspace import WorkspaceSecurityError, get_workspace_manager

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
    application.state.settings_repository = create_settings_repository()
    application.state.settings_service = SettingsService(application.state.settings_repository)
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


@app.get("/api/skills")
def get_skills():
    """Return installed skills from skills.sh and their dedicated agent mappings."""
    from app.skills import get_skill_registry
    reg = get_skill_registry()
    return {
        "status": "active",
        "skills": reg.list_available_skills(),
        "mappings": reg.list_agent_skills(),
        "source": "https://www.skills.sh/",
    }


# =====================================================================
# Authentication & User Safety Routes
# =====================================================================

@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def signup(payload: UserSignupRequest, request: Request):
    """Register a new user account with secure PBKDF2 password hashing."""
    user_repo = request.app.state.user_repository
    clean_email = payload.email.strip().lower()

    existing = await user_repo.get_by_email(clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in instead.",
        )

    user_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    hashed_password = hash_password(payload.password)

    user_data = {
        "id": user_id,
        "email": clean_email,
        "full_name": payload.full_name.strip(),
        "name": payload.full_name.strip(),
        "password_hash": hashed_password,
        "hashed_password": hashed_password,
        "created_at": now,
        "updated_at": now,
    }

    try:
        await user_repo.create_user(user_data)
    except (DuplicateUserError, sqlite3.IntegrityError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in instead.",
        ) from exc
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account.",
        ) from exc

    token = create_access_token({
        "sub": user_id,
        "email": clean_email,
        "name": payload.full_name.strip(),
        "full_name": payload.full_name.strip(),
        "created_at": now,
    })

    user_response = UserResponse(
        id=user_id,
        email=clean_email,
        full_name=payload.full_name.strip(),
        name=payload.full_name.strip(),
        created_at=now,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400,
        user=user_response,
    )


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest | dict[str, Any], request: Request):
    """Register a new user account (supporting frontend registration and test models)."""
    user_repo = request.app.state.user_repository
    if isinstance(payload, dict):
        raw_email = payload.get("email") or ""
        clean_email = raw_email.strip().lower()
        full_name = (payload.get("full_name") or payload.get("name") or "").strip()
        raw_password = payload.get("password") or ""
    else:
        raw_email = payload.email
        clean_email = raw_email.strip().lower()
        full_name = payload.name.strip()
        raw_password = payload.password

    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid email format")
    if len(full_name) < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Full name must be at least 2 characters")
    if len(raw_password) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 6 characters")

    existing = await user_repo.get_by_email(clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{clean_email}' already exists.",
        )

    user_id = str(uuid4())
    now_iso = datetime.now(UTC).isoformat()
    hashed_pw = hash_password(raw_password)

    user_record = {
        "id": user_id,
        "name": full_name,
        "full_name": full_name,
        "email": clean_email,
        "hashed_password": hashed_pw,
        "password_hash": hashed_pw,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        created_user = await user_repo.create_user(user_record)
    except (DuplicateUserError, sqlite3.IntegrityError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{clean_email}' already exists.",
        ) from exc
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with email '{clean_email}' already exists.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account.",
        ) from exc

    token = create_access_token({
        "sub": created_user["id"],
        "email": created_user["email"],
        "name": full_name,
        "full_name": full_name,
        "created_at": created_user["created_at"],
    })

    user_response = UserResponse(
        id=created_user["id"],
        name=full_name,
        full_name=full_name,
        email=created_user["email"],
        created_at=created_user["created_at"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400,
        user=user_response,
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, request: Request):
    """Authenticate with email and password, returning JWT bearer token."""
    user_repo = request.app.state.user_repository
    clean_email = payload.email.strip().lower()
    user = await user_repo.get_by_email(clean_email)
    stored_hash = user.get("password_hash") or user.get("hashed_password", "") if user else ""
    if not user or not verify_password(payload.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_name = user.get("full_name") or user.get("name") or clean_email.split("@")[0]
    remember = getattr(payload, "remember_me", False)
    expires_in = 30 * 86400 if remember else 86400
    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "name": user_name,
        "full_name": user_name,
        "created_at": user.get("created_at"),
    }, expires_delta=timedelta(seconds=expires_in))

    user_response = UserResponse(
        id=user["id"],
        name=user_name,
        full_name=user_name,
        email=user["email"],
        created_at=user.get("created_at", datetime.now(UTC).isoformat()),
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_response,
    )


@app.post("/api/auth/demo", response_model=TokenResponse)
async def demo_login(request: Request):
    """Instant demo access for exhibitions and quick evaluation."""
    user_repo = request.app.state.user_repository
    demo_email = "alex.morgan@swarm.dev"
    user = await user_repo.get_by_email(demo_email)
    now = datetime.now(UTC).isoformat()
    if not user:
        user_id = "demo-lead-1"
        user_record = {
            "id": user_id,
            "email": demo_email,
            "full_name": "Alex Morgan",
            "name": "Alex Morgan",
            "password_hash": hash_password("demo123"),
            "hashed_password": hash_password("demo123"),
            "created_at": now,
            "updated_at": now,
        }
        try:
            await user_repo.create_user(user_record)
        except Exception:
            pass
        user = await user_repo.get_by_email(demo_email) or user_record

    user_name = user.get("full_name") or user.get("name") or "Alex Morgan"
    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "name": user_name,
        "full_name": user_name,
        "created_at": user.get("created_at") or now,
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400 * 7,
        user=UserResponse(
            id=user["id"],
            name=user_name,
            full_name=user_name,
            email=user["email"],
            created_at=user.get("created_at") or now,
        ),
    )


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Acknowledge logout for the authenticated user session."""
    user = await get_optional_user(request)
    return {
        "message": "Signed out successfully.",
        "user_id": user["id"] if user else None,
    }


@app.get("/api/auth/me", response_model=UserResponse)
async def get_my_profile(current_user: dict[str, Any] = Depends(get_current_user)):
    """Retrieve current authenticated user profile."""
    user_name = current_user.get("full_name") or current_user.get("name") or ""
    return UserResponse(
        id=current_user["id"],
        name=user_name,
        full_name=user_name,
        email=current_user["email"],
        created_at=current_user.get("created_at") or datetime.now(UTC).isoformat(),
    )


# =====================================================================
# Protected Swarm Pipeline Routes
# =====================================================================

@app.post("/api/pipelines/development")
async def start_development_pipeline(
    payload: PipelineRequest,
    request: Request,
):
    """Run the development workflow (Planning, Coding, Build, Testing) and return observable history."""
    repo = request.app.state.pipeline_repository
    user = await get_optional_user(request)
    user_id = user["id"] if user else (payload.user_id or "anonymous")
    task = payload.to_mission_task(fallback_user_id=user_id)
    return await DevelopmentSupervisor(repository=repo).run_pipeline(task["request"], task=task)


@app.post("/api/pipelines")
async def start_swarm_pipeline(
    payload: PipelineRequest,
    request: Request,
    background: bool = False,
):
    """Run the observable development-to-operations swarm with authenticated user data binding."""
    repo = request.app.state.pipeline_repository
    user = await get_optional_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = user["id"]
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
async def simulate_failure_and_self_heal(
    payload: PipelineRequest,
    request: Request,
    background: bool = False,
):
    """Run an intentional failure test to demonstrate real failure detection & autonomous self-healing."""
    user = await get_optional_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from app.agents import BuildAgent, TestingAgent
    repo = request.app.state.pipeline_repository
    user_id = user["id"]
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
async def list_pipelines(
    request: Request,
    limit: int = 20,
):
    """Return recent delivery missions with authenticated user isolation."""
    user = await get_optional_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    safe_limit = min(max(limit, 1), 100)
    repository = request.app.state.pipeline_repository
    user_id = user["id"]
    pipelines = await repository.list(safe_limit, user_id=user_id)
    return {
        "storage": repository.storage_name,
        "user_isolated": True,
        "pipelines": pipelines,
    }


@app.get("/api/failures")
async def list_failures(
    request: Request,
    limit: int = 50,
):
    """Return stored failure memory and self-healing resolution logs from Database."""
    user = await get_optional_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
    """Operator approval gate to unblock production deployment and resume Operations Swarm."""
    repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
    dev_supervisor = DevelopmentSupervisor(repository=repo)
    orchestrator = GlobalOrchestrator(repository=repo, development_supervisor=dev_supervisor)
    result = await orchestrator.approve_and_resume_pipeline(pipeline_id)
    if not result:
        result = await dev_supervisor.approve_pipeline(pipeline_id)
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


def get_settings_service(request: Request) -> SettingsService:
    if not hasattr(request.app.state, "settings_service"):
        repo = create_settings_repository()
        request.app.state.settings_repository = repo
        request.app.state.settings_service = SettingsService(repo)
    return request.app.state.settings_service


# ============================================================================
# Enterprise DevOps Settings & Audit Endpoints
# ============================================================================

@app.get("/api/settings")
async def get_settings(request: Request):
    """Retrieve persistent enterprise DevOps swarm settings with masked secrets."""
    service = get_settings_service(request)
    return await service.get_sanitized_settings()


@app.put("/api/settings")
async def update_settings(request: Request, payload: dict[str, Any] = Body(...)):
    """Validate and persist updated DevOps settings, preserving existing unmasked secrets."""
    service = get_settings_service(request)
    user = await get_optional_user(request)
    user_id = user["email"] if user else "admin"
    settings_data = payload.get("settings") if "settings" in payload and isinstance(payload.get("settings"), dict) else payload
    updated = await service.update_settings(settings_data, user_id=user_id)
    return updated


@app.post("/api/settings/reset")
async def reset_settings(request: Request):
    """Reset settings to recommended enterprise factory defaults."""
    service = get_settings_service(request)
    user = await get_optional_user(request)
    user_id = user["email"] if user else "admin"
    return await service.reset_settings(user_id=user_id)


@app.post("/api/settings/test-connection")
async def test_integration_connection(request: Request, payload: dict[str, Any] = Body(...)):
    """Perform real connectivity probe against target service (github, docker, nvidia, webhook, slack)."""
    service = get_settings_service(request)
    target = payload.get("service", "")
    config = payload.get("config", {})
    return await service.test_connection(target, config)


@app.post("/api/settings/test-notification")
async def test_notification(request: Request, payload: dict[str, Any] = Body(...)):
    """Dispatch a real test notification event and record in audit log."""
    service = get_settings_service(request)
    user = await get_optional_user(request)
    user_id = user["email"] if user else "admin"
    return await service.test_notification(payload, user_id=user_id)


@app.get("/api/settings/audit")
async def get_audit_trail(request: Request, limit: int = 50):
    """Retrieve comprehensive enterprise DevOps audit history from settings and pipeline runs."""
    service = get_settings_service(request)
    settings_audits = await service.list_audit_events(limit=limit)
    combined = list(settings_audits)

    # Augment with pipeline history if available
    try:
        pipeline_repo = request.app.state.pipeline_repository
        recent_pipelines = await pipeline_repo.list(limit=25)
        for p in recent_pipelines:
            combined.append({
                "id": f"audit_pipe_{p.get('id', '')}",
                "timestamp": p.get("created_at") or datetime.now(UTC).isoformat(),
                "user_id": p.get("user_id") or "anonymous",
                "action": f"PIPELINE_{p.get('status', 'EXECUTED').upper()}",
                "section": "Execution & Policies",
                "details": f"Pipeline Mission: {p.get('request', '')[:50]} (Status: {p.get('status', 'unknown')})",
            })
    except Exception:
        pass

    combined.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return combined[:limit]
# ============================================================================
# Workspace & File Endpoints
# ============================================================================

@app.get("/api/workspace/projects")
async def list_workspace_projects(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all project workspaces belonging to the authenticated user."""
    workspace_mgr = get_workspace_manager()
    return {"projects": workspace_mgr.list_projects(current_user["id"])}


@app.post("/api/workspace/projects")
async def create_workspace_project(
    payload: dict[str, str],
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Create a new project workspace for the user."""
    project_id = payload.get("project_id") or payload.get("name") or "new_project"
    workspace_mgr = get_workspace_manager()
    try:
        project_dir = workspace_mgr.get_project_dir(current_user["id"], project_id, create=True)
        safe_rel_path = None
        try:
            safe_rel_path = project_dir.relative_to(workspace_mgr.root_dir).as_posix()
        except ValueError:
            safe_rel_path = None

        response: dict[str, Any] = {
            "project_id": project_dir.name,
            "message": f"Workspace initialized for project '{project_dir.name}'",
        }
        if safe_rel_path is not None:
            response["path"] = safe_rel_path
        return response
    except WorkspaceSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/workspace/files")
async def list_workspace_files(
    project_id: str = Query("project_default", description="Project workspace identifier"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all real source files in a specific project workspace."""
    workspace_mgr = get_workspace_manager()
    try:
        files = workspace_mgr.list_files(current_user["id"], project_id)
    except WorkspaceSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "project_id": project_id,
        "total_files": len(files),
        "files": files,
    }


@app.get("/api/workspace/structure")
async def get_workspace_structure(
    project_id: str = Query("project_default", description="Project workspace identifier"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return the hierarchical directory tree of the project workspace."""
    workspace_mgr = get_workspace_manager()
    try:
        return workspace_mgr.get_structure(current_user["id"], project_id)
    except WorkspaceSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/workspace/file")
async def read_workspace_file(
    path: str = Query(..., description="Relative path of file"),
    project_id: str = Query("project_default", description="Project workspace identifier"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Read actual file contents from the project workspace."""
    workspace_mgr = get_workspace_manager()
    try:
        return workspace_mgr.read_file(current_user["id"], project_id, path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except WorkspaceSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.put("/api/workspace/file")
async def update_workspace_file(
    payload: WorkspaceFileUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Update or create a file in the project workspace."""
    workspace_mgr = get_workspace_manager()
    try:
        result = workspace_mgr.write_file(
            user_id=current_user["id"],
            project_id=payload.project_id,
            relative_path=payload.path,
            content=payload.content,
        )
        return result
    except WorkspaceSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/api/workspace/file")
async def delete_workspace_file(
    path: str = Query(..., description="Relative path of file to delete"),
    project_id: str = Query("project_default", description="Project workspace identifier"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Delete a file from the project workspace."""
    workspace_mgr = get_workspace_manager()
    try:
        workspace_mgr.delete_file(current_user["id"], project_id, path)
        return {"deleted": True, "path": path}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except WorkspaceSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/workspace/generate")
async def direct_generate_workspace_code(
    payload: WorkspaceGenerateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Directly execute Planning and Coding Agent to generate project files in workspace."""
    from app.agents import PlanningAgent, CodingAgent
    task = {
        "id": str(uuid4()),
        "request": payload.request,
        "user_id": current_user["id"],
        "project_id": payload.project_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    context: dict[str, Any] = {}
    plan_stage = await PlanningAgent().run(task, context)
    context["Planning Agent"] = plan_stage
    code_stage = await CodingAgent().run(task, context)
    return {
        "plan": plan_stage,
        "coding": code_stage,
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
        matches = list(ws_root.glob(f"*/{safe_mission}"))
        if matches and matches[0].is_dir():
            return matches[0].resolve()
        if (ws_root / safe_mission).is_dir():
            return (ws_root / safe_mission).resolve()

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
    status_info = preview_mgr.get_status(pipeline_id)

    if status_info["status"] == "stopped":
        repo = getattr(request.app.state, "pipeline_repository", None) or create_pipeline_repository()
        if hasattr(repo, "get_preview_metadata"):
            try:
                db_meta = await repo.get_preview_metadata(pipeline_id)
                if db_meta:
                    status_info["framework"] = db_meta.get("framework") or status_info.get("framework")
                    status_info["entry_point"] = db_meta.get("entry_point") or status_info.get("entry_point")
            except Exception:
                pass

    return status_info


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
