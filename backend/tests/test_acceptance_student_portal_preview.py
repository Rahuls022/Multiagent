import asyncio
import os
import unittest
import urllib.request
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient

from app.agents.planning_agent import PlanningAgent
from app.agents.coding_agent import CodingAgent
from app.agents.build_agent import BuildAgent
from app.agents.testing_agent import TestingAgent
from app.tools.workspace import WorkspaceManager
from app.tools.preview_manager import PreviewManager
from app.database.repository import SQLitePipelineRepository
from main import app


class TestAcceptanceStudentPortalPreview(unittest.TestCase):
    """
    Acceptance test for Live Website Preview feature:
    Mission: 'Build a Student Management Portal with a login page, dashboard, student registration form, student list, search, and responsive navigation.'
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        os.environ["WORKSPACE_ROOT"] = self.workspace_root
        self.user_id = "test_user_acceptance"
        self.mission_id = "mission_student_portal_acceptance"
        self.repo = SQLitePipelineRepository(db_path=os.path.join(self.workspace_root, "test_repo.db"))
        self.preview_mgr = PreviewManager()
        app.state.pipeline_repository = self.repo
        self.client = TestClient(app)

    def tearDown(self):
        self.preview_mgr.stop_preview(self.mission_id)
        import time
        time.sleep(0.3)
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_end_to_end_student_portal_live_preview_acceptance(self):
        """
        End-to-End Acceptance Test verifying all 10 criteria:
        1. Launch mission
        2. Planning Agent prepares plan
        3. Coding Agent generates actual application
        4. Build Agent validates files
        5. Preview server starts automatically
        6. Live Preview displays generated website (HTTP 200)
        7. User can navigate generated pages (login, dashboard, registration form, student list, search)
        8. Files API returns actual project structure
        9. Code API returns actual source code
        10. Preview error and stop state handling
        """
        request_text = (
            "Build a Student Management Portal with a login page, dashboard, "
            "student registration form, student list, search, and responsive navigation."
        )
        task = {
            "id": self.mission_id,
            "request": request_text,
            "user_id": self.user_id,
        }

        # 1. Initialize mission workspace
        workspace = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id=self.user_id,
            mission_id=self.mission_id,
        )
        context = {
            "workspace": workspace,
            "task": task,
        }

        # 2. Planning Agent
        planning_agent = PlanningAgent()
        plan_stage = asyncio.run(planning_agent.run(task, context))
        self.assertEqual(plan_stage["status"], "completed")
        plan_output = plan_stage["output"]
        self.assertTrue(len(plan_output.get("implementation_steps", [])) > 0)
        context["Planning Agent"] = plan_stage

        # 3. Coding Agent
        coding_agent = CodingAgent()
        coding_stage = asyncio.run(coding_agent.run(task, context))
        self.assertEqual(coding_stage["status"], "completed")
        context["Coding Agent"] = coding_stage

        # Verify files generated in workspace
        self.assertTrue(workspace.path_exists("index.html"))
        self.assertTrue(workspace.path_exists("styles.css"))
        self.assertTrue(workspace.path_exists("app.js"))
        self.assertTrue(workspace.path_exists("app.py"))
        self.assertTrue(workspace.path_exists("tests/test_app.py"))

        # Verify frontend contents match mission requirements
        html_content = workspace.read_file("index.html")
        self.assertIn("Student Management Portal", html_content)
        self.assertIn("Dashboard", html_content)
        self.assertIn("Register Student", html_content)
        self.assertIn("Search", html_content)
        self.assertIn("Login", html_content)

        # 4. Build Agent
        build_agent = BuildAgent()
        build_stage = asyncio.run(build_agent.run(task, context))
        self.assertEqual(build_stage["status"], "completed")
        build_output = build_stage["output"]
        self.assertEqual(build_output["syntax_check"], "PASSED")
        self.assertTrue(build_output["total_loc"] > 50)
        context["Build Agent"] = build_stage

        # 5. Verify Preview Server was started by Build Agent
        web_preview = build_output.get("web_preview")
        self.assertIsNotNone(web_preview)
        self.assertIn(web_preview["status"], ("ready", "running"))
        self.assertTrue(web_preview["ready"])
        preview_url = web_preview["url"]
        self.assertTrue(preview_url.startswith("http://127.0.0.1:"))

        # 6. Real Website Rendering (HTTP probe against actual running preview server)
        req = urllib.request.Request(preview_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            served_body = resp.read().decode("utf-8")
            # 7. Navigation & interactive components present
            self.assertIn("Student Management Portal", served_body)
            self.assertIn("registration", served_body.lower())
            self.assertIn("search", served_body.lower())
            self.assertIn("login", served_body.lower())

        # 8. Test Files API (GET /api/pipelines/{pipeline_id}/preview/files)
        files_res = self.client.get(f"/api/pipelines/{self.mission_id}/preview/files")
        self.assertEqual(files_res.status_code, 200)
        files_data = files_res.json()
        self.assertEqual(files_data["pipeline_id"], self.mission_id)
        file_paths = [f["path"] for f in files_data["files"]]
        self.assertIn("index.html", file_paths)
        self.assertIn("styles.css", file_paths)
        self.assertIn("app.js", file_paths)
        self.assertIn("app.py", file_paths)
        # Check categories
        self.assertIn("frontend", files_data["categories"])
        self.assertIn("backend", files_data["categories"])

        # 9. Test Source Code API (GET /api/pipelines/{pipeline_id}/preview/file?path=index.html)
        file_res = self.client.get(f"/api/pipelines/{self.mission_id}/preview/file?path=index.html")
        self.assertEqual(file_res.status_code, 200)
        file_data = file_res.json()
        self.assertEqual(file_data["path"], "index.html")
        self.assertIn(file_data["extension"], ("html", ".html"))
        self.assertTrue(file_data["lines_count"] > 10)
        self.assertIn("<!DOCTYPE html>", file_data["content"])

        # Path traversal security check
        traversal_res = self.client.get(f"/api/pipelines/{self.mission_id}/preview/file?path=../../etc/passwd")
        self.assertEqual(traversal_res.status_code, 403)

        # 10. Status API & Logs API
        status_res = self.client.get(f"/api/pipelines/{self.mission_id}/preview/status")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertIn(status_data["status"], ("ready", "running"))
        self.assertTrue(status_data["ready"])

        logs_res = self.client.get(f"/api/pipelines/{self.mission_id}/preview/logs")
        self.assertEqual(logs_res.status_code, 200)
        logs_data = logs_res.json()
        self.assertTrue(isinstance(logs_data["logs"], list))

        # Test Stop API
        stop_res = self.client.post(f"/api/pipelines/{self.mission_id}/preview/stop")
        self.assertEqual(stop_res.status_code, 200)
        self.assertEqual(stop_res.json()["status"], "stopped")

        # Confirm stopped
        status_after_stop = self.client.get(f"/api/pipelines/{self.mission_id}/preview/status")
        self.assertEqual(status_after_stop.json()["status"], "stopped")

        # 11. Run Testing Agent to ensure whole DevOps swarm pipeline succeeds
        testing_agent = TestingAgent()
        test_stage = asyncio.run(testing_agent.run(task, context))
        self.assertEqual(test_stage["status"], "completed")


if __name__ == "__main__":
    unittest.main()
