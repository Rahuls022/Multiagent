"""End-to-end unit test verifying Student Management Portal generation and preview startup."""

import asyncio
import tempfile
import unittest
import urllib.request
from pathlib import Path

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.testing_agent import TestingAgent
from app.tools.preview_manager import PreviewManager
from app.tools.workspace import WorkspaceManager


class TestStudentPortalGeneration(unittest.TestCase):
    def setUp(self):
        self.preview_mgr = PreviewManager()
        self.preview_mgr.stop_all()

    def tearDown(self):
        self.preview_mgr.stop_all()

    def test_student_portal_full_pipeline_preview(self):
        async def run_pipeline():
            mission_id = "test-student-portal-mission"
            workspace = WorkspaceManager(mission_id=mission_id)
            task = {
                "id": mission_id,
                "request": "Build a Student Management Portal with a login page, dashboard, student registration form, student list, search, and responsive navigation.",
                "user_id": "test_user",
            }
            context = {"workspace": workspace}

            # 1. Planning Agent
            planner = PlanningAgent()
            plan_output = await planner.execute(task, context)
            context["Planning Agent"] = {"output": plan_output, "status": "completed"}
            
            planned_paths = [f["path"] for f in plan_output.get("files_to_create", [])]
            self.assertTrue(any("index.html" in p for p in planned_paths), "Planner should plan index.html for web portal")

            # 2. Coding Agent
            coder = CodingAgent()
            code_output = await coder.execute(task, context)
            context["Coding Agent"] = {"output": code_output, "status": "completed"}

            # Verify files were actually written to disk in the mission workspace
            written_paths = [f["path"] for f in code_output.get("files_written", [])]
            self.assertIn("index.html", written_paths)
            self.assertIn("app.py", written_paths)
            self.assertIn("tests/test_app.py", written_paths)

            # Verify content of index.html has required elements
            html_content = workspace.read_file("index.html")
            self.assertIn("Student", html_content)
            self.assertIn("Dashboard", html_content)
            self.assertIn("Registration", html_content)
            self.assertIn("Search", html_content)

            # 3. Build Agent
            builder = BuildAgent()
            build_output = await builder.execute(task, context)
            context["Build Agent"] = {"output": build_output, "status": "completed"}

            self.assertEqual(build_output["status"], "success")
            self.assertIn("web_preview", build_output)
            self.assertEqual(build_output["preview_status"], "ready")
            preview_url = build_output["web_preview"]["preview_url"]

            # 4. HTTP Health Verification on Live Preview Server
            with urllib.request.urlopen(preview_url, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
                self.assertIn("Student Management Portal", body)

            # 5. Testing Agent
            tester = TestingAgent()
            test_output = await tester.execute(task, context)
            self.assertEqual(test_output["status"], "completed")
            self.assertEqual(test_output["failed"], 0)
            self.assertGreater(test_output["passed"], 0)

        asyncio.run(run_pipeline())


if __name__ == "__main__":
    unittest.main()

