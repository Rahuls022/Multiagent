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
        self.development_supervisor = development_supervisor or DevelopmentSupervisor()
        self.operations_supervisor = operations_supervisor or OperationsSupervisor()
        self.observer = observer or ObserverAgent()

    async def run_pipeline(self, request: str) -> dict[str, Any]:
        task = {"id": str(uuid4()), "request": request, "created_at": datetime.now(UTC).isoformat()}
        
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

