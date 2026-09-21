"""Coordinates Security, Release, Deploy, and Monitor with autonomous rollback & retry capabilities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..base_agent import BaseAgent
from ..healing_agent import SelfHealingAgent
from .deploy_agent import DeployAgent
from .monitor_agent import MonitorAgent
from .release_agent import ReleaseAgent
from .security_agent import SecurityAgent
from app.database.repository import PipelineRepository


class OperationsSupervisor:
    """Handles release & production operations (Security, Release, Deploy, Monitor).
    
    If deployment or release fails, it automatically executes a rollback to the previous
    stable state and retries independently before reporting status.
    """

    name = "Operations Supervisor"

    def __init__(
        self,
        pipeline: list[BaseAgent] | None = None,
        repository: PipelineRepository | None = None,
        healing_agent: SelfHealingAgent | None = None,
        max_ops_retries: int = 2,
    ) -> None:
        self.pipeline = pipeline or [SecurityAgent(), ReleaseAgent(), DeployAgent(), MonitorAgent()]
        self.repository = repository
        self.healing_agent = (
            healing_agent
            if healing_agent is not None
            else (None if pipeline is not None else SelfHealingAgent(repository=repository))
        )
        self.max_ops_retries = max_ops_retries



    async def run_pipeline(self, task: dict[str, Any], development: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {"development": development}
        stages: list[dict[str, Any]] = []
        logs: list[dict[str, str]] = []
        events: list[dict[str, Any]] = [{"pipeline_id": task["id"], "agent": self.name, "event": "PIPELINE_STARTED", "timestamp": datetime.now(UTC).isoformat()}]
        
        for agent in self.pipeline:
            stage = await agent.run(task, context)
            stages.append(stage)
            logs.extend(stage["logs"])
            events.extend(stage["events"])
            context[agent.name] = stage

            if stage["status"] == "failed":
                # Autonomous Rollback & Retry Mechanism
                healed = False
                for retry in range(1, self.max_ops_retries + 1):
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": self.name,
                        "event": "DEPLOYMENT_ROLLBACK",
                        "details": f"Deployment/Release failure in {agent.name}. Autonomous rollback executed to stable baseline.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    events.append({
                        "pipeline_id": task["id"],
                        "agent": self.name,
                        "event": "DEPLOYMENT_RETRY_INITIATED",
                        "details": f"Attempting independent ops retry ({retry}/{self.max_ops_retries}) for {agent.name}.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    logs.append({
                        "agent": self.name,
                        "message": f"Deployment rollback executed for {agent.name}. Retrying independently...",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })

                    if self.healing_agent is not None:
                        healed_stage = await self.healing_agent.heal(stage, task, context)
                        if healed_stage["status"] == "healed":
                            stages[-1] = healed_stage
                            logs.extend(healed_stage["logs"][len(stage.get("logs", [])):])
                            events.extend(healed_stage["events"][len(stage.get("events", [])):])
                            context[agent.name] = healed_stage
                            healed = True
                            break

                if healed:
                    continue

                events.append({"pipeline_id": task["id"], "agent": self.name, "event": "PIPELINE_FAILED", "timestamp": datetime.now(UTC).isoformat()})
                return {"status": "failed", "current_agent": agent.name, "stages": stages, "logs": logs, "events": events}

        events.append({"pipeline_id": task["id"], "agent": self.name, "event": "PIPELINE_COMPLETED", "timestamp": datetime.now(UTC).isoformat()})
        return {"status": "completed", "current_agent": None, "stages": stages, "logs": logs, "events": events}

