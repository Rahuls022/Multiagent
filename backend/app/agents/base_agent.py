"""Common lifecycle and result contract for every swarm agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from time import perf_counter
from typing import Any


class BaseAgent(ABC):
    """Base class that makes specialised agents observable and consistent."""

    name: str = "Base Agent"

    async def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute, validate, and wrap work in a consistent stage result."""
        started_at = datetime.now(UTC)
        timer = perf_counter()
        logs = [self._log("started")]

        try:
            output = await self.execute(task, context)
            is_valid, validation_message = self.validate(output)
            if not is_valid:
                raise ValueError(validation_message)
            logs.append(self._log("completed"))
            status = "completed"
            error = None
        except Exception as exc:  # Keeps pipeline failures visible to the supervisor.
            output = {}
            logs.append(self._log("failed", str(exc)))
            status = "failed"
            error = str(exc)

        finished_at = datetime.now(UTC)
        duration_ms = round((perf_counter() - timer) * 1000, 2)
        return {
            "agent": self.name,
            "status": status,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_ms": duration_ms,
            "logs": logs,
            "output": output,
            "error": error,
            "events": [
                {"pipeline_id": task["id"], "agent": self.name, "event": "AGENT_STARTED", "timestamp": started_at.isoformat()},
                {
                    "pipeline_id": task["id"],
                    "agent": self.name,
                    "event": "AGENT_COMPLETED" if status == "completed" else "AGENT_FAILED",
                    "timestamp": finished_at.isoformat(),
                    "duration_ms": duration_ms,
                },
            ],
        }

    @abstractmethod
    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Perform this agent's one specialised responsibility."""

    def validate(self, output: dict[str, Any]) -> tuple[bool, str]:
        """Validate an agent result before the supervisor continues."""
        return bool(output), "Agent returned no output"

    def _log(self, event: str, detail: str | None = None) -> dict[str, str]:
        message = f"{self.name} {event}"
        if detail:
            message = f"{message}: {detail}"
        return {"timestamp": datetime.now(UTC).isoformat(), "message": message}
