"""Real End-to-End Autonomous DevOps Swarm Mission Execution Demo.

Mission:
"Build a REST API for a task management application with user authentication,
CRUD operations, database persistence, unit tests, Docker support,
API documentation, self-healing, security validation, and git commit."
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.agents import DevelopmentSupervisor
from app.database.repository import SQLitePipelineRepository
from app.llm import LLMClient
from app.tools.workspace import WorkspaceManager


def print_banner(text: str) -> None:
    width = 75
    print("\n" + "=" * width)
    print(f" {text}")
    print("=" * width)


async def main() -> None:
    print_banner("AUTONOMOUS DEVOPS SWARM - REAL-WORLD MISSION DEMO")
    print(f"Execution Root: {backend_root}")

    # 1. Initialize Client & Check Configuration
    client = LLMClient()
    print(f"LLM Provider:     {client.provider_name.upper()}")
    print(f"Model ID:         {client.model}")
    print(f"Configured:       {client.is_configured}")

    if not client.is_configured:
        print("\n[ERROR] LLM API Key is not configured in backend/.env!")
        sys.exit(1)

    # 2. Setup Persistent Mission Workspace and SQLite Repository
    mission_id = f"mission_{int(time.time())}"
    user_id = "real_operator"
    db_path = backend_root / "devops_swarm.db"
    repo = SQLitePipelineRepository(db_path)
    workspace_root = backend_root / "workspaces"

    workspace = WorkspaceManager(
        workspace_root=workspace_root,
        user_id=user_id,
        mission_id=mission_id,
    )

    mission_request = (
        "Build a REST API for a task management application with user authentication, "
        "CRUD operations, database persistence, unit tests, Docker support, API documentation, "
        "self-healing, security validation, and git commit."
    )

    task = {
        "id": mission_id,
        "request": mission_request,
        "user_id": user_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    print_banner("MISSION SPECIFICATION")
    print(f"Mission ID:       {mission_id}")
    print(f"Operator ID:      {user_id}")
    print(f"Request:          {mission_request}")
    print(f"Sandbox Path:     {workspace.root_path}")
    print(f"Database Path:    {db_path}")

    # 3. Instantiate Adaptive Development Supervisor
    supervisor = DevelopmentSupervisor(
        repository=repo,
        workspace_root=workspace_root,
        max_internal_retries=3,
    )

    t0 = time.perf_counter()
    print_banner("STARTING AUTONOMOUS MISSION WORKFLOW")
    print("Supervisor initiating adaptive workflow: Planning -> Coding -> Build -> Testing -> Security -> Git Release...")

    try:
        result = await supervisor.run_pipeline(mission_request, task=task)
    except Exception as exc:
        print(f"\n[EXCEPTION] Workflow failed with unhandled error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    duration_total = time.perf_counter() - t0

    # 4. Display Agent Execution Stages
    print_banner("AGENT STAGE EXECUTION RESULTS")
    stages = result.get("stages", [])
    for idx, stage in enumerate(stages, start=1):
        status_sym = "[OK]" if stage.get("status") in ("completed", "healed") else "[FAIL]"
        agent_name = stage.get("agent", "Unknown")
        print(f"\n{status_sym} Stage {idx}: {agent_name} ({stage.get('duration_ms', 0)}ms)")
        output = stage.get("output", {})
        if agent_name == "Planning Agent":
            print(f"   Architecture:   {output.get('architecture', {})}")
            print(f"   Planned Files:  {[f['path'] for f in output.get('files_to_create', [])]}")
        elif agent_name == "Coding Agent":
            print(f"   Files Written:  {[f['path'] for f in output.get('files_written', [])]}")
            print(f"   LOC Total:      {sum(f.get('lines', 0) for f in output.get('files_written', []))}")
        elif agent_name == "Build Agent":
            print(f"   AST Check:      {'PASS' if output.get('success') else 'FAIL'}")
            print(f"   Files Checked:  {len(output.get('syntax_checks', []))}")
            print(f"   Code Metrics:   {output.get('total_classes', 0)} classes, {output.get('total_functions', 0)} functions, {output.get('total_loc', 0)} LOC")
        elif agent_name == "Testing Agent":
            print(f"   Total Tests:    {output.get('total', 0)}")
            print(f"   Passed Tests:   {output.get('passed', 0)}")
            print(f"   Failed Tests:   {output.get('failed', 0)}")
            print(f"   Quality Gate:   {output.get('quality_gate', {}).get('status')}")
        elif agent_name == "Security Agent":
            print(f"   Secrets Found:  {output.get('secrets_found', 0)}")
            print(f"   Vulns Found:    {output.get('vulnerabilities', 0)}")
            print(f"   Checks Passed:  {', '.join(output.get('checks', []))}")

    # 5. Display Physical Workspace Files
    print_banner("PHYSICAL WORKSPACE ARTIFACTS")
    files_on_disk = [f["path"] for f in workspace.list_files() if not f["is_dir"]]
    print(f"Files physically created ({len(files_on_disk)} total):")
    for fpath in files_on_disk:
        size = len(workspace.read_file(fpath).encode("utf-8"))
        print(f"   - {fpath:<30} ({size:,} bytes)")

    # 6. Display Local Git Repository Log
    print_banner("SANDBOXED GIT VERSION CONTROL HISTORY")
    git_commits = result.get("git_commits", [])
    print(f"Local Git Commits ({len(git_commits)} recorded):")
    for c in git_commits:
        print(f"   commit {c.get('hash', '')[:8]} - {c.get('subject', '')} ({c.get('author', '')})")

    # 7. Display LLM Telemetry & Cost
    print_banner("LLM TELEMETRY & OBSERVABILITY")
    metrics = client.get_metrics()
    print(f"Total API Calls:      {metrics.get('requests_count', 0)}")
    print(f"Total Prompt Tokens:  {metrics.get('prompt_tokens', 0):,}")
    print(f"Total Output Tokens:  {metrics.get('completion_tokens', 0):,}")
    print(f"Combined Tokens:      {metrics.get('total_tokens', 0):,}")
    print(f"Total LLM Latency:    {metrics.get('total_latency_ms', 0):,.1f}ms")
    print(f"Estimated Cost:       ${metrics.get('estimated_cost_usd', 0.0):.6f} USD")

    # 8. Check Database Persistence
    print_banner("SQLITE DATABASE PERSISTENCE VERIFICATION")
    persisted_pipeline = await repo.get(mission_id)
    if persisted_pipeline:
        print(f"[OK] Pipeline record verified in SQLite: ID {mission_id}")
        print(f"     Status: {persisted_pipeline.get('status')}, Workflow State: {persisted_pipeline.get('workflow_state')}")
    else:
        print("[FAIL] Pipeline record not found in SQLite.")

    recent_failures = await repo.list_failure_memory(limit=5)
    print(f"[OK] Total Failure Memory Records in SQLite: {len(recent_failures)}")

    # 9. Final Scorecard
    print_banner("MISSION SCORECARD")
    all_stages_clean = all(s.get("status") in ("completed", "healed") for s in stages)
    print(f"1. Adaptive Planning:         {'PASSED' if any(s.get('agent') == 'Planning Agent' for s in stages) else 'FAILED'}")
    print(f"2. Physical Code Generation:   {'PASSED' if len(files_on_disk) >= 2 else 'FAILED'}")
    print(f"3. AST Syntax Compilation:     {'PASSED' if any(s.get('agent') == 'Build Agent' and s.get('status') == 'completed' for s in stages) else 'FAILED'}")
    print(f"4. Automated Test Verification:{'PASSED' if any(s.get('agent') == 'Testing Agent' and s.get('status') in ('completed', 'healed') for s in stages) else 'FAILED'}")
    print(f"5. Security Quality Gate:      {'PASSED' if any(s.get('agent') == 'Security Agent' and s.get('status') == 'completed' for s in stages) else 'FAILED'}")
    print(f"6. Local Git Checkpoints:      {'PASSED' if len(git_commits) >= 1 else 'FAILED'}")
    print(f"7. SQLite Telemetry & State:   {'PASSED' if persisted_pipeline else 'FAILED'}")
    print(f"8. Overall Mission Status:     {result.get('workflow_state')} (in {duration_total:.2f}s)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
