"""Comprehensive test suite for Agent Skills Integration in Autonomous DevOps Swarm.

Verifies:
1. Discovery and parsing of the 4 designated skills from skills.sh (.agents/skills/)
2. Dedicated 1-to-1 agent mappings (Planning -> writing-plans, Coding -> frontend-design, Build -> systematic-debugging, Testing -> verification-before-completion)
3. Skill prompt injections for each agent specialist
4. Planning Agent execution attaching 'writing-plans'
5. Coding Agent execution attaching 'frontend-design'
6. Build Agent execution attaching 'systematic-debugging'
7. Testing Agent execution attaching 'verification-before-completion'
8. REST API /api/skills endpoint returning available skills and mappings
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import tempfile
import unittest

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from starlette.testclient import TestClient

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.testing_agent import TestingAgent
from app.database.repository import SQLitePipelineRepository
from app.llm.client import LLMClient
from app.skills.skill_registry import SkillRegistry, get_skill_registry
from app.tools.workspace import WorkspaceManager
from main import app


class StubLLMClient(LLMClient):
    """Stub client that behaves as unconfigured to verify deterministic domain generators."""

    def __init__(self) -> None:
        self.api_key = ""
        self.provider_name = "offline"
        self.model = "offline-model"

    @property
    def is_configured(self) -> bool:
        return False

    def verify_configured(self) -> None:
        raise RuntimeError("LLM API key is not configured.")

    async def create_json(self, *args, **kwargs):
        raise RuntimeError("LLM API key is not configured.")


class TestAgentSkills(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = SQLitePipelineRepository("devops_swarm.db")
        app.state.pipeline_repository = cls.repo
        cls.client = TestClient(app)

    def test_01_skill_registry_loads_four_designated_skills(self):
        registry = get_skill_registry()
        available = {s["name"]: s for s in registry.list_available_skills()}

        self.assertIn("writing-plans", available, "writing-plans skill must be loaded")
        self.assertIn("frontend-design", available, "frontend-design skill must be loaded")
        self.assertIn("systematic-debugging", available, "systematic-debugging skill must be loaded")
        self.assertIn("verification-before-completion", available, "verification-before-completion skill must be loaded")

    def test_02_agent_to_skill_mappings(self):
        registry = get_skill_registry()
        mappings = registry.list_agent_skills()

        self.assertEqual(mappings["Planning Agent"], "writing-plans")
        self.assertEqual(mappings["Coding Agent"], "frontend-design")
        self.assertEqual(mappings["Build Agent"], "systematic-debugging")
        self.assertEqual(mappings["Testing Agent"], "verification-before-completion")

    def test_03_skill_prompt_injections(self):
        registry = get_skill_registry()

        plan_inj = registry.get_prompt_injection("Planning Agent")
        self.assertIn("writing-plans", plan_inj)
        self.assertIn("Task Right-Sizing", plan_inj)

        code_inj = registry.get_prompt_injection("Coding Agent")
        self.assertIn("frontend-design", code_inj)
        self.assertIn("Distinctive Visual Identity", code_inj)

        build_inj = registry.get_prompt_injection("Build Agent")
        self.assertIn("systematic-debugging", build_inj)
        self.assertIn("The Iron Law", build_inj)

        test_inj = registry.get_prompt_injection("Testing Agent")
        self.assertIn("verification-before-completion", test_inj)
        self.assertIn("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE", test_inj)

    def test_04_planning_agent_records_skill(self):
        with tempfile.TemporaryDirectory() as td:
            ws = WorkspaceManager(workspace_root=Path(td), user_id="test_user", mission_id="test_plan_skill")
            agent = PlanningAgent(client=StubLLMClient())
            task = {"id": "test_plan_skill", "request": "Juice Centre Ordering App", "user_id": "test_user"}
            context = {"workspace": ws}

            res = asyncio.run(agent.execute(task, context))

            self.assertIn("skills_used", res)
            self.assertIn("writing-plans", res["skills_used"])
            self.assertEqual(res.get("skill_applied", {}).get("name"), "writing-plans")

    def test_05_coding_agent_records_skill(self):
        with tempfile.TemporaryDirectory() as td:
            ws = WorkspaceManager(workspace_root=Path(td), user_id="test_user", mission_id="test_code_skill")
            agent = CodingAgent(client=StubLLMClient())
            task = {"id": "test_code_skill", "request": "Juice Centre Ordering App", "user_id": "test_user"}
            context = {
                "workspace": ws,
                "Planning Agent": {
                    "output": {
                        "summary": "Juice Centre Plan",
                        "requirements": ["Juice catalog", "Shopping cart"],
                        "files_to_create": [
                            {"path": "index.html", "language": "html", "purpose": "Juice storefront"},
                            {"path": "styles.css", "language": "css", "purpose": "Juice styles"},
                            {"path": "app.js", "language": "javascript", "purpose": "Juice state"},
                            {"path": "app.py", "language": "python", "purpose": "Backend API"},
                            {"path": "tests/test_app.py", "language": "python", "purpose": "Tests"},
                        ],
                    }
                },
            }

            res = asyncio.run(agent.execute(task, context))

            self.assertIn("skills_used", res)
            self.assertIn("frontend-design", res["skills_used"])
            self.assertEqual(res.get("skill_applied", {}).get("name"), "frontend-design")

    def test_06_build_agent_records_skill(self):
        with tempfile.TemporaryDirectory() as td:
            ws = WorkspaceManager(workspace_root=Path(td), user_id="test_user", mission_id="test_build_skill")
            ws.write_file("app.py", "def add(a, b):\n    return a + b\n")
            agent = BuildAgent()
            task = {"id": "test_build_skill", "request": "Calculator App", "user_id": "test_user"}
            context = {"workspace": ws}

            res = asyncio.run(agent.execute(task, context))

            self.assertIn("skills_used", res)
            self.assertIn("systematic-debugging", res["skills_used"])
            self.assertEqual(res.get("skill_applied", {}).get("name"), "systematic-debugging")

    def test_07_testing_agent_records_skill(self):
        with tempfile.TemporaryDirectory() as td:
            ws = WorkspaceManager(workspace_root=Path(td), user_id="test_user", mission_id="test_test_skill")
            ws.write_file("app.py", "def add(a, b):\n    return a + b\n")
            ws.write_file("tests/test_app.py", "import unittest\nfrom app import add\nclass TestApp(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n")
            agent = TestingAgent()
            task = {"id": "test_test_skill", "request": "Calculator App", "user_id": "test_user"}
            context = {"workspace": ws}

            res = asyncio.run(agent.execute(task, context))

            self.assertIn("skills_used", res)
            self.assertIn("verification-before-completion", res["skills_used"])
            self.assertEqual(res.get("skill_applied", {}).get("name"), "verification-before-completion")
            self.assertTrue(res.get("success"))

    def test_08_api_skills_endpoint(self):
        res = self.client.get("/api/skills")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["source"], "https://www.skills.sh/")
        self.assertIn("mappings", data)
        self.assertEqual(data["mappings"]["Planning Agent"], "writing-plans")
        self.assertEqual(data["mappings"]["Coding Agent"], "frontend-design")
        self.assertEqual(data["mappings"]["Build Agent"], "systematic-debugging")
        self.assertEqual(data["mappings"]["Testing Agent"], "verification-before-completion")
        self.assertGreaterEqual(len(data["skills"]), 4)


if __name__ == "__main__":
    unittest.main()
