"""Unit and integration tests for real agent responsibilities (Planning, Coding, Build, Testing)."""

import asyncio
import tempfile
import unittest
from unittest.mock import MagicMock

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.testing_agent import TestingAgent
from app.llm import LLMClient
from app.tools.workspace import WorkspaceManager


class FakeLLMClient(LLMClient):
    def __init__(self, plan_data=None, code_data=None):
        super().__init__(provider_name="openai", api_key="test-key", model="test-model")
        self.plan_data = plan_data or {
            "summary": "Calculator Microservice Plan",
            "requirements": ["Math API", "Unit Tests"],
            "architecture": {"frontend": "None", "backend": "Python", "database": "SQLite"},
            "acceptance_criteria": ["All unit tests pass", "Zero syntax errors"],
            "files_to_create": [
                {"path": "calc.py", "language": "python", "purpose": "Math functions"},
                {"path": "models.py", "language": "python", "purpose": "Models"},
                {"path": "tests/test_calc.py", "language": "python", "purpose": "Tests"}
            ],
            "api_contract": [{"method": "GET", "path": "/add", "description": "Add numbers"}],
        }
        self.code_data = code_data or {
            "summary": "Generated calc.py, models.py, and tests/test_calc.py",
            "files": [
                {
                    "path": "calc.py",
                    "language": "python",
                    "purpose": "Math logic",
                    "code": "def add(a: int, b: int) -> int:\n    return a + b\n\ndef multiply(a: int, b: int) -> int:\n    return a * b\n",
                },
                {
                    "path": "models.py",
                    "language": "python",
                    "purpose": "Data models",
                    "code": "class Operation:\n    pass\n",
                },
                {
                    "path": "tests/test_calc.py",
                    "language": "python",
                    "purpose": "Math unit tests",
                    "code": (
                        "import unittest\n"
                        "from calc import add, multiply\n\n"
                        "class TestCalc(unittest.TestCase):\n"
                        "    def test_add(self):\n"
                        "        self.assertEqual(add(2, 3), 5)\n\n"
                        "    def test_multiply(self):\n"
                        "        self.assertEqual(multiply(3, 4), 12)\n"
                    ),
                },
            ],
        }

    def verify_configured(self):
        pass

    async def create_json(self, *, system_prompt: str, user_prompt: str, **kwargs):
        if "Architect" in system_prompt or "files_to_create" in system_prompt:
            return self.plan_data
        return self.code_data


class TestRealAgents(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = WorkspaceManager(
            workspace_root=self.temp_dir.name,
            user_id="u1",
            mission_id="m1",
        )
        self.fake_llm = FakeLLMClient()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_planning_agent_produces_structured_plan(self):
        agent = PlanningAgent(client=self.fake_llm)
        task = {"id": "t1", "request": "Build a calculator API"}
        output = asyncio.run(agent.execute(task, {}))

        self.assertIn("files_to_create", output)
        self.assertEqual(len(output["files_to_create"]), 3)
        self.assertEqual(output["summary"], "Calculator Microservice Plan")

    def test_planning_agent_missing_key_raises_error(self):
        unconfigured_llm = LLMClient(api_key="")
        agent = PlanningAgent(client=unconfigured_llm)
        task = {"id": "t1", "request": "Build an API"}
        with self.assertRaises(RuntimeError) as ctx:
            asyncio.run(agent.execute(task, {}))
        self.assertIn("LLM API key is not configured.", str(ctx.exception))

    def test_coding_agent_writes_real_files_to_workspace(self):
        agent = CodingAgent(client=self.fake_llm)
        task = {"id": "t1", "request": "Build a calculator API"}
        context = {
            "workspace": self.workspace,
            "Planning Agent": {"output": self.fake_llm.plan_data},
        }

        output = asyncio.run(agent.execute(task, context))
        self.assertEqual(len(output["files_written"]), 3)

        # Verify files were actually written to physical disk
        calc_content = self.workspace.read_file("calc.py")
        self.assertIn("def add(", calc_content)
        self.assertIn("def multiply(", calc_content)

        test_content = self.workspace.read_file("tests/test_calc.py")
        self.assertIn("class TestCalc(unittest.TestCase):", test_content)

    def test_build_agent_performs_real_ast_checks_and_compiles(self):
        # Write clean files to workspace
        self.workspace.write_file("calc.py", "def add(a, b): return a + b\n")
        context = {"workspace": self.workspace}
        task = {"id": "t1", "request": "Build calculator"}

        build_agent = BuildAgent()
        output = asyncio.run(build_agent.execute(task, context))

        self.assertEqual(output["status"], "success")
        self.assertTrue(output["success"])
        self.assertEqual(output["exit_code"], 0)
        self.assertEqual(len(output["syntax_checks"]), 1)
        self.assertTrue(output["syntax_checks"][0]["ast_valid"])

    def test_build_agent_detects_real_syntax_error(self):
        # Write file with syntax error
        self.workspace.write_file("bad_code.py", "def broken_syntax(:\n")
        context = {"workspace": self.workspace}
        task = {"id": "t1", "request": "Build calculator"}

        build_agent = BuildAgent()
        with self.assertRaises(RuntimeError) as ctx:
            asyncio.run(build_agent.execute(task, context))
        self.assertIn("BUILD_SYNTAX_ERROR", str(ctx.exception))

    def test_testing_agent_runs_real_tests_and_passes(self):
        # Write real code and passing tests
        self.workspace.write_file("calc.py", "def add(a, b): return a + b\n")
        self.workspace.write_file(
            "tests/test_calc.py",
            "import unittest\nfrom calc import add\nclass Test(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(1, 2), 3)\n"
        )
        context = {"workspace": self.workspace}
        task = {"id": "t1", "request": "Test calculator"}

        testing_agent = TestingAgent()
        output = asyncio.run(testing_agent.execute(task, context))

        self.assertEqual(output["status"], "completed")
        self.assertTrue(output["success"])
        self.assertEqual(output["passed"], 1)
        self.assertEqual(output["failed"], 0)
        self.assertEqual(len(output["test_cases"]), 1)

    def test_testing_agent_detects_real_assertion_failure(self):
        # Write real code with broken logic
        self.workspace.write_file("calc.py", "def add(a, b): return a - b\n")
        self.workspace.write_file(
            "tests/test_calc.py",
            "import unittest\nfrom calc import add\nclass Test(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2, 3), 5)\n"
        )
        context = {"workspace": self.workspace}
        task = {"id": "t1", "request": "Test calculator"}

        testing_agent = TestingAgent()
        with self.assertRaises(RuntimeError) as ctx:
            asyncio.run(testing_agent.execute(task, context))
        self.assertIn("TESTS_FAILED", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
