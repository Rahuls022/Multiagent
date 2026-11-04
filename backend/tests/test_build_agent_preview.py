"""Tests for Build Agent integration with Live Website Preview."""

import tempfile
import unittest
from pathlib import Path

from app.agents.build_agent import BuildAgent
from app.tools.preview_manager import PreviewManager
from app.tools.workspace import WorkspaceManager


class TestBuildAgentPreview(unittest.TestCase):
    def setUp(self):
        self.preview_mgr = PreviewManager()
        self.preview_mgr.stop_all()

    def tearDown(self):
        self.preview_mgr.stop_all()

    def test_build_agent_starts_preview_for_frontend_project(self):
        async def run_test():
            mission_id = "test-build-preview-1"
            workspace = WorkspaceManager(mission_id=mission_id)
            
            # Generate frontend application files
            html_code = (
                "<!DOCTYPE html>\n"
                "<html lang='en'>\n"
                "<head><title>Student Management Portal</title></head>\n"
                "<body><h1>Student Management Portal</h1><div id='app'></div></body>\n"
                "</html>"
            )
            css_code = "body { margin: 0; font-family: sans-serif; background: #0b0f19; color: #fff; }"
            js_code = "console.log('Student Portal Initialized');"
            py_code = "def get_status(): return {'status': 'healthy'}\n"

            workspace.write_file("index.html", html_code)
            workspace.write_file("styles.css", css_code)
            workspace.write_file("app.js", js_code)
            workspace.write_file("app.py", py_code)

            agent = BuildAgent()
            task = {
                "id": mission_id,
                "request": "Build a Student Management Portal",
                "user_id": "test_user",
            }
            context = {"workspace": workspace}

            result = await agent.execute(task, context)

            self.assertEqual(result["status"], "success")
            self.assertTrue(result["success"])
            self.assertIn("web_preview", result)
            preview = result["web_preview"]
            self.assertEqual(preview["status"], "running")
            self.assertTrue(preview["preview_url"].startswith("http://127.0.0.1:"))
            self.assertEqual(preview["framework"], "HTML5 / SPA")
            self.assertEqual(result["preview_status"], "ready")

        import asyncio
        asyncio.run(run_test())

    def test_build_agent_reports_error_when_python_has_syntax_error(self):
        async def run_test():
            mission_id = "test-build-preview-err"
            workspace = WorkspaceManager(mission_id=mission_id)
            workspace.write_file("app.py", "def broken_syntax( - invalid Python code")
            workspace.write_file("index.html", "<html><body>Broken App</body></html>")

            agent = BuildAgent()
            task = {
                "id": mission_id,
                "request": "Broken mission",
                "user_id": "test_user",
            }
            context = {"workspace": workspace}

            with self.assertRaises(RuntimeError) as ctx:
                await agent.execute(task, context)
            self.assertIn("BUILD_SYNTAX_ERROR", str(ctx.exception))

        import asyncio
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
