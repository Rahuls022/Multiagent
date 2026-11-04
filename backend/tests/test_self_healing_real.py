"""Unit and integration tests for real self-healing, failure memory, and retry limits."""

import asyncio
import tempfile
import unittest

from app.agents.development_supervisor import DevelopmentSupervisor
from app.agents.healing_agent import SelfHealingAgent
from app.agents.testing_agent import TestingAgent
from app.database.repository import InMemoryPipelineRepository
from app.llm import LLMClient
from app.tools.workspace import WorkspaceManager


class HealingLLMClient(LLMClient):
    def __init__(self, should_succeed: bool = True):
        super().__init__(provider_name="openai", api_key="mock-key", model="mock-model")
        self.should_succeed = should_succeed

    def verify_configured(self):
        pass

    async def create_json(self, *, system_prompt: str, user_prompt: str, **kwargs):
        if self.should_succeed:
            # Provide working fix
            return {
                "root_cause": "The add function used subtraction (-) instead of addition (+)",
                "fix_description": "Changed 'a - b' to 'a + b' in calc.py",
                "files_to_patch": [
                    {
                        "path": "calc.py",
                        "code": "def add(a: int, b: int) -> int:\n    return a + b\n\ndef multiply(a: int, b: int) -> int:\n    return a * b\n",
                    }
                ],
            }
        else:
            # Provide broken fix that still fails
            return {
                "root_cause": "Still broken",
                "fix_description": "Did not fix bug",
                "files_to_patch": [
                    {
                        "path": "calc.py",
                        "code": "def add(a: int, b: int) -> int:\n    return a - b\n",
                    }
                ],
            }


class TestSelfHealingReal(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = WorkspaceManager(
            workspace_root=self.temp_dir.name,
            user_id="user_heal",
            mission_id="mission_heal",
        )
        self.repo = InMemoryPipelineRepository()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_real_self_healing_fixes_code_and_persists_to_memory(self):
        # 1. Create broken file and test
        self.workspace.write_file("calc.py", "def add(a, b): return a - b\n")
        self.workspace.write_file(
            "tests/test_calc.py",
            "import unittest\nfrom calc import add\nclass Test(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2, 3), 5)\n"
        )

        task = {"id": "mission_heal", "request": "Fix math module", "user_id": "user_heal"}
        context = {"workspace": self.workspace}

        # 2. Run testing agent to capture real failure
        testing_agent = TestingAgent()
        failed_stage = asyncio.run(testing_agent.run(task, context))
        self.assertEqual(failed_stage["status"], "failed")

        # 3. Heal using real healing agent with HealingLLMClient
        healing_agent = SelfHealingAgent(repository=self.repo, client=HealingLLMClient(should_succeed=True))
        healed_stage = asyncio.run(healing_agent.heal(failed_stage, task, context))

        # 4. Verify stage was healed and tests passed
        self.assertEqual(healed_stage["status"], "healed")
        self.assertTrue(healed_stage["output"]["healed"])
        self.assertIn("calc.py", healed_stage["output"]["files_modified"])

        # 5. Verify the file on disk was actually patched
        calc_content = self.workspace.read_file("calc.py")
        self.assertIn("return a + b", calc_content)

        # 6. Verify failure memory was recorded in repository
        failures = asyncio.run(self.repo.list_failure_memory())
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["failed_agent"], "Testing Agent")
        self.assertTrue(failures[0]["success"])
        self.assertIn("calc.py", failures[0]["files_modified"])

        # 7. Verify pattern retrieval
        pattern = asyncio.run(self.repo.find_matching_healing_pattern(failures[0]["error_signature"]))
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern["root_cause"], failures[0]["root_cause"])

    def test_maximum_retry_protection_stops_after_3_attempts(self):
        """Verify supervisor stops after max retries and marks mission as FAILED instead of looping indefinitely."""
        # Create permanently failing test
        self.workspace.write_file("calc.py", "def add(a, b): return a - b\n")
        self.workspace.write_file(
            "tests/test_calc.py",
            "import unittest\nfrom calc import add\nclass Test(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2, 3), 5)\n"
        )

        failing_healing_agent = SelfHealingAgent(
            repository=self.repo,
            client=HealingLLMClient(should_succeed=False)
        )

        supervisor = DevelopmentSupervisor(
            pipeline=[TestingAgent()],
            repository=self.repo,
            healing_agent=failing_healing_agent,
            max_internal_retries=3,
            workspace_root=self.temp_dir.name,
        )

        task = {"id": "mission_heal", "request": "Permanently failing mission", "user_id": "user_heal"}
        result = asyncio.run(supervisor.run_pipeline("Permanently failing mission", task=task))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["workflow_state"], "FAILED")

        # Verify exactly 3 DEV_INTERNAL_RETRY events were logged
        retry_events = [e for e in result["events"] if e.get("event") == "DEV_INTERNAL_RETRY"]
        self.assertEqual(len(retry_events), 3)


if __name__ == "__main__":
    unittest.main()
