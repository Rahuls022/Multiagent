import asyncio
import sys
import unittest
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.agents import GlobalOrchestrator
from app.agents.base_agent import BaseAgent
from app.agents.development_supervisor import DevelopmentSupervisor
from app.database import InMemoryPipelineRepository


class Sprint3PipelineTests(unittest.TestCase):
    def test_full_swarm_completes_in_development_then_operations_order(self):
        repository = InMemoryPipelineRepository()
        from app.agents.planning_agent import PlanningAgent
        from app.agents.coding_agent import CodingAgent
        from app.agents.build_agent import BuildAgent
        from app.agents.testing_agent import TestingAgent
        from tests.test_real_agents import FakeLLMClient

        fake_llm = FakeLLMClient()
        dev_supervisor = DevelopmentSupervisor(
            pipeline=[PlanningAgent(client=fake_llm), CodingAgent(client=fake_llm), BuildAgent(), TestingAgent()],
            repository=repository,
        )
        orchestrator = GlobalOrchestrator(repository=repository, development_supervisor=dev_supervisor)
        result = asyncio.run(orchestrator.run_pipeline("Build an observable portal"))

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
        self.assertIsNotNone(saved)
        assert saved is not None
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


if __name__ == "__main__":
    unittest.main()
