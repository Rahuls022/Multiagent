"""Unit tests for the WorkspaceManager sandbox, path confinement, and controlled tools."""

import tempfile
import unittest
from pathlib import Path

from app.tools.workspace import WorkspaceManager


class TestWorkspaceTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = WorkspaceManager(
            workspace_root=self.temp_dir.name,
            user_id="test_user",
            mission_id="mission_001",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_workspace_path_confinement_prevent_path_traversal(self):
        """Verify that any attempt to traverse outside the workspace root is rejected."""
        with self.assertRaises(PermissionError):
            self.workspace.resolve_path("../../etc/passwd")

        with self.assertRaises(PermissionError):
            self.workspace.resolve_path("..\\..\\Windows\\System32")

    def test_file_write_and_read(self):
        res = self.workspace.write_file("src/app.py", "print('hello world')\n")
        self.assertEqual(res["path"], "src/app.py")
        self.assertEqual(res["lines"], 1)
        self.assertTrue(res["created"])

        content = self.workspace.read_file("src/app.py")
        self.assertEqual(content, "print('hello world')\n")

    def test_read_nonexistent_file_raises_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.workspace.read_file("does_not_exist.py")

    def test_list_and_search_files(self):
        self.workspace.write_file("module_a.py", "def calculate_tax():\n    return 0.15\n")
        self.workspace.write_file("module_b.py", "def calculate_discount():\n    return 0.05\n")
        self.workspace.write_file("docs/readme.txt", "Project documentation.\n")

        files = self.workspace.list_files()
        file_paths = [f["path"] for f in files if not f["is_dir"]]
        self.assertIn("module_a.py", file_paths)
        self.assertIn("module_b.py", file_paths)
        self.assertIn("docs/readme.txt", file_paths)

        matches = self.workspace.search_files("calculate")
        self.assertEqual(len(matches), 2)
        match_files = [m["file"] for m in matches]
        self.assertIn("module_a.py", match_files)
        self.assertIn("module_b.py", match_files)

    def test_run_command_execution_in_workspace(self):
        self.workspace.write_file("hello.py", "print('EXEC_SUCCESS')\n")
        res = self.workspace.run_command("python hello.py", timeout_seconds=10.0)
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("EXEC_SUCCESS", res["stdout"])
        self.assertTrue(res["success"])

    def test_run_command_timeout_protection(self):
        # Run a sleep command that exceeds 1s timeout
        res = self.workspace.run_command("python -c \"import time; time.sleep(5)\"", timeout_seconds=1.0)
        self.assertEqual(res["exit_code"], -1)
        self.assertIn("timed out", res["stderr"].lower())

    def test_audit_logging(self):
        self.workspace.write_file("test.txt", "data")
        self.workspace.read_file("test.txt")
        self.assertGreaterEqual(len(self.workspace.audit_log), 2)
        actions = [log["action"] for log in self.workspace.audit_log]
        self.assertIn("write_file", actions)
        self.assertIn("read_file", actions)


if __name__ == "__main__":
    unittest.main()
