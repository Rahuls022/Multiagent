import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure backend is on sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import asyncio
from starlette.testclient import TestClient

from app.agents.coding_agent import CodingAgent
from app.agents.nvidia_client import NvidiaNimClient
from app.agents.planning_agent import PlanningAgent
from app.database import InMemoryPipelineRepository, SqliteUserRepository
from app.workspace import WorkspaceManager, WorkspaceSecurityError, set_workspace_manager
from main import app


class StubClient(NvidiaNimClient):
    def __init__(self) -> None:
        self.api_key = ""

    @property
    def is_configured(self) -> bool:
        return False


class CodingAgentWorkspaceTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create temp workspace root and db for test isolation
        cls.temp_ws_dir = tempfile.mkdtemp(prefix="ws_test_")
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(cls.temp_db_fd)

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.temp_ws_dir):
            shutil.rmtree(cls.temp_ws_dir, ignore_errors=True)
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except OSError:
                pass

    def setUp(self):
        self.workspace_mgr = WorkspaceManager(root_dir=self.temp_ws_dir)
        set_workspace_manager(self.workspace_mgr)
        self.user_repo = SqliteUserRepository(self.temp_db_path)
        self.pipeline_repo = InMemoryPipelineRepository()
        app.state.user_repository = self.user_repo
        app.state.pipeline_repository = self.pipeline_repo
        self.client = TestClient(app)

        # Register User A
        self.user_a_res = self.client.post("/api/auth/signup", json={
            "full_name": "Developer Alpha",
            "email": "alpha@swarm.dev",
            "password": "Password123!",
            "confirm_password": "Password123!",
        })
        if self.user_a_res.status_code == 201:
            self.token_a = self.user_a_res.json()["access_token"]
            self.user_a_id = self.user_a_res.json()["user"]["id"]
        else:
            login_a = self.client.post("/api/auth/login", json={"email": "alpha@swarm.dev", "password": "Password123!"})
            self.token_a = login_a.json()["access_token"]
            self.user_a_id = login_a.json()["user"]["id"]

        # Register User B
        self.user_b_res = self.client.post("/api/auth/signup", json={
            "full_name": "Developer Beta",
            "email": "beta@swarm.dev",
            "password": "Password123!",
            "confirm_password": "Password123!",
        })
        if self.user_b_res.status_code == 201:
            self.token_b = self.user_b_res.json()["access_token"]
            self.user_b_id = self.user_b_res.json()["user"]["id"]
        else:
            login_b = self.client.post("/api/auth/login", json={"email": "beta@swarm.dev", "password": "Password123!"})
            self.token_b = login_b.json()["access_token"]
            self.user_b_id = login_b.json()["user"]["id"]

    def test_01_generate_new_react_application(self):
        """Test 1: Coding Agent generates real React files on disk."""
        agent = CodingAgent(client=StubClient(), workspace_manager=self.workspace_mgr)
        task = {
            "id": "task_react_01",
            "request": "Build a modern e-commerce website with React",
            "user_id": self.user_a_id,
            "project_id": "ecommerce_react",
        }
        context = {
            "Planning Agent": {
                "output": {
                    "summary": "E-Commerce React Plan",
                    "project": {"name": "E-Commerce Shop", "feature_slug": "orders"},
                }
            }
        }

        result = asyncio.run(agent.execute(task, context))
        self.assertIn("files_to_create", result)
        self.assertGreater(len(result["files_to_create"]), 4)

        # Verify real files exist on physical disk
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "ecommerce_react")
        self.assertTrue((proj_dir / "package.json").exists())
        self.assertTrue((proj_dir / "src/App.jsx").exists())
        self.assertTrue((proj_dir / "src/main.jsx").exists())
        self.assertTrue((proj_dir / "index.html").exists())
        self.assertTrue((proj_dir / "README.md").exists())

        # Check content is real React code
        app_code = (proj_dir / "src/App.jsx").read_text(encoding="utf-8")
        self.assertIn("import React", app_code)
        self.assertIn("export default function App", app_code)

    def test_02_generate_simple_python_application(self):
        """Test 2: Coding Agent generates real Python files on disk."""
        agent = CodingAgent(client=StubClient(), workspace_manager=self.workspace_mgr)
        task = {
            "id": "task_py_01",
            "request": "Build a simple Python CLI calculator application",
            "user_id": self.user_a_id,
            "project_id": "calculator_py",
        }
        context = {
            "Planning Agent": {
                "output": {
                    "summary": "Calculator Plan",
                    "project": {"name": "CLI Calculator", "feature_slug": "calculator"},
                }
            }
        }

        result = asyncio.run(agent.execute(task, context))
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "calculator_py")

        self.assertTrue((proj_dir / "main.py").exists())
        self.assertTrue((proj_dir / "app/core.py").exists())
        self.assertTrue((proj_dir / "tests/test_core.py").exists())

        main_code = (proj_dir / "main.py").read_text(encoding="utf-8")
        self.assertIn("def main()", main_code)

    def test_03_generate_project_with_multiple_folders(self):
        """Test 3: Coding Agent scaffolds multi-tier directory hierarchies."""
        agent = CodingAgent(client=StubClient(), workspace_manager=self.workspace_mgr)
        task = {
            "id": "task_multi_01",
            "request": "Build a student management portal with database and backend",
            "user_id": self.user_a_id,
            "project_id": "student_portal",
        }
        context = {
            "Planning Agent": {
                "output": {
                    "summary": "Student Portal Plan",
                    "project": {"name": "Student Portal", "feature_slug": "students"},
                }
            }
        }

        result = asyncio.run(agent.execute(task, context))
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "student_portal")

        self.assertTrue((proj_dir / "backend/main.py").exists())
        self.assertTrue((proj_dir / "backend/app/schemas.py").exists())
        self.assertTrue((proj_dir / "database/schema.sql").exists())
        self.assertTrue((proj_dir / "tests/test_api.py").exists())

    def test_04_modify_existing_source_file_and_preserve_unrelated(self):
        """Test 4 & 5: Modifying an existing file updates it while preserving unrelated files."""
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "ecommerce_react")
        if not (proj_dir / "package.json").exists():
            self.test_01_generate_new_react_application()

        app_file = proj_dir / "src/App.jsx"
        package_file = proj_dir / "package.json"

        original_pkg_code = package_file.read_text(encoding="utf-8")
        original_app_code = app_file.read_text(encoding="utf-8")

        agent = CodingAgent(client=StubClient(), workspace_manager=self.workspace_mgr)
        task = {
            "id": "task_mod_01",
            "request": "Modify src/App.jsx to add a shopping cart badge",
            "user_id": self.user_a_id,
            "project_id": "ecommerce_react",
        }
        context = {
            "Planning Agent": {
                "output": {
                    "summary": "Add Cart Badge",
                    "project": {"name": "E-Commerce", "feature_slug": "ecommerce_react"},
                }
            }
        }

        result = asyncio.run(agent.execute(task, context))
        self.assertIn("src/App.jsx", result["files_modified"])

        # Check App.jsx was updated
        updated_app_code = app_file.read_text(encoding="utf-8")
        self.assertNotEqual(original_app_code, updated_app_code)
        self.assertIn("Feature Update", updated_app_code)

        # Check package.json remains COMPLETELY UNCHANGED
        self.assertEqual(original_pkg_code, package_file.read_text(encoding="utf-8"))

    def test_06_read_and_update_files_through_api(self):
        """Test 6: User can list, read, and update workspace files via REST endpoints."""
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "ecommerce_react")
        if not (proj_dir / "package.json").exists():
            self.test_01_generate_new_react_application()

        # List files via API
        list_res = self.client.get(
            "/api/workspace/files?project_id=ecommerce_react",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(list_res.status_code, 200)
        file_paths = [f["path"] for f in list_res.json()["files"]]
        self.assertIn("package.json", file_paths)
        self.assertIn("src/App.jsx", file_paths)

        # Read specific file via API
        read_res = self.client.get(
            "/api/workspace/file?project_id=ecommerce_react&path=package.json",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(read_res.status_code, 200)
        self.assertIn("dependencies", read_res.json()["content"])

        # Update file via API
        update_res = self.client.put(
            "/api/workspace/file",
            headers={"Authorization": f"Bearer {self.token_a}"},
            json={
                "project_id": "ecommerce_react",
                "path": "src/config.js",
                "content": "export const API_URL = 'http://api.swarm.dev';",
            },
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["status"], "created")

        # Verify it exists on disk
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "ecommerce_react")
        self.assertTrue((proj_dir / "src/config.js").exists())

    def test_07_persistence_after_backend_restart(self):
        """Test 7: Files remain permanently available across new WorkspaceManager instances."""
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, "ecommerce_react")
        if not (proj_dir / "package.json").exists():
            self.test_01_generate_new_react_application()

        new_mgr = WorkspaceManager(root_dir=self.temp_ws_dir)
        files = new_mgr.list_files(self.user_a_id, "ecommerce_react")
        paths = [f["path"] for f in files]
        self.assertIn("src/App.jsx", paths)
        self.assertIn("package.json", paths)

    def test_08_user_workspace_isolation(self):
        """Test 8: User B cannot access or modify User A's project files."""
        set_workspace_manager(self.workspace_mgr)

        # User B tries to read User A's file in User B's workspace context
        # (Since User B doesn't have ecommerce_react, it should return 404)
        res = self.client.get(
            "/api/workspace/file?project_id=ecommerce_react&path=package.json",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(res.status_code, 404)

    def test_09_path_traversal_prevention(self):
        """Test 9: Path traversal attacks (../) and forbidden files (.env) are blocked."""
        # Direct manager check
        with self.assertRaises(WorkspaceSecurityError):
            self.workspace_mgr.resolve_safe_path(self.user_a_id, "test_proj", "../../etc/passwd")

        with self.assertRaises(WorkspaceSecurityError):
            self.workspace_mgr.resolve_safe_path(self.user_a_id, "test_proj", ".env")

        # API check
        set_workspace_manager(self.workspace_mgr)

        api_res = self.client.get(
            "/api/workspace/file?project_id=ecommerce_react&path=../../etc/passwd",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(api_res.status_code, 400)

    def test_10_directory_creation_on_demand(self):
        """Test 10: Reads, safe path resolution, and listings do not create directories; writes do."""
        non_existent_proj = "ghost_project"
        proj_dir = self.workspace_mgr.get_project_dir(self.user_a_id, non_existent_proj)
        self.assertFalse(proj_dir.exists())

        # resolve_safe_path should not create directory
        target = self.workspace_mgr.resolve_safe_path(self.user_a_id, non_existent_proj, "test.txt")
        self.assertFalse(proj_dir.exists())

        # list_files should not create directory
        files = self.workspace_mgr.list_files(self.user_a_id, non_existent_proj)
        self.assertEqual(files, [])
        self.assertFalse(proj_dir.exists())

        # get_structure should not create directory
        structure = self.workspace_mgr.get_structure(self.user_a_id, non_existent_proj)
        self.assertEqual(structure["total_files"], 0)
        self.assertEqual(structure["root"]["children"], [])
        self.assertFalse(proj_dir.exists())

        # write_file SHOULD create directory
        self.workspace_mgr.write_file(self.user_a_id, non_existent_proj, "test.txt", "hello")
        self.assertTrue(proj_dir.exists())
        self.assertTrue((proj_dir / "test.txt").exists())

    def test_11_project_security_and_non_absolute_path_exposure(self):
        """Test 11: Workspace project endpoints catch WorkspaceSecurityError and do not expose absolute paths."""
        set_workspace_manager(self.workspace_mgr)

        # 1. create_workspace_project rejects forbidden project_id
        res_create_err = self.client.post(
            "/api/workspace/projects",
            headers={"Authorization": f"Bearer {self.token_a}"},
            json={"project_id": ".env"},
        )
        self.assertEqual(res_create_err.status_code, 400)

        # 2. create_workspace_project succeeds with valid project_id and returns relative path
        res_create_ok = self.client.post(
            "/api/workspace/projects",
            headers={"Authorization": f"Bearer {self.token_a}"},
            json={"project_id": "valid_proj"},
        )
        self.assertEqual(res_create_ok.status_code, 200)
        data = res_create_ok.json()
        self.assertIn("path", data)
        # Verify path is relative, not exposing absolute drive/filesystem path
        self.assertFalse(os.path.isabs(data["path"]))
        self.assertNotIn(":\\", data["path"])

        # 3. list_workspace_files rejects forbidden project_id
        res_list_err = self.client.get(
            "/api/workspace/files?project_id=.env",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(res_list_err.status_code, 400)

        # 4. get_workspace_structure rejects forbidden project_id
        res_struct_err = self.client.get(
            "/api/workspace/structure?project_id=.env",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(res_struct_err.status_code, 400)


if __name__ == "__main__":
    unittest.main()
