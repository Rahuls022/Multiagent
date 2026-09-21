"""Agent that simulates test execution and reports a quality signal."""

from typing import Any

from .base_agent import BaseAgent


class TestingAgent(BaseAgent):
    name = "Testing Agent"

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "total": 25,
            "passed": 25,
            "failed": 0,
            "coverage": 95,
            "message": "Tests passed.",
        }
