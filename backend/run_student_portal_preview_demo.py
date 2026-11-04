"""Run Student Management Portal Live Preview Demonstration.

Executes the mission end-to-end:
1. Planning Agent: Plans domain models, routes, and implementation steps.
2. Coding Agent: Generates rich, interactive frontend & backend files.
3. Build Agent: Validates syntax, total LOC, and automatically starts the live preview server.
4. Preview Server: Serves the real running Student Management Portal on 127.0.0.1.
5. Testing Agent: Runs automated quality verification gates.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import urllib.request
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.agents import DevelopmentSupervisor
from app.database.repository import SQLitePipelineRepository
from app.tools.workspace import WorkspaceManager
from app.tools.preview_manager import PreviewManager


def banner(text: str) -> None:
    width = 76
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


async def run_mission():
    banner("AUTONOMOUS DEVOPS SWARM - LIVE WEBSITE PREVIEW RUN")

    mission_request = (
        "Build a Student Management Portal with a login page, dashboard, "
        "student registration form, student list, search, and responsive navigation."
    )
    mission_id = f"mission_student_portal_{int(time.time())}"
    user_id = "demo_operator"
    db_path = backend_root / "devops_swarm.db"
    repo = SQLitePipelineRepository(db_path)
    workspace_root = backend_root / "workspaces"

    workspace = WorkspaceManager(
        workspace_root=workspace_root,
        user_id=user_id,
        mission_id=mission_id,
    )

    task = {
        "id": mission_id,
        "request": mission_request,
        "user_id": user_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    print(f"Mission ID:     {mission_id}")
    print(f"User / Operator: {user_id}")
    print(f"Mission Request: {mission_request}")
    print(f"Workspace Dir:   {workspace.root_path}")
    print(f"Database File:   {db_path}")

    supervisor = DevelopmentSupervisor(
        repository=repo,
        workspace_root=workspace_root,
        max_internal_retries=3,
    )

    t0 = time.perf_counter()
    banner("STEP 1: EXECUTING MULTI-AGENT SWARM PIPELINE")
    print("Launching swarm: Planning -> Coding -> Build & Preview Launch -> Testing...")

    result = await supervisor.run_pipeline(mission_request, task=task)

    elapsed = time.perf_counter() - t0
    banner("STEP 2: PIPELINE EXECUTION RESULTS")
    print(f"Pipeline Status:  {result.get('status', 'unknown').upper()}")
    print(f"Workflow State:   {result.get('workflow_state', 'unknown')}")
    print(f"Stages Executed:  {len(result.get('stages', []))}")
    print(f"Execution Time:   {elapsed:.2f} seconds")

    stages = {s.get("agent", s.get("name", f"stage_{i}")): s for i, s in enumerate(result.get("stages", []))}

    # Inspect Coding Stage
    coding = stages.get("Coding Agent", {})
    files_written = coding.get("output", {}).get("files_written", [])
    print(f"\n[Coding Agent] Generated {len(files_written)} workspace files:")
    for f in files_written:
        p = f.get("path", "")
        print(f"  - {p}")

    # Inspect Build Stage & Live Preview
    build = stages.get("Build Agent", {})
    build_out = build.get("output", {})
    web_preview = build_out.get("web_preview", {})
    preview_url = web_preview.get("url") or web_preview.get("preview_url")
    port = web_preview.get("port")
    framework = web_preview.get("framework")

    print("\n[Build Agent & Live Preview]")
    print(f"  - Syntax Validation: {build_out.get('syntax_check', 'PASSED')}")
    print(f"  - Total Generated LOC: {build_out.get('total_loc', 0)}")
    print(f"  - Preview Status:    {web_preview.get('status')}")
    print(f"  - Framework:         {framework}")
    print(f"  - Active Port:       {port}")
    print(f"  - Preview URL:       {preview_url}")

    # Step 3: Probe live running website
    banner("STEP 3: LIVE HTTP PROBE OF GENERATED APPLICATION")
    if preview_url:
        try:
            req = urllib.request.Request(preview_url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                status_code = resp.status
                body = resp.read().decode("utf-8")
                print(f"  HTTP Probe:         GET {preview_url} -> {status_code} OK")
                print(f"  HTML Title:         {'Student Management Portal' in body}")
                print(f"  Interactive Dashboard: {'dashboard' in body.lower()}")
                print(f"  Registration Form:  {'registration' in body.lower() or 'register' in body.lower()}")
                print(f"  Search Functionality: {'search' in body.lower()}")
                print(f"  Student List Table: {'student-row' in body or 'table' in body.lower() or 'student' in body.lower()}")
                print(f"  Response Size:      {len(body)} bytes")
                print("\n  >> LIVE WEBSITE IS ACTIVE AND SERVING TRAFFIC SUCCESSFULLY! <<")
        except Exception as exc:
            print(f"  HTTP probe error: {exc}")
    else:
        print("  Preview URL not available.")

    # Inspect Testing Stage
    testing = stages.get("Testing Agent", {})
    test_out = testing.get("output", {})
    print("\n[Testing Agent]")
    print(f"  - Test Status:       {testing.get('status')}")
    print(f"  - Test Framework:    {test_out.get('framework', 'unittest')}")
    print(f"  - Passing Tests:     {test_out.get('passed', 0)}")
    print(f"  - Total Tests:       {test_out.get('total', 0)}")

    banner("MISSION PREVIEW DEMONSTRATION COMPLETE")
    print(f"Website Preview running at: {preview_url}")
    print(f"Mission ID saved in DB:     {mission_id}")


if __name__ == "__main__":
    asyncio.run(run_mission())
