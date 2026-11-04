"""10-Scenario Autonomous DevOps Swarm Mission Test Suite.

Verifies end-to-end autonomous agent execution, failure classification,
self-healing, database failure memory learning, security quality gates,
git workspace checkpoints, and governance approval gates.
"""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from app.agents import (
    BaseAgent,
    BuildAgent,
    CodingAgent,
    DevelopmentSupervisor,
    PlanningAgent,
    SelfHealingAgent,
    TestingAgent,
)
from app.agents.operations.security_agent import SecurityAgent
from app.database.repository import SQLitePipelineRepository
from app.llm import LLMClient
from app.tools.failure_classifier import FailureClassifier
from app.tools.security_scanner import SecurityScanner
from app.tools.workspace import WorkspaceManager


class MockDeterministicLLMClient(LLMClient):
    """Deterministic LLM client for rapid test execution without external API dependency."""

    def __init__(self, plan_data=None, code_data=None, heal_data=None) -> None:
        super().__init__(provider_name="openai", api_key="sk-test-mock-key-only", model="gpt-4o-mini")
        self.plan_data = plan_data or {
            "summary": "Calculator Application",
            "requirements": ["add", "subtract", "multiply", "divide", "unit tests"],
            "architecture": {"backend": "Python 3.12", "testing": "unittest"},
            "acceptance_criteria": ["All unit tests pass", "AST valid"],
            "files_to_create": [
                {"path": "calc.py", "language": "python", "purpose": "Calculator logic"},
                {"path": "tests/test_calc.py", "language": "python", "purpose": "Unit tests"},
            ],
            "api_contract": [],
        }
        self.code_data = code_data or {
            "summary": "Generated calculator and tests",
            "files": [
                {
                    "path": "calc.py",
                    "language": "python",
                    "purpose": "Math functions",
                    "code": (
                        "def add(a, b):\n    return a + b\n\n"
                        "def subtract(a, b):\n    return a - b\n\n"
                        "def multiply(a, b):\n    return a * b\n\n"
                        "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b\n"
                    ),
                },
                {
                    "path": "tests/test_calc.py",
                    "language": "python",
                    "purpose": "Unit tests",
                    "code": (
                        "import unittest\nfrom calc import add, subtract, multiply, divide\n\n"
                        "class TestCalc(unittest.TestCase):\n"
                        "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n"
                        "    def test_subtract(self):\n        self.assertEqual(subtract(5, 2), 3)\n"
                        "    def test_multiply(self):\n        self.assertEqual(multiply(4, 2), 8)\n"
                        "    def test_divide(self):\n        self.assertEqual(divide(10, 2), 5)\n"
                        "        with self.assertRaises(ValueError):\n            divide(10, 0)\n"
                    ),
                },
            ],
        }
        self.heal_data = heal_data or {
            "root_cause": "Fixed logic calculation defect",
            "fix_description": "Corrected arithmetic operator to match test assertions",
            "files_to_patch": [
                {
                    "path": "calc.py",
                    "code": (
                        "def add(a, b):\n    return a + b\n\n"
                        "def subtract(a, b):\n    return a - b\n\n"
                        "def multiply(a, b):\n    return a * b\n\n"
                        "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b\n"
                    ),
                }
            ],
            "message": "Healed defect",
        }

    async def create_json(self, *, system_prompt: str, user_prompt: str, **kwargs):
        self._record_metrics({"usage": {"prompt_tokens": 150, "completion_tokens": 200}}, duration_ms=45.0)
        if "Site Reliability" in system_prompt or "Self-Healing" in system_prompt:
            return self.heal_data
        if "Senior Staff Software Engineer" in system_prompt:
            return self.code_data
        if "Principal Software Architect" in system_prompt:
            return self.plan_data
        return self.plan_data

    async def create_text(self, *, system_prompt: str, user_prompt: str, **kwargs):
        self._record_metrics({"usage": {"prompt_tokens": 100, "completion_tokens": 50}}, duration_ms=25.0)
        return "Autonomous DevOps Swarm execution log."


class TestRealMissionSuite(unittest.TestCase):
    """10 Progressive Real Mission Test Scenarios."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)
        self.db_path = self.workspace_root / "test_missions.db"
        self.repo = SQLitePipelineRepository(self.db_path)

    def tearDown(self) -> None:
        try:
            from app.tools.preview_manager import PreviewManager
            PreviewManager().stop_all()
        except Exception:
            pass
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Scenario 1: Simple Python Calculator Application
    # -------------------------------------------------------------------------
    def test_scenario_01_simple_python_calculator(self) -> None:
        """Scenario 1: End-to-end execution of a Python calculator mission with git commit."""
        mock_llm = MockDeterministicLLMClient()
        supervisor = DevelopmentSupervisor(
            pipeline=[PlanningAgent(client=mock_llm), CodingAgent(client=mock_llm), BuildAgent(), TestingAgent()],
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Create a Python calculator application with add, subtract, multiply, divide."))

        self.assertEqual(result["workflow_state"], "COMPLETED")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertIn("calc.py", result["files_in_workspace"])
        self.assertIn("tests/test_calc.py", result["files_in_workspace"])
        self.assertTrue(len(result["git_commits"]) >= 1)

    # -------------------------------------------------------------------------
    # Scenario 2: REST API Application
    # -------------------------------------------------------------------------
    def test_scenario_02_rest_api_application(self) -> None:
        """Scenario 2: REST API application with route definitions, health check, and tests."""
        api_code = {
            "summary": "REST API with health and items endpoints",
            "files": [
                {
                    "path": "api.py",
                    "language": "python",
                    "purpose": "REST API endpoints",
                    "code": (
                        "class SimpleAPI:\n"
                        "    def __init__(self):\n        self.items = {}\n"
                        "    def get_health(self):\n        return {'status': 'healthy'}\n"
                        "    def create_item(self, item_id, name):\n        self.items[item_id] = name\n        return {'id': item_id, 'name': name}\n"
                        "    def get_item(self, item_id):\n        return self.items.get(item_id)\n"
                    ),
                },
                {
                    "path": "tests/test_api.py",
                    "language": "python",
                    "purpose": "REST API tests",
                    "code": (
                        "import unittest\nfrom api import SimpleAPI\n\n"
                        "class TestAPI(unittest.TestCase):\n"
                        "    def test_health(self):\n        api = SimpleAPI()\n        self.assertEqual(api.get_health()['status'], 'healthy')\n"
                        "    def test_crud(self):\n        api = SimpleAPI()\n        api.create_item('1', 'Test')\n        self.assertEqual(api.get_item('1'), 'Test')\n"
                    ),
                },
            ],
        }
        mock_llm = MockDeterministicLLMClient(code_data=api_code)
        supervisor = DevelopmentSupervisor(
            pipeline=[PlanningAgent(client=mock_llm), CodingAgent(client=mock_llm), BuildAgent(), TestingAgent()],
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Build a REST API application with health check and item management."))

        self.assertEqual(result["workflow_state"], "COMPLETED")
        self.assertIn("api.py", result["files_in_workspace"])

    # -------------------------------------------------------------------------
    # Scenario 3: Database Persistence Application
    # -------------------------------------------------------------------------
    def test_scenario_03_database_persistence_app(self) -> None:
        """Scenario 3: Application with SQLite database persistence and CRUD logic."""
        db_code = {
            "summary": "SQLite Persistence Store",
            "files": [
                {
                    "path": "db_app.py",
                    "language": "python",
                    "purpose": "Database persistence",
                    "code": (
                        "import sqlite3\n\n"
                        "class TaskRepository:\n"
                        "    def __init__(self, db_path=':memory:'):\n"
                        "        self.conn = sqlite3.connect(db_path)\n"
                        "        self.conn.execute('CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT)')\n"
                        "    def add_task(self, title):\n"
                        "        with self.conn:\n"
                        "            cur = self.conn.execute('INSERT INTO tasks (title) VALUES (?)', (title,))\n"
                        "            return cur.lastrowid\n"
                        "    def get_tasks(self):\n"
                        "        cur = self.conn.execute('SELECT id, title FROM tasks')\n"
                        "        return [{'id': r[0], 'title': r[1]} for r in cur.fetchall()]\n"
                    ),
                },
                {
                    "path": "tests/test_db_app.py",
                    "language": "python",
                    "purpose": "Database tests",
                    "code": (
                        "import unittest\nfrom db_app import TaskRepository\n\n"
                        "class TestDB(unittest.TestCase):\n"
                        "    def test_persistence(self):\n"
                        "        repo = TaskRepository()\n"
                        "        task_id = repo.add_task('Buy milk')\n"
                        "        tasks = repo.get_tasks()\n"
                        "        self.assertEqual(len(tasks), 1)\n"
                        "        self.assertEqual(tasks[0]['title'], 'Buy milk')\n"
                    ),
                },
            ],
        }
        mock_llm = MockDeterministicLLMClient(code_data=db_code)
        supervisor = DevelopmentSupervisor(
            pipeline=[PlanningAgent(client=mock_llm), CodingAgent(client=mock_llm), BuildAgent(), TestingAgent()],
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Build a task management application with database persistence."))
        self.assertEqual(result["workflow_state"], "COMPLETED")
        self.assertIn("db_app.py", result["files_in_workspace"])

    # -------------------------------------------------------------------------
    # Scenario 4: Docker Containerized Application
    # -------------------------------------------------------------------------
    def test_scenario_04_docker_containerized_app(self) -> None:
        """Scenario 4: Application with valid Dockerfile and entrypoint script."""
        docker_code = {
            "summary": "Containerized application with Dockerfile",
            "files": [
                {
                    "path": "Dockerfile",
                    "language": "dockerfile",
                    "purpose": "Docker build configuration",
                    "code": "FROM python:3.12-slim\nWORKDIR /app\nCOPY . /app\nCMD [\"python\", \"main.py\"]\n",
                },
                {
                    "path": "main.py",
                    "language": "python",
                    "purpose": "Entrypoint",
                    "code": "def run():\n    return 'Container running'\nif __name__ == '__main__':\n    print(run())\n",
                },
                {
                    "path": "tests/test_main.py",
                    "language": "python",
                    "purpose": "Tests",
                    "code": "import unittest\nfrom main import run\nclass TestMain(unittest.TestCase):\n    def test_run(self):\n        self.assertEqual(run(), 'Container running')\n",
                },
            ],
        }
        mock_llm = MockDeterministicLLMClient(code_data=docker_code)
        supervisor = DevelopmentSupervisor(
            pipeline=[PlanningAgent(client=mock_llm), CodingAgent(client=mock_llm), BuildAgent(), TestingAgent()],
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Build a containerized Python application with Docker support."))
        self.assertEqual(result["workflow_state"], "COMPLETED")
        self.assertIn("Dockerfile", result["files_in_workspace"])

    # -------------------------------------------------------------------------
    # Scenario 5: Real Syntax Failure Detection & Healing
    # -------------------------------------------------------------------------
    def test_scenario_05_syntax_failure_detection_and_healing(self) -> None:
        """Scenario 5: BuildAgent catches real syntax error, classifies as SYNTAX_ERROR, and heals it."""
        # 1. Verify failure classifier identifies syntax errors
        classifier = FailureClassifier()
        diag = classifier.classify("SyntaxError: invalid syntax on line 12")
        self.assertEqual(diag["category"], "SYNTAX_ERROR")
        self.assertTrue(diag["retryable"])

        # 2. End-to-end healing of syntax error
        class SyntaxDefectCodingAgent(BaseAgent):
            name = "Coding Agent"
            async def execute(self, task, context):
                ws: WorkspaceManager = context["workspace"]
                broken_code = "def add(a, b)\n    return a + b\n"  # Missing colon
                test_code = "import unittest\nfrom calc import add\nclass T(unittest.TestCase):\n    def test(self):\n        self.assertEqual(add(1, 2), 3)\n"
                ws.write_file("calc.py", broken_code)
                ws.write_file("tests/test_calc.py", test_code)
                return {"files_written": [{"path": "calc.py"}, {"path": "tests/test_calc.py"}]}

        mock_llm = MockDeterministicLLMClient(heal_data={
            "root_cause": "Missing colon in function signature",
            "fix_description": "Added colon to def add(a, b):",
            "files_to_patch": [{"path": "calc.py", "code": "def add(a, b):\n    return a + b\n"}],
            "message": "Syntax repaired",
        })
        healing_agent = SelfHealingAgent(repository=self.repo, client=mock_llm)
        supervisor = DevelopmentSupervisor(
            pipeline=[SyntaxDefectCodingAgent(), BuildAgent(), TestingAgent()],
            healing_agent=healing_agent,
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Repair syntax error."))
        self.assertEqual(result["workflow_state"], "COMPLETED")
        stages = result["stages"]
        self.assertEqual(stages[1]["status"], "healed")

    # -------------------------------------------------------------------------
    # Scenario 6: Real Test Assertion Failure & Healing
    # -------------------------------------------------------------------------
    def test_scenario_06_test_assertion_failure_and_healing(self) -> None:
        """Scenario 6: TestingAgent detects real assertion mismatch, classifies TEST_ASSERTION_FAILURE, and heals it."""
        classifier = FailureClassifier()
        diag = classifier.classify("AssertionError: 10 != 20")
        self.assertEqual(diag["category"], "TEST_ASSERTION_FAILURE")

        class AssertionDefectCodingAgent(BaseAgent):
            name = "Coding Agent"
            async def execute(self, task, context):
                ws: WorkspaceManager = context["workspace"]
                flawed_code = "def multiply(a, b):\n    return a + b\n"  # Flawed logic
                test_code = "import unittest\nfrom calc import multiply\nclass T(unittest.TestCase):\n    def test(self):\n        self.assertEqual(multiply(3, 4), 12)\n"
                ws.write_file("calc.py", flawed_code)
                ws.write_file("tests/test_calc.py", test_code)
                return {"files_written": [{"path": "calc.py"}, {"path": "tests/test_calc.py"}]}

        mock_llm = MockDeterministicLLMClient(heal_data={
            "root_cause": "Function used addition instead of multiplication",
            "fix_description": "Changed operator to *",
            "files_to_patch": [{"path": "calc.py", "code": "def multiply(a, b):\n    return a * b\n"}],
            "message": "Fixed multiplication",
        })
        healing_agent = SelfHealingAgent(repository=self.repo, client=mock_llm)
        supervisor = DevelopmentSupervisor(
            pipeline=[AssertionDefectCodingAgent(), BuildAgent(), TestingAgent()],
            healing_agent=healing_agent,
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Fix assertion failure."))
        self.assertEqual(result["workflow_state"], "COMPLETED")
        self.assertEqual(result["stages"][2]["status"], "healed")

    # -------------------------------------------------------------------------
    # Scenario 7: Missing Dependency / Import Error Diagnosis & Healing
    # -------------------------------------------------------------------------
    def test_scenario_07_missing_dependency_healing(self) -> None:
        """Scenario 7: ModuleNotFoundError classified as IMPORT_OR_MODULE_ERROR and resolved."""
        classifier = FailureClassifier()
        diag = classifier.classify("ModuleNotFoundError: No module named 'utils'")
        self.assertEqual(diag["category"], "IMPORT_OR_MODULE_ERROR")

        class MissingModuleCodingAgent(BaseAgent):
            name = "Coding Agent"
            async def execute(self, task, context):
                ws: WorkspaceManager = context["workspace"]
                app_code = "from utils import helper\ndef run():\n    return helper()\n"
                test_code = "import unittest\nfrom app import run\nclass T(unittest.TestCase):\n    def test(self):\n        self.assertEqual(run(), 'ok')\n"
                ws.write_file("app.py", app_code)
                ws.write_file("tests/test_app.py", test_code)
                return {"files_written": [{"path": "app.py"}, {"path": "tests/test_app.py"}]}

        mock_llm = MockDeterministicLLMClient(heal_data={
            "root_cause": "Missing internal helper module utils.py",
            "fix_description": "Created utils.py module providing helper function",
            "files_to_patch": [{"path": "utils.py", "code": "def helper():\n    return 'ok'\n"}],
            "message": "Created missing module",
        })
        healing_agent = SelfHealingAgent(repository=self.repo, client=mock_llm)
        supervisor = DevelopmentSupervisor(
            pipeline=[MissingModuleCodingAgent(), BuildAgent(), TestingAgent()],
            healing_agent=healing_agent,
            repository=self.repo,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Fix missing module."))
        self.assertEqual(result["workflow_state"], "COMPLETED")

    # -------------------------------------------------------------------------
    # Scenario 8: Healing Retry Limit Enforcement
    # -------------------------------------------------------------------------
    def test_scenario_08_healing_retry_limit_stops_after_max_attempts(self) -> None:
        """Scenario 8: Continuous unresolvable failure stops at max_retries and marks mission FAILED."""
        class UnfixableCodingAgent(BaseAgent):
            name = "Coding Agent"
            async def execute(self, task, context):
                ws: WorkspaceManager = context["workspace"]
                ws.write_file("calc.py", "def add(a, b): return a + b\n")
                ws.write_file("tests/test_unfixable.py", "import unittest\nclass T(unittest.TestCase):\n    def test_fail(self):\n        self.fail('Permanent unfixable failure')\n")
                return {"files_written": [{"path": "calc.py"}, {"path": "tests/test_unfixable.py"}]}

        mock_llm = MockDeterministicLLMClient(heal_data={
            "root_cause": "Unfixable test case",
            "fix_description": "Did not change test",
            "files_to_patch": [{"path": "calc.py", "code": "def add(a, b): return a + b\n"}],
            "message": "Unable to heal",
        })
        healing_agent = SelfHealingAgent(repository=self.repo, client=mock_llm)
        supervisor = DevelopmentSupervisor(
            pipeline=[UnfixableCodingAgent(), BuildAgent(), TestingAgent()],
            healing_agent=healing_agent,
            repository=self.repo,
            max_internal_retries=3,
            workspace_root=self.workspace_root,
        )

        result = asyncio.run(supervisor.run_pipeline("Test retry ceiling."))
        self.assertEqual(result["workflow_state"], "FAILED")
        self.assertEqual(result["status"], "failed")

    # -------------------------------------------------------------------------
    # Scenario 9: Repeated Failure Learning via DB Memory
    # -------------------------------------------------------------------------
    def test_scenario_09_repeated_failure_memory_learning(self) -> None:
        """Scenario 9: Failure and verified solution stored in SQLite and matched for subsequent failures."""
        record = {
            "failure_id": str(uuid4()),
            "pipeline_id": "test-pipe-1",
            "user_id": "tester",
            "failed_agent": "Testing Agent",
            "error_category": "TEST_ASSERTION_FAILURE",
            "error_signature": "AssertionError: Expected 42 but got 0",
            "error_message": "Traceback: AssertionError: Expected 42 but got 0",
            "stack_trace_hash": "hash123",
            "affected_component": "calc.py",
            "affected_files": ["calc.py"],
            "git_diff": "diff --git a/calc.py",
            "root_cause": "Default constant returned 0 instead of 42",
            "fix_description": "Set ANSWER = 42",
            "files_modified": ["calc.py"],
            "attempts": 1,
            "tech_stack": "python",
            "verification_result": "PASS",
            "success": True,
        }
        asyncio.run(self.repo.save_failure_memory(record))

        # Query matching pattern
        pattern = asyncio.run(self.repo.find_matching_healing_pattern("AssertionError: Expected 42 but got 0"))
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern["root_cause"], "Default constant returned 0 instead of 42")
        self.assertEqual(pattern["error_category"], "TEST_ASSERTION_FAILURE")

    # -------------------------------------------------------------------------
    # Scenario 10: Security Violation Quality Gate
    # -------------------------------------------------------------------------
    def test_scenario_10_security_violation_quality_gate(self) -> None:
        """Scenario 10: Injected API key or destructive command is blocked by SecurityAgent."""
        # 1. Test SecurityScanner directly
        scanner = SecurityScanner()
        leaked_key_text = "NVIDIA_KEY = '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'"
        findings = scanner.scan_text(leaked_key_text)
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0]["category"], "SECRET_LEAK")
        # Ensure secret is redacted in output snippet
        self.assertNotIn("NGL2UlebbtEMIpMP4OGGWj6kUhCuGY1Dl8099EeWk4QR3jdj_tbrt3lwUgSYh1mQ", findings[0]["snippet"])

        # 2. Test SecurityAgent rejecting workspace with leak
        ws = WorkspaceManager(workspace_root=self.workspace_root, user_id="test", mission_id="sec_test")
        ws.write_file("config.py", "API_TOKEN = 'sk-proj-1234567890abcdef1234567890abcdef1234567890abcdef'")

        sec_agent = SecurityAgent()
        context = {"workspace": ws}
        with self.assertRaises(RuntimeError) as cm:
            asyncio.run(sec_agent.execute({"id": "sec_test"}, context))
        self.assertIn("SECURITY_GATE_FAILED", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
