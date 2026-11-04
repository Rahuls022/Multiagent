"""Unit tests verifying full collaboration between Planning, Coding, Build, and Testing agents."""

import asyncio
import unittest

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.development_supervisor import DevelopmentSupervisor
from app.agents.planning_agent import PlanningAgent
from app.agents.testing_agent import TestingAgent
from app.database import InMemoryPipelineRepository


class TestCollaborativeDevSupervisor(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryPipelineRepository()

    def test_full_development_pipeline_collaboration(self):
        """Verify that Planning, Coding, Build, and Testing agents execute and exchange context."""
        from tests.test_real_agents import FakeLLMClient
        fake_llm = FakeLLMClient()
        dev_supervisor = DevelopmentSupervisor(
            pipeline=[PlanningAgent(client=fake_llm), CodingAgent(client=fake_llm), BuildAgent(), TestingAgent()],
            repository=self.repository,
        )
        mission = "Build a customer feedback portal"
        result = asyncio.run(dev_supervisor.run_pipeline(mission))

        # Overall pipeline assertions
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(len(result["stages"]), 4)

        stage_names = [s["agent"] for s in result["stages"]]
        self.assertEqual(stage_names, ["Planning Agent", "Coding Agent", "Build Agent", "Testing Agent"])

        # Stage 1: Planning Agent
        planning_stage = result["stages"][0]
        self.assertEqual(planning_stage["status"], "completed")
        self.assertIn("architecture", planning_stage["output"])
        self.assertIn("api_contract", planning_stage["output"])
        self.assertIn("acceptance_criteria", planning_stage["output"])

        # Stage 2: Coding Agent
        coding_stage = result["stages"][1]
        self.assertEqual(coding_stage["status"], "completed")
        files = coding_stage["output"]["files_to_create"]
        self.assertGreaterEqual(len(files), 3)

        # Stage 3: Build Agent (AST validation on Coding Agent's output)
        build_stage = result["stages"][2]
        self.assertEqual(build_stage["status"], "completed")
        self.assertTrue(build_stage["output"]["success"])
        self.assertIn("dockerfile", build_stage["output"])
        self.assertIn("syntax_checks", build_stage["output"])
        self.assertGreater(build_stage["output"]["total_loc"], 0)
        # All Python syntax checks must pass AST parsing
        for chk in build_stage["output"]["syntax_checks"]:
            if chk.get("language") == "python":
                self.assertTrue(chk["ast_valid"])

        # Stage 4: Testing Agent (verifies functional contracts)
        testing_stage = result["stages"][3]
        self.assertEqual(testing_stage["status"], "completed")
        self.assertTrue(testing_stage["output"]["success"])
        self.assertGreater(testing_stage["output"]["total"], 0)
        self.assertEqual(testing_stage["output"]["failed"], 0)
        self.assertGreaterEqual(testing_stage["output"]["coverage"], 85.0)
        self.assertEqual(testing_stage["output"]["quality_gate"]["status"], "PASSED")

        # Collaborative events verification
        event_names = [e["event"] for e in result["events"]]
        self.assertIn("PLAN_HANDOFF_TO_CODING", event_names)
        self.assertIn("CODE_SUBMITTED_TO_BUILD", event_names)
        self.assertIn("BUILD_ARTIFACTS_VALIDATED", event_names)
        self.assertIn("TEST_SUITE_EXECUTED", event_names)
        self.assertIn("PIPELINE_COMPLETED", event_names)


if __name__ == "__main__":
    unittest.main()
