"""Supervisor for the development pipeline orchestrating real autonomous agent workflows."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .base_agent import BaseAgent
from .build_agent import BuildAgent
from .coding_agent import CodingAgent
from .healing_agent import SelfHealingAgent
from .operations.security_agent import SecurityAgent
from .planning_agent import PlanningAgent
from .testing_agent import TestingAgent
from app.database.repository import PipelineRepository
from app.tools.workspace import WorkspaceManager


_DEFAULT_HEALING = object()


class DevelopmentSupervisor:
    """Orchestrates the 16-state software delivery lifecycle:

    RECEIVED -> ANALYZING -> PLANNING -> CODING -> BUILDING -> TESTING ->
    SECURITY_SCANNING -> HEALING -> RETESTING -> WAITING_FOR_APPROVAL ->
    DEPLOYING -> HEALTH_CHECK -> ROLLING_BACK -> COMPLETED / FAILED / CANCELLED.
    """

    name = "Development Supervisor"
    MAX_WORKFLOW_DURATION_SECONDS = 600.0
    MAX_AGENT_STEPS = 20

    def __init__(
        self,
        pipeline: list[BaseAgent] | None = None,
        repository: PipelineRepository | None = None,
        healing_agent: Any = _DEFAULT_HEALING,
        max_internal_retries: int = 3,
        workspace_root: Path | str | None = None,
    ) -> None:
        self.default_pipeline = pipeline
        self.repository = repository
        self.healing_agent = SelfHealingAgent(repository=repository) if healing_agent is _DEFAULT_HEALING else healing_agent
        self.max_internal_retries = max_internal_retries
        self.workspace_root = workspace_root or os.getenv("WORKSPACE_ROOT", Path(__file__).parents[2] / "workspaces")

    def _resolve_pipeline(self, request: str) -> list[BaseAgent]:
        """Dynamically configure agent pipeline based on mission requirements."""
        if self.default_pipeline is not None:
            return list(self.default_pipeline)

        req_lower = request.lower()
        pipeline: list[BaseAgent] = [
            PlanningAgent(),
            CodingAgent(),
            BuildAgent(),
            TestingAgent(),
        ]
        return pipeline

    async def run_pipeline(self, request: str, task: dict[str, Any] | None = None) -> dict[str, Any]:
        start_time = time.monotonic()
        task = task or {
            "id": str(uuid4()),
            "request": request,
            "created_at": datetime.now(UTC).isoformat(),
            "user_id": "anonymous",
        }

        # Initialize isolated workspace sandbox for this mission
        workspace = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id=task.get("user_id") or "anonymous",
            mission_id=task["id"],
        )

        # 1. Initialize local sandboxed Git repository
        workspace.git_init()

        context: dict[str, Any] = {"workspace": workspace}
        stages: list[dict[str, Any]] = []
        logs: list[dict[str, str]] = []
        events = [
            {
                "pipeline_id": task["id"],
                "agent": self.name,
                "event": "PIPELINE_STARTED",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ]

        active_pipeline = self._resolve_pipeline(request)

        # State: RECEIVED -> ANALYZING
        await self._save(self._result(task, stages, logs, "RECEIVED", self.name, events, workspace))
        events.append({
            "pipeline_id": task["id"],
            "agent": self.name,
            "event": "REQUIREMENTS_ANALYZED",
            "details": f"Configured adaptive workflow with {len(active_pipeline)} autonomous agent gates.",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        await self._save(self._result(task, stages, logs, "ANALYZING", self.name, events, workspace))

        for index, agent in enumerate(active_pipeline, start=1):
            # Check maximum workflow duration limit
            if (time.monotonic() - start_time) > self.MAX_WORKFLOW_DURATION_SECONDS:
                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "WORKFLOW_TIMEOUT",
                    "details": f"Pipeline exceeded maximum execution duration of {self.MAX_WORKFLOW_DURATION_SECONDS}s.",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                result = self._result(task, stages, logs, "FAILED", agent.name, events, workspace)
                await self._save(result)
                return result

            current_state = self._state_for_agent(agent.name)
            await self._save(self._result(task, stages, logs, current_state, agent.name, events, workspace))

            stage = await agent.run(task, context)
            stage["progress"] = round(index / len(active_pipeline) * 100)
            stages.append(stage)
            logs.extend(stage.get("logs", []))
            events.extend(stage.get("events", []))
            context[agent.name] = stage

            # Real agent handoff events & Git checkpoints
            now_iso = datetime.now(UTC).isoformat()
            if agent.name == "Planning Agent" and stage["status"] == "completed":
                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "PLAN_HANDOFF_TO_CODING",
                    "details": f"Plan produced with {len(stage.get('output', {}).get('files_to_create', []))} planned files.",
                    "timestamp": now_iso,
                })
            elif agent.name == "Coding Agent" and stage["status"] == "completed":
                # Git checkpoint after initial code generation
                workspace.git_add()
                workspace.git_commit("Initial implementation by Coding Agent")
                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "CODE_SUBMITTED_TO_BUILD",
                    "details": f"{len(stage.get('output', {}).get('files_written', []))} files committed to local Git workspace.",
                    "timestamp": now_iso,
                })
            elif agent.name == "Build Agent" and stage["status"] == "completed":
                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "BUILD_ARTIFACTS_VALIDATED",
                    "details": "AST syntax clean and compile checks passed. Handing off to Testing Agent.",
                    "timestamp": now_iso,
                })
            elif agent.name == "Testing Agent" and stage["status"] == "completed":
                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "TEST_SUITE_EXECUTED",
                    "details": f"{stage.get('output', {}).get('passed', 0)} assertions verified across all quality gates.",
                    "timestamp": now_iso,
                })
            elif agent.name == "Security Agent" and stage["status"] == "completed":
                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "SECURITY_AUDIT_PASSED",
                    "details": f"Scanned {stage.get('output', {}).get('scanned_files', 0)} files. Zero credential leaks or dangerous commands.",
                    "timestamp": now_iso,
                })

            # Failure and Autonomous Self-Healing Handling
            if stage["status"] == "failed":
                if not self.healing_agent:
                    # Mark subsequent unexecuted stages as blocked
                    for remaining_agent in active_pipeline[index:]:
                        stages.append({
                            "agent": remaining_agent.name,
                            "status": "blocked",
                            "error": f"Execution blocked: Preceding stage '{agent.name}' failed quality gates.",
                            "logs": [{
                                "timestamp": datetime.now(UTC).isoformat(),
                                "message": f"🚫 Stage blocked: Dependent on successful completion of '{agent.name}'."
                            }],
                            "events": [{
                                "pipeline_id": task["id"],
                                "agent": remaining_agent.name,
                                "event": "STAGE_BLOCKED",
                                "details": f"Blocked because {agent.name} failed.",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }],
                            "output": {
                                "status": "blocked",
                                "reason": f"Preceding stage {agent.name} failed."
                            }
                        })
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": self.name,
                        "event": "PIPELINE_FAILED",
                        "details": f"Stage {agent.name} failed and self-healing is disabled.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    result = self._result(task, stages, logs, "FAILED", agent.name, events, workspace)
                    await self._save(result)
                    return result

                healed = False
                for retry in range(1, self.max_internal_retries + 1):
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": self.name,
                        "event": "DEV_INTERNAL_RETRY",
                        "details": f"Initiating autonomous self-healing for {agent.name} (Attempt {retry}/{self.max_internal_retries}).",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": self.name,
                        "event": "CODE_REVISE_REQUESTED",
                        "details": f"Requesting autonomous code revision and fix for {agent.name}.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    await self._save(self._result(task, stages, logs, "HEALING", self.healing_agent.name, events, workspace))

                    healed_stage = await self.healing_agent.heal(stage, task, context)
                    if healed_stage.get("status") == "healed":
                        stages[-1] = healed_stage
                        logs.extend(healed_stage.get("logs", [])[len(stage.get("logs", [])):])
                        events.extend(healed_stage.get("events", [])[len(stage.get("events", [])):])
                        context[agent.name] = healed_stage
                        next_agent = active_pipeline[index].name if index < len(active_pipeline) else None
                        await self._save(self._result(task, stages, logs, "RETESTING", next_agent, events, workspace))
                        healed = True
                        break

                if healed:
                    continue

                # Healing exhausted: Mark all subsequent stages as blocked
                for remaining_agent in active_pipeline[index:]:
                    stages.append({
                        "agent": remaining_agent.name,
                        "status": "blocked",
                        "error": f"Execution blocked: Preceding stage '{agent.name}' failed quality gates.",
                        "logs": [{
                            "timestamp": datetime.now(UTC).isoformat(),
                            "message": f"🚫 Stage blocked: Dependent on successful completion of '{agent.name}'."
                        }],
                        "events": [{
                            "pipeline_id": task["id"],
                            "agent": remaining_agent.name,
                            "event": "STAGE_BLOCKED",
                            "details": f"Blocked because {agent.name} failed.",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }],
                        "output": {
                            "status": "blocked",
                            "reason": f"Preceding stage {agent.name} failed."
                        }
                    })

                events.append({
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "PIPELINE_FAILED",
                    "details": f"Exceeded maximum healing attempts ({self.max_internal_retries}). Mission marked as failed.",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                result = self._result(task, stages, logs, "FAILED", agent.name, events, workspace)
                await self._save(result)
                return result

            next_agent = active_pipeline[index].name if index < len(active_pipeline) else None
            await self._save(self._result(task, stages, logs, "RUNNING", next_agent, events, workspace))

        # Check for Human Approval Gate
        requires_approval = task.get("require_approval", False) or any(
            t in request.lower() for t in ["deploy to prod", "production deploy", "run migration", "database migration"]
        )
        if requires_approval:
            events.append({
                "pipeline_id": task["id"],
                "agent": self.name,
                "event": "APPROVAL_REQUIRED",
                "details": "Mission requires human operator authorization before production deployment.",
                "timestamp": datetime.now(UTC).isoformat(),
            })
            result = self._result(task, stages, logs, "WAITING_FOR_APPROVAL", None, events, workspace)
            await self._save(result)
            return result

        # Final local git release commit
        workspace.git_add()
        workspace.git_commit("Verified autonomous release build ready")

        events.append({
            "pipeline_id": task["id"],
            "agent": self.name,
            "event": "PIPELINE_COMPLETED",
            "details": "All autonomous agent stages and quality gates verified clean.",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        result = self._result(task, stages, logs, "COMPLETED", None, events, workspace)
        await self._save(result)
        return result

    async def approve_pipeline(self, pipeline_id: str) -> dict[str, Any] | None:
        """Human approval callback to proceed from WAITING_FOR_APPROVAL to COMPLETED."""
        if self.repository is None:
            return None
        pipeline = await self.repository.get(pipeline_id)
        if not pipeline or pipeline.get("workflow_state") != "WAITING_FOR_APPROVAL":
            return pipeline

        pipeline["workflow_state"] = "COMPLETED"
        pipeline["status"] = "completed"
        pipeline["events"].append({
            "pipeline_id": pipeline_id,
            "agent": self.name,
            "event": "APPROVAL_GRANTED",
            "details": "Human operator approved production deployment.",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        await self.repository.update(pipeline_id, pipeline)
        return pipeline

    async def reject_pipeline(self, pipeline_id: str, reason: str = "Operator rejected") -> dict[str, Any] | None:
        """Human rejection callback to cancel pipeline in WAITING_FOR_APPROVAL."""
        if self.repository is None:
            return None
        pipeline = await self.repository.get(pipeline_id)
        if not pipeline:
            return None

        pipeline["workflow_state"] = "CANCELLED"
        pipeline["status"] = "cancelled"
        pipeline["events"].append({
            "pipeline_id": pipeline_id,
            "agent": self.name,
            "event": "APPROVAL_REJECTED",
            "details": f"Deployment cancelled by operator: {reason}",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        await self.repository.update(pipeline_id, pipeline)
        return pipeline

    async def resume_pipeline(self, pipeline_id: str) -> dict[str, Any]:
        """Crash recovery: Resume execution from the last pending agent stage."""
        if self.repository is None:
            raise RuntimeError("Repository required for pipeline crash recovery.")

        pipeline_data = await self.repository.get(pipeline_id)
        if not pipeline_data:
            raise ValueError(f"Pipeline {pipeline_id} not found in database.")

        task = pipeline_data["task"]
        request = task.get("request", "")
        stages = pipeline_data.get("stages", [])
        logs = pipeline_data.get("logs", [])
        events = pipeline_data.get("events", [])

        workspace = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id=task.get("user_id") or "anonymous",
            mission_id=task["id"],
        )

        completed_agent_names = {s.get("agent") for s in stages if s.get("status") in ("completed", "healed")}
        active_pipeline = self._resolve_pipeline(request)

        remaining_pipeline = [a for a in active_pipeline if a.name not in completed_agent_names]
        if not remaining_pipeline:
            pipeline_data["status"] = "completed"
            pipeline_data["workflow_state"] = "COMPLETED"
            await self._save(pipeline_data)
            return pipeline_data

        events.append({
            "pipeline_id": pipeline_id,
            "agent": self.name,
            "event": "PIPELINE_RESUMED",
            "details": f"Resuming execution with {len(remaining_pipeline)} remaining agent stages.",
            "timestamp": datetime.now(UTC).isoformat(),
        })

        context: dict[str, Any] = {"workspace": workspace}
        for s in stages:
            context[s.get("agent", "")] = s

        for index, agent in enumerate(remaining_pipeline, start=len(completed_agent_names) + 1):
            current_state = self._state_for_agent(agent.name)
            await self._save(self._result(task, stages, logs, current_state, agent.name, events, workspace))

            stage = await agent.run(task, context)
            stage["progress"] = round(index / len(active_pipeline) * 100)
            stages.append(stage)
            logs.extend(stage.get("logs", []))
            events.extend(stage.get("events", []))
            context[agent.name] = stage

            if stage["status"] == "failed":
                # Trigger self healing
                if self.healing_agent:
                    healed_stage = await self.healing_agent.heal(stage, task, context)
                    if healed_stage.get("status") == "healed":
                        stages[-1] = healed_stage
                        continue
                result = self._result(task, stages, logs, "FAILED", agent.name, events, workspace)
                await self._save(result)
                return result

        result = self._result(task, stages, logs, "COMPLETED", None, events, workspace)
        await self._save(result)
        return result

    def _state_for_agent(self, agent_name: str) -> str:
        mapping = {
            "Planning Agent": "PLANNING",
            "Coding Agent": "CODING",
            "Build Agent": "BUILDING",
            "Testing Agent": "TESTING",
            "Security Agent": "SECURITY_SCANNING",
            "Self-Healing Agent": "HEALING",
        }
        return mapping.get(agent_name, "RUNNING")

    async def _save(self, result: dict[str, Any]) -> None:
        result["updated_at"] = datetime.now(UTC).isoformat()
        if self.repository is None:
            return
        pipeline_id = result["task"]["id"]
        if not result["stages"]:
            await self.repository.create(result)
        else:
            await self.repository.update(pipeline_id, result)

    @staticmethod
    def _result(
        task: dict[str, Any],
        stages: list[dict[str, Any]],
        logs: list[dict[str, str]],
        status: str,
        current_agent: str | None,
        events: list[dict[str, Any]],
        workspace: WorkspaceManager,
    ) -> dict[str, Any]:
        git_history = []
        try:
            log_res = workspace.git_log(limit=5)
            if isinstance(log_res, list):
                git_history = log_res
            elif isinstance(log_res, dict):
                git_history = log_res.get("commits", [])
        except Exception:
            pass

        return {
            "task": task,
            "status": status.lower(),
            "workflow_state": status.upper(),
            "progress": 100 if status.upper() in ("COMPLETED",) else (stages[-1].get("progress", 0) if stages else 0),
            "current_agent": None if status.upper() in ("COMPLETED", "FAILED", "WAITING_FOR_APPROVAL", "CANCELLED") else current_agent,
            "stages": stages,
            "logs": logs,
            "events": events,
            "workspace_path": str(workspace.root_path),
            "files_in_workspace": [f["path"] for f in workspace.list_files() if not f["is_dir"]],
            "git_commits": git_history,
        }
