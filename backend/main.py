from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.agents import BaseAgent, DevelopmentSupervisor, GlobalOrchestrator
from app.auth import (
    REMEMBER_ME_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import create_pipeline_repository, create_user_repository
from app.schemas import (
    PipelineRequest,
    TokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
    WorkspaceFileUpdateRequest,
    WorkspaceGenerateRequest,
)
from app.workspace import WorkspaceSecurityError, get_workspace_manager

load_dotenv(Path(__file__).with_name(".env"))


class SimulatedFailingBuildAgent(BaseAgent):
    """Simulates a compiler environment failure to demonstrate autonomous self-healing."""
    name = "Build Agent"

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("COMPILER_ERROR: Missing C++ build dependencies & header lockfile mismatch in build environment")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.pipeline_repository = create_pipeline_repository()
    application.state.user_repository = create_user_repository()
    if hasattr(application.state.user_repository, "init_indexes"):
        try:
            await application.state.user_repository.init_indexes()
        except Exception:
            pass
    yield
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
        "message": "Autonomous DevOps Swarm Backend Running"
    }


# ============================================================================
# Authentication API Endpoints
# ============================================================================

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
        "password_hash": hashed_password,
        "created_at": now,
        "updated_at": now,
    }

    try:
        await user_repo.create_user(user_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT if "duplicate" in str(exc).lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An account with this email address already exists." if "duplicate" in str(exc).lower() else "Failed to create user account.",
        ) from exc

    token, expires_in = create_access_token({
        "sub": user_id,
        "email": clean_email,
        "name": payload.full_name.strip(),
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user_id,
            "email": clean_email,
            "full_name": payload.full_name.strip(),
            "created_at": now,
        },
    }


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, request: Request):
    """Authenticate an existing user and return a signed expiring token."""
    user_repo = request.app.state.user_repository
    clean_email = payload.email.strip().lower()

    user = await user_repo.get_by_email(clean_email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
        )

    expires_delta = timedelta(minutes=REMEMBER_ME_EXPIRE_MINUTES) if payload.remember_me else None
    token, expires_in = create_access_token(
        {
            "sub": user["id"],
            "email": user["email"],
            "name": user["full_name"],
        },
        expires_delta=expires_delta,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"],
        },
    }


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "created_at": current_user["created_at"],
    }


@app.post("/api/auth/logout")
async def logout(current_user: dict[str, Any] = Depends(get_current_user)):
    """Acknowledge logout for the authenticated user session."""
    return {
        "message": "Signed out successfully.",
        "user_id": current_user["id"],
    }


# ============================================================================
# Protected Swarm Pipeline Endpoints
# ============================================================================

@app.post("/api/pipelines/development")
async def start_development_pipeline(
    payload: PipelineRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Run the Sprint 2 development workflow and return its observable history."""
    repo = request.app.state.pipeline_repository
    task = {
        "id": str(uuid4()),
        "request": payload.request,
        "user_id": current_user["id"],
        "project_id": payload.project_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return await DevelopmentSupervisor(repository=repo).run_pipeline(payload.request, task=task)


@app.post("/api/pipelines")
async def start_swarm_pipeline(
    payload: PipelineRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Run the observable Sprint 3 development-to-operations swarm."""
    repo = request.app.state.pipeline_repository
    dev_supervisor = DevelopmentSupervisor(repository=repo)
    return await GlobalOrchestrator(repository=repo, development_supervisor=dev_supervisor).run_pipeline(
        payload.request, user_id=current_user["id"], project_id=payload.project_id
    )


@app.post("/api/pipelines/simulate-failure")
async def simulate_failure_and_self_heal(
    payload: PipelineRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Simulate a pipeline build failure to demonstrate autonomous self-healing & DB failure memory persistence."""
    repo = request.app.state.pipeline_repository
    failing_pipeline = [
        DevelopmentSupervisor().pipeline[0],  # Planning Agent
        DevelopmentSupervisor().pipeline[1],  # Coding Agent
        SimulatedFailingBuildAgent(),         # Simulated Failure Build Agent
        DevelopmentSupervisor().pipeline[3],  # Testing Agent
    ]
    dev_supervisor = DevelopmentSupervisor(pipeline=failing_pipeline, repository=repo)
    return await GlobalOrchestrator(repository=repo, development_supervisor=dev_supervisor).run_pipeline(
        payload.request, user_id=current_user["id"], project_id=payload.project_id
    )


@app.get("/api/pipelines")
async def list_pipelines(
    request: Request,
    limit: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return recent delivery missions for the dashboard history panel."""
    safe_limit = min(max(limit, 1), 100)
    repository = request.app.state.pipeline_repository
    return {"storage": repository.storage_name, "pipelines": await repository.list(safe_limit)}


@app.get("/api/failures")
async def list_failures(
    request: Request,
    limit: int = 50,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return stored failure memory and self-healing resolution logs from Database."""
    repository = request.app.state.pipeline_repository
    failures = await repository.list_failure_memory(limit)
    return {
        "storage": repository.storage_name,
        "total_failures_healed": len(failures),
        "failures": failures
    }


@app.get("/api/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    pipeline = await request.app.state.pipeline_repository.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


# ============================================================================
# Protected Project Workspace & Real File Endpoints
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
    project_dir = workspace_mgr.get_project_dir(current_user["id"], project_id)
    return {
        "project_id": project_dir.name,
        "path": str(project_dir),
        "message": f"Workspace initialized for project '{project_dir.name}'",
    }


@app.get("/api/workspace/files")
async def list_workspace_files(
    project_id: str = Query("project_default", description="Project workspace identifier"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all real source files in a specific project workspace."""
    workspace_mgr = get_workspace_manager()
    files = workspace_mgr.list_files(current_user["id"], project_id)
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
    return workspace_mgr.get_structure(current_user["id"], project_id)


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
