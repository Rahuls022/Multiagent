"""Integration tests for FastAPI preview endpoints and preview repository integration."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from app.tools.workspace import WorkspaceManager
from app.tools.preview_manager import PreviewManager


class TestPreviewAPI(unittest.TestCase):
    def setUp(self):
        from app.database.repository import SQLitePipelineRepository
        self.repo = SQLitePipelineRepository("devops_swarm.db")
        app.state.pipeline_repository = self.repo
        self.client = TestClient(app)
        self.preview_mgr = PreviewManager()
        self.preview_mgr.stop_all()

    def tearDown(self):
        self.preview_mgr.stop_all()

    def _create_mock_mission(self, mission_id="test-mission-api-1"):
        workspace = WorkspaceManager(mission_id=mission_id)
        workspace.write_file("index.html", "<!DOCTYPE html><html><body><h1>API Student Portal</h1></body></html>")
        workspace.write_file("styles.css", "body { background: #000; color: #fff; }")
        workspace.write_file("app.py", "def main(): print('backend')")
        return workspace

    def test_preview_lifecycle_apis(self):
        mission_id = "test-mission-api-1"
        ws = self._create_mock_mission(mission_id)

        # 1. List files in workspace
        res = self.client.get(f"/api/pipelines/{mission_id}/preview/files")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("files", data)
        file_paths = [f["path"] for f in data["files"]]
        self.assertIn("index.html", file_paths)
        self.assertIn("styles.css", file_paths)
        self.assertIn("app.py", file_paths)

        # 2. Read file content
        res = self.client.get(f"/api/pipelines/{mission_id}/preview/file?path=index.html")
        self.assertEqual(res.status_code, 200)
        file_data = res.json()
        self.assertEqual(file_data["path"], "index.html")
        self.assertIn("API Student Portal", file_data["content"])
        self.assertEqual(file_data["language"], "html")

        # 3. Path traversal attack rejected
        res = self.client.get(f"/api/pipelines/{mission_id}/preview/file?path=../../etc/passwd")
        self.assertEqual(res.status_code, 403)

        # 4. Start preview
        res = self.client.post(f"/api/pipelines/{mission_id}/preview/start")
        self.assertEqual(res.status_code, 200)
        start_data = res.json()
        self.assertEqual(start_data["status"], "running")
        self.assertTrue(start_data["preview_url"].startswith("http://127.0.0.1:"))
        self.assertIsNotNone(start_data["port"])

        # 5. Get preview status
        res = self.client.get(f"/api/pipelines/{mission_id}/preview/status")
        self.assertEqual(res.status_code, 200)
        status_data = res.json()
        self.assertEqual(status_data["status"], "running")
        self.assertEqual(status_data["preview_url"], start_data["preview_url"])

        # 6. Get preview logs
        res = self.client.get(f"/api/pipelines/{mission_id}/preview/logs")
        self.assertEqual(res.status_code, 200)
        logs_data = res.json()
        self.assertIn("logs", logs_data)

        # 7. Stop preview
        res = self.client.post(f"/api/pipelines/{mission_id}/preview/stop")
        self.assertEqual(res.status_code, 200)
        stop_data = res.json()
        self.assertEqual(stop_data["status"], "stopped")

        # Verify status is stopped
        res = self.client.get(f"/api/pipelines/{mission_id}/preview/status")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
