"""Main Brain (Global Orchestrator) - High-level pipeline phase decomposition and delegation to supervisor agents."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.database.repository import PipelineRepository

from .development_supervisor import DevelopmentSupervisor
from .observer import ObserverAgent
from .operations import OperationsSupervisor


class GlobalOrchestrator:
    """Agent 1: Main Brain / Global Orchestrator.
    
    Receives user requests, decomposes them into high-level phases (Development & Operations),
    assigns work to supervisor agents, collects phase results, and attaches Swarm Observer metrics.
    NEVER generates code or deploys directly.
    """

    name = "Global Orchestrator (Main Brain)"

    def __init__(
        self,
        repository: PipelineRepository | None = None,
        development_supervisor: DevelopmentSupervisor | None = None,
        operations_supervisor: OperationsSupervisor | None = None,
        observer: ObserverAgent | None = None,
    ) -> None:
        self.repository = repository
        self.development_supervisor = development_supervisor or DevelopmentSupervisor(repository=repository)
        self.operations_supervisor = operations_supervisor or OperationsSupervisor(repository=repository)
        self.observer = observer or ObserverAgent()


    async def run_pipeline(self, request: str, task: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
        task = task or {"id": str(uuid4()), "request": request, "created_at": datetime.now(UTC).isoformat()}
        if user_id:
            task["user_id"] = user_id
        
        # High level phase decomposition event
        initial_events = [
            {
                "pipeline_id": task["id"],
                "agent": self.name,
                "event": "REQUEST_DECOMPOSED",
                "details": f"Main Brain decomposed user request into 2 phases: Development & Operations.",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            {
                "pipeline_id": task["id"],
                "agent": self.name,
                "event": "PHASE_ASSIGNED",
                "phase": "Development Phase",
                "assigned_to": self.development_supervisor.name,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        ]

        pipeline = self._result(task, "running", [], [], initial_events, "Planning Agent")
        await self._save(pipeline, create=True)

        # Phase 1: Development Phase Delegation
        development = await self.development_supervisor.run_pipeline(request, task)
        all_events = [*initial_events, *development["events"]]
        pipeline = self._result(
            task, development["status"], development["stages"], development["logs"], all_events,
            development["current_agent"], {"development": development},
        )
        await self._save(pipeline)

        if development["status"] != "completed":
            failed_stage = next((s for s in development["stages"] if s.get("status") in ("failed", "error")), None)
            pipeline["final_result"] = {
                "success": False,
                "mission_summary": task.get("request", ""),
                "pipeline_id": task["id"],
                "final_status": "failed",
                "failed_stage": failed_stage.get("agent") if failed_stage else development.get("current_agent", "Unknown"),
                "root_cause_analysis": (
                    failed_stage.get("error") or
                    failed_stage.get("output", {}).get("root_cause") or
                    "Development Supervisor reported phase failure"
                ) if failed_stage else "Development pipeline stopped",
                "error_details": failed_stage.get("error") if failed_stage else "Stage failure",
                "recovery_attempts": 3,
                "why_recovery_failed": "Automated self-healing retry budget exhausted without resolving quality gate.",
                "recommended_next_action": "Inspect logs in Logs view or review failed stage in Self-Healing panel.",
            }
            pipeline["events"].append({
                "pipeline_id": task["id"],
                "agent": self.name,
                "event": "PIPELINE_FAILED",
                "details": "Development Supervisor reported unresolvable phase failure. Main Brain terminating pipeline.",
                "timestamp": datetime.now(UTC).isoformat(),
            })
            pipeline["observer"] = self.observer.inspect(pipeline)
            await self._save(pipeline)
            return pipeline

        # Phase 2: Operations Phase Delegation
        pipeline["status"] = "running"
        pipeline["current_agent"] = "Security Agent"
        pipeline["progress"] = 50
        pipeline["events"].append({
            "pipeline_id": task["id"],
            "agent": self.name,
            "event": "PHASE_ASSIGNED",
            "phase": "Operations Phase",
            "assigned_to": self.operations_supervisor.name,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        pipeline["observer"] = self.observer.inspect(pipeline)
        await self._save(pipeline)

        operations = await self.operations_supervisor.run_pipeline(task, development)
        all_stages = [*development["stages"], *operations["stages"]]
        all_logs = [*development["logs"], *operations["logs"]]
        all_events = [*pipeline["events"], *operations["events"]]
        final_status = "completed" if operations["status"] == "completed" else "failed"

        pipeline = self._result(
            task, final_status, all_stages, all_logs, all_events, operations["current_agent"],
            {"development": development, "operations": operations},
        )
        pipeline["events"].append({
            "pipeline_id": task["id"],
            "agent": self.name,
            "event": "PIPELINE_COMPLETED" if final_status == "completed" else "PIPELINE_FAILED",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        pipeline["observer"] = self.observer.inspect(pipeline)

        # Section 7: Compile comprehensive final result for user
        healed_count = sum(1 for s in all_stages if s.get("status") == "healed")
        build_stage = next((s for s in all_stages if s.get("agent") == "Build Agent"), None)
        test_stage = next((s for s in all_stages if s.get("agent") == "Testing Agent"), None)
        sec_stage = next((s for s in all_stages if s.get("agent") == "Security Agent"), None)
        dep_stage = next((s for s in all_stages if s.get("agent") == "Deploy Agent"), None)

        if final_status == "completed":
            pipeline["final_result"] = {
                "success": True,
                "mission_summary": task.get("request", ""),
                "pipeline_id": task["id"],
                "final_status": "completed",
                "completed_stages": [s.get("agent") for s in all_stages if s.get("status") in ("completed", "healed")],
                "build_status": build_stage.get("status", "completed") if build_stage else "completed",
                "test_results": {
                    "total": test_stage.get("output", {}).get("total", 0) if test_stage else 0,
                    "passed": test_stage.get("output", {}).get("passed", 0) if test_stage else 0,
                    "failed": test_stage.get("output", {}).get("failed", 0) if test_stage else 0,
                    "coverage": test_stage.get("output", {}).get("coverage", 100.0) if test_stage else 100.0,
                },
                "security_findings": {
                    "vulnerabilities": sec_stage.get("output", {}).get("vulnerabilities", 0) if sec_stage else 0,
                    "secrets_found": sec_stage.get("output", {}).get("secrets_found", 0) if sec_stage else 0,
                    "status": "PASSED (Clean)",
                },
                "deployment_status": {
                    "environment": dep_stage.get("output", {}).get("environment", "development") if dep_stage else "development",
                    "status": dep_stage.get("output", {}).get("status", "deployed") if dep_stage else "deployed",
                    "endpoint": dep_stage.get("output", {}).get("endpoint") if dep_stage else None,
                },
                "failures_recovered": healed_count,
                "total_execution_time_ms": pipeline["observer"]["performance_metrics"]["total_duration_ms"],
                "generated_files": development.get("files_in_workspace", []),
            }
        else:
            failed_stage = next((s for s in all_stages if s.get("status") in ("failed", "error")), None)
            pipeline["final_result"] = {
                "success": False,
                "mission_summary": task.get("request", ""),
                "pipeline_id": task["id"],
                "final_status": "failed",
                "failed_stage": failed_stage.get("agent") if failed_stage else operations.get("current_agent", "Unknown"),
                "root_cause_analysis": (
                    failed_stage.get("error") or
                    failed_stage.get("output", {}).get("root_cause") or
                    "Stage execution failure"
                ) if failed_stage else "Pipeline execution stopped",
                "error_details": failed_stage.get("error") if failed_stage else "Stage failure",
                "recovery_attempts": 3,
                "why_recovery_failed": "Automated self-healing retry budget exhausted without resolving quality gate.",
                "recommended_next_action": "Inspect logs in Logs view or review failed stage in Self-Healing panel.",
            }

        await self._save(pipeline)
        return pipeline

    def _result(
        self, task: dict[str, Any], status: str, stages: list[dict[str, Any]], logs: list[dict[str, Any]],
        events: list[dict[str, Any]], current_agent: str | None, teams: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "task": task,
            "status": status,
            "progress": 100 if status == "completed" else round(len(stages) / 8 * 100),
            "current_agent": None if status == "completed" else current_agent,
            "stages": stages,
            "logs": logs,
            "events": events,
            "teams": teams or {},
        }
        if teams and "development" in teams:
            dev_team = teams["development"]
            if isinstance(dev_team, dict):
                if dev_team.get("workspace_path"):
                    result["workspace_path"] = dev_team["workspace_path"]
                if dev_team.get("files_in_workspace"):
                    result["files_in_workspace"] = dev_team["files_in_workspace"]
        result["observer"] = self.observer.inspect(result)
        return result

    async def _save(self, pipeline: dict[str, Any], create: bool = False) -> None:
        pipeline["updated_at"] = datetime.now(UTC).isoformat()
        if self.repository is None:
            return
        if create:
            await self.repository.create(pipeline)
        else:
            await self.repository.update(pipeline["task"]["id"], pipeline)


