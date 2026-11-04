"""Tests for PreviewManager: process lifecycle, port allocation, framework detection, and security."""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from app.tools.preview_manager import PreviewManager
from app.tools.workspace import WorkspaceManager


class TestPreviewManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="preview_test_")
        self.workspace_root = Path(self.temp_dir) / "workspaces"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.user_id = "test_user"
        self.mission_id = "test_mission_001"
        self.workspace = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id=self.user_id,
            mission_id=self.mission_id,
        )
        self.preview_mgr = PreviewManager()

    def tearDown(self):
        self.preview_mgr.stop_all()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_allocate_available_port(self):
        port = self.preview_mgr.allocate_port()
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 9100)
        self.assertLess(port, 9999)

    def test_detect_static_html_framework(self):
        # Create an index.html in the workspace
        self.workspace.write_file("index.html", "<!DOCTYPE html><html><body><h1>Hello World</h1></body></html>")
        detection = self.preview_mgr.detect_frontend(self.workspace.root_path)
        self.assertEqual(detection["framework"], "HTML5 / SPA")
        self.assertEqual(detection["entry_point"], "index.html")

    def test_detect_nested_frontend_framework(self):
        # Create a frontend/index.html
        self.workspace.write_file("frontend/index.html", "<!DOCTYPE html><html><body><h1>Portal</h1></body></html>")
        detection = self.preview_mgr.detect_frontend(self.workspace.root_path)
        self.assertEqual(detection["framework"], "HTML5 / SPA")
        self.assertIn("index.html", detection["entry_point"])

    def test_start_and_stop_static_preview_server(self):
        sample_html = "<!DOCTYPE html><html><head><title>Student Portal</title></head><body><h1>Student Management Portal</h1></body></html>"
        self.workspace.write_file("index.html", sample_html)

        result = self.preview_mgr.start_preview(
            mission_id=self.mission_id,
            workspace_dir=self.workspace.root_path,
            user_id=self.user_id,
        )

        self.assertEqual(result["status"], "running")
        self.assertTrue(result["preview_url"].startswith("http://127.0.0.1:"))
        self.assertIsNotNone(result["port"])
        self.assertIsNotNone(result["pid"])

        # Verify HTTP GET returns the content
        import urllib.request
        with urllib.request.urlopen(result["preview_url"], timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8")
            self.assertIn("Student Management Portal", body)

        # Check status API
        status = self.preview_mgr.get_status(self.mission_id)
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["port"], result["port"])

        # Stop preview
        stop_res = self.preview_mgr.stop_preview(self.mission_id)
        self.assertEqual(stop_res["status"], "stopped")

        # Verify it is no longer running
        status_after = self.preview_mgr.get_status(self.mission_id)
        self.assertEqual(status_after["status"], "stopped")

    def test_prevent_duplicate_preview_servers(self):
        self.workspace.write_file("index.html", "<h1>App</h1>")
        res1 = self.preview_mgr.start_preview(self.mission_id, self.workspace.root_path, self.user_id)
        res2 = self.preview_mgr.start_preview(self.mission_id, self.workspace.root_path, self.user_id)

        # Both should report running and have the exact same port and pid
        self.assertEqual(res1["port"], res2["port"])
        self.assertEqual(res1["pid"], res2["pid"])

    def test_list_and_read_workspace_files_securely(self):
        self.workspace.write_file("frontend/src/App.jsx", "export default function App() {}")
        self.workspace.write_file("backend/app.py", "def main(): pass")
        self.workspace.write_file("package.json", '{"name": "test"}')

        files = self.preview_mgr.list_workspace_files(self.workspace.root_path)
        paths = [f["path"] for f in files]
        self.assertIn("frontend/src/App.jsx", paths)
        self.assertIn("backend/app.py", paths)
        self.assertIn("package.json", paths)

        # Reading valid file
        content_info = self.preview_mgr.read_workspace_file(self.workspace.root_path, "frontend/src/App.jsx")
        self.assertEqual(content_info["content"], "export default function App() {}")
        self.assertEqual(content_info["language"], "javascript")

        # Path traversal attack must be blocked
        with self.assertRaises(PermissionError):
            self.preview_mgr.read_workspace_file(self.workspace.root_path, "../../../etc/passwd")

        with self.assertRaises(PermissionError):
            self.preview_mgr.read_workspace_file(self.workspace.root_path, "..\\..\\windows\\system32")


if __name__ == "__main__":
    unittest.main()

