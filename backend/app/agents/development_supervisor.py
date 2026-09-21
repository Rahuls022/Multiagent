"""Supervisor for the development pipeline with autonomous internal feedback loops and self-healing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .base_agent import BaseAgent
from .build_agent import BuildAgent
from .coding_agent import CodingAgent
from .healing_agent import SelfHealingAgent
from .planning_agent import PlanningAgent
from .testing_agent import TestingAgent
from app.database.repository import PipelineRepository


class DevelopmentSupervisor:
    """Manages software creation lifecycle (Planning, Coding, Build, Testing).
    
    If Build Agent or Testing Agent fails, it handles internal retries by routing
    the issue back to Coding Agent / SelfHealing without involving Global Orchestration.
    """

    name = "Development Supervisor"

    def __init__(
        self,
        pipeline: list[BaseAgent] | None = None,
        repository: PipelineRepository | None = None,
        healing_agent: SelfHealingAgent | None = None,
        max_internal_retries: int = 2,
    ) -> None:
        self.pipeline = pipeline or [PlanningAgent(), CodingAgent(), BuildAgent(), TestingAgent()]
        self.repository = repository
        self.healing_agent = (
            healing_agent
            if healing_agent is not None
            else (None if pipeline is not None else SelfHealingAgent(repository=repository))
        )
        self.max_internal_retries = max_internal_retries



    async def run_pipeline(self, request: str, task: dict[str, Any] | None = None) -> dict[str, Any]:
        task = task or {"id": str(uuid4()), "request": request, "created_at": datetime.now(UTC).isoformat()}
        context: dict[str, Any] = {}
        stages: list[dict[str, Any]] = []
        logs: list[dict[str, str]] = []
        events = [{"pipeline_id": task["id"], "agent": self.name, "event": "PIPELINE_STARTED", "timestamp": datetime.now(UTC).isoformat()}]
        await self._save(self._result(task, stages, logs, "running", self.pipeline[0].name, events))

        for index, agent in enumerate(self.pipeline, start=1):
            stage = await agent.run(task, context)
            stage["progress"] = round(index / len(self.pipeline) * 100)
            stages.append(stage)
            logs.extend(stage["logs"])
            events.extend(stage["events"])
            context[agent.name] = stage

            if stage["status"] == "failed":
                # Internal Feedback Loop: Route build/test failure back to Coding Agent / Healing Agent internally
                healed = False
                for retry in range(1, self.max_internal_retries + 1):
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": self.name,
                        "event": "DEV_INTERNAL_RETRY",
                        "details": f"Routing failure in {agent.name} back to Coding Agent / Self Healing (Attempt {retry}/{self.max_internal_retries}) without escalating to Global Orchestrator.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": "Coding Agent",
                        "event": "CODE_REVISE_REQUESTED",
                        "details": f"Analyzing failure logs from {agent.name} and generating patch.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    logs.append({
                        "agent": self.name,
                        "message": f"Internal feedback loop triggered: Routing {agent.name} issue back to Coding Agent.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })

                    if self.healing_agent is not None:
                        healed_stage = await self.healing_agent.heal(stage, task, context)
                        if healed_stage["status"] == "healed":
                            stages[-1] = healed_stage
                            logs.extend(healed_stage["logs"][len(stage.get("logs", [])):])
                            events.extend(healed_stage["events"][len(stage.get("events", [])):])
                            context[agent.name] = healed_stage
                            next_agent = self.pipeline[index].name if index < len(self.pipeline) else None
                            await self._save(self._result(task, stages, logs, "running", next_agent, events))
                            healed = True
                            break

                if healed:
                    continue

                events.append({"pipeline_id": task["id"], "agent": self.name, "event": "PIPELINE_FAILED", "timestamp": datetime.now(UTC).isoformat()})
                result = self._result(task, stages, logs, "failed", agent.name, events)
                await self._save(result)
                return result

            next_agent = self.pipeline[index].name if index < len(self.pipeline) else None
            await self._save(self._result(task, stages, logs, "running", next_agent, events))

        events.append({"pipeline_id": task["id"], "agent": self.name, "event": "PIPELINE_COMPLETED", "timestamp": datetime.now(UTC).isoformat()})
        result = self._result(task, stages, logs, "completed", None, events)
        await self._save(result)
        return result

    async def _save(self, result: dict[str, Any]) -> None:
        """Persist after every state transition so the observer can inspect progress."""
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
        task: dict[str, Any], stages: list[dict[str, Any]], logs: list[dict[str, str]], status: str, failed_agent: str | None,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "task": task,
            "status": status,
            "progress": 100 if status == "completed" else (stages[-1]["progress"] if stages else 0),
            "current_agent": None if status == "completed" else failed_agent,
            "stages": stages,
            "logs": logs,
            "events": events,
        }

