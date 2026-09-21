import asyncio
import unittest

from app.agents import GlobalOrchestrator
from app.agents.base_agent import BaseAgent
from app.agents.development_supervisor import DevelopmentSupervisor
from app.database import InMemoryPipelineRepository


class Sprint3PipelineTests(unittest.TestCase):
    def test_full_swarm_completes_in_development_then_operations_order(self):
        repository = InMemoryPipelineRepository()
        result = asyncio.run(GlobalOrchestrator(repository=repository).run_pipeline("Build an observable portal"))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(
            [stage["agent"] for stage in result["stages"]],
            ["Planning Agent", "Coding Agent", "Build Agent", "Testing Agent", "Security Agent", "Release Agent", "Deploy Agent", "Monitor Agent"],
        )
        self.assertEqual(result["teams"]["operations"]["status"], "completed")
        self.assertEqual(result["observer"]["agents_monitored"], 8)
        self.assertEqual(result["observer"]["failures_detected"], 0)
        self.assertIn("PIPELINE_COMPLETED", [event["event"] for event in result["events"]])
        saved = asyncio.run(repository.get(result["task"]["id"]))
        self.assertEqual(saved["status"], "completed")

    def test_failure_is_observed_and_operations_is_not_started(self):
        class FailingAgent(BaseAgent):
            name = "Build Agent"

            async def execute(self, task, context):
                raise RuntimeError("Build artifact could not be created")

        result = asyncio.run(
            GlobalOrchestrator(
                development_supervisor=DevelopmentSupervisor(pipeline=[FailingAgent()], healing_agent=None)
            ).run_pipeline("Build a failing portal")
        )


        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["observer"]["failures_detected"], 1)
        self.assertEqual(result["observer"]["failed_agents"], ["Build Agent"])
        self.assertNotIn("operations", result["teams"])
