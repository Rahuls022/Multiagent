"""End-to-end tests for the complete autonomous multi-agent workflow and intentional failure test."""

import asyncio
import tempfile
import unittest

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.development_supervisor import DevelopmentSupervisor
from app.agents.healing_agent import SelfHealingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.testing_agent import TestingAgent
from app.database.repository import SQLitePipelineRepository
from app.llm import LLMClient
from main import ControlledBugCodingAgent


class AutonomousWorkflowLLM(LLMClient):
    def __init__(self):
        super().__init__(provider_name="openai", api_key="test-key", model="test-model")

    def verify_configured(self):
        pass

    async def create_json(self, *, system_prompt: str, user_prompt: str, **kwargs):
        if "Architect" in system_prompt or "planning" in system_prompt.lower():
            return {
                "summary": "Calculator Health API Plan",
                "requirements": ["Health endpoint", "Math function", "Unit tests"],
                "architecture": {
                    "frontend": "None",
                    "backend": "Python math service",
                    "database": "SQLite",
                    "security": "Internal",
                },
                "files_to_create": [
                    {"path": "service.py", "language": "python", "purpose": "Math logic"},
                    {"path": "tests/test_service.py", "language": "python", "purpose": "Test suite"},
                ],
                "api_contract": [{"method": "GET", "path": "/health", "description": "Status OK"}],
                "testing_plan": [{"name": "test_add", "target": "tests/test_service.py", "assertion": "add(10, 5) == 15"}],
            }
        elif "Senior Staff Software Engineer" in system_prompt or "generate" in system_prompt.lower():
            return {
                "summary": "Implemented service.py and tests/test_service.py",
                "files": [
                    {
                        "path": "service.py",
                        "language": "python",
                        "purpose": "Math service",
                        "code": (
                            "def add(a: int, b: int) -> int:\n"
                            "    return a + b\n\n"
                            "def is_healthy() -> bool:\n"
                            "    return True\n"
                        ),
                    },
                    {
                        "path": "tests/test_service.py",
                        "language": "python",
                        "purpose": "Unit test suite",
                        "code": (
                            "import unittest\n"
                            "from service import add, is_healthy\n\n"
                            "class ServiceTests(unittest.TestCase):\n"
                            "    def test_add(self):\n"
                            "        self.assertEqual(add(10, 5), 15)\n\n"
                            "    def test_healthy(self):\n"
                            "        self.assertTrue(is_healthy())\n"
                        ),
                    },
                ],
            }
        elif "Site Reliability" in system_prompt or "Self-Healing" in system_prompt:
            # Healing prompt response
            return {
                "root_cause": "Controlled calculation bug subtracted 1 instead of returning pure sum",
                "fix_description": "Updated app_logic.py to return sum(items)",
                "files_to_patch": [
                    {
                        "path": "app_logic.py",
                        "code": "def calculate_total(items: list[int]) -> int:\n    return sum(items)\n",
                    }
                ],
            }
        return {"status": "ok"}


class TestEndToEndWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = f"{self.temp_dir.name}/test_devops.db"
        self.repo = SQLitePipelineRepository(self.db_path)
        self.llm = AutonomousWorkflowLLM()

    def tearDown(self):
        try:
            from app.tools.preview_manager import PreviewManager
            PreviewManager().stop_all()
        except Exception:
            pass
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_e2e_autonomous_pipeline_execution(self):
        """Verify full autonomous chain: User Mission -> Planning -> Coding -> Build -> Testing -> Final Result."""
        pipeline = [
            PlanningAgent(client=self.llm),
            CodingAgent(client=self.llm),
            BuildAgent(),
            TestingAgent(),
        ]
        supervisor = DevelopmentSupervisor(
            pipeline=pipeline,
            repository=self.repo,
            healing_agent=SelfHealingAgent(repository=self.repo, client=self.llm),
            workspace_root=self.temp_dir.name,
        )

        mission = "Build a math calculator service with health check and unit tests"
        result = asyncio.run(supervisor.run_pipeline(mission))

        # 1. Pipeline status completed
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["workflow_state"], "COMPLETED")
        self.assertEqual(result["progress"], 100)

        # 2. Verify all 4 agent stages executed cleanly
        stages = result["stages"]
        self.assertEqual(len(stages), 4)
        stage_names = [s["agent"] for s in stages]
        self.assertEqual(stage_names, ["Planning Agent", "Coding Agent", "Build Agent", "Testing Agent"])

        # 3. Verify real files were written to workspace
        files_in_workspace = result["files_in_workspace"]
        self.assertIn("service.py", files_in_workspace)
        self.assertIn("tests/test_service.py", files_in_workspace)

        # 4. Verify test execution was real
        test_stage = stages[3]
        self.assertEqual(test_stage["output"]["status"], "completed")
        self.assertEqual(test_stage["output"]["passed"], 2)
        self.assertEqual(test_stage["output"]["failed"], 0)

        # 5. Verify persistence in SQLite
        persisted = asyncio.run(self.repo.get(result["task"]["id"]))
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted["status"], "completed")

    def test_e2e_intentional_failure_and_self_healing(self):
        """Verify: Controlled Bug -> Real Failure -> Diagnosis -> Patch -> Retest -> Pass -> DB Memory Saved."""
        failing_pipeline = [
            ControlledBugCodingAgent(),  # Injects calculate_total returning sum - 1
            BuildAgent(),                # Syntax is valid
            TestingAgent(),              # Test fails: 59 != 60
        ]
        supervisor = DevelopmentSupervisor(
            pipeline=failing_pipeline,
            repository=self.repo,
            healing_agent=SelfHealingAgent(repository=self.repo, client=self.llm),
            workspace_root=self.temp_dir.name,
        )

        mission = "Execute intentional failure test"
        result = asyncio.run(supervisor.run_pipeline(mission))

        # 1. Pipeline ultimately completed via self-healing
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["workflow_state"], "COMPLETED")

        # 2. Verify the Testing Agent stage was healed
        testing_stage = result["stages"][2]
        self.assertEqual(testing_stage["status"], "healed")
        self.assertTrue(testing_stage["output"]["healed"])
        self.assertIn("app_logic.py", testing_stage["output"]["files_modified"])

        # 3. Verify failure was captured and persisted in SQLite Failure Memory
        failures = asyncio.run(self.repo.list_failure_memory())
        self.assertGreaterEqual(len(failures), 1)
        self.assertEqual(failures[0]["failed_agent"], "Testing Agent")
        self.assertTrue(failures[0]["success"])
        self.assertIn("app_logic.py", failures[0]["files_modified"])


if __name__ == "__main__":
    unittest.main()
