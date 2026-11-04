"""Regression & acceptance tests verifying strict mission isolation and domain-specific code generation.

Verifies:
1. Mission 1: Student Management Portal produces student directory, GPA, and academic analytics.
2. Mission 2: E-Commerce Website produces product catalog, shopping cart, and checkout with ZERO academic/GPA leaks.
3. Workspaces are strictly isolated in separate directories on disk.
4. Preview servers run on distinct, allocated ports and serve their respective domain contents over HTTP.
5. Generated unit tests in both workspaces run cleanly and pass 100%.
"""

import asyncio
import os
import re
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from fastapi.testclient import TestClient

from app.agents.coding_agent import CodingAgent
from app.agents.build_agent import BuildAgent
from app.agents.testing_agent import TestingAgent
from app.agents.planning_agent import PlanningAgent
from app.database.repository import SQLitePipelineRepository
from app.tools.preview_manager import PreviewManager
from app.tools.workspace import WorkspaceManager
from main import app


class TestMissionIsolationAndDomainGeneration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        os.environ["WORKSPACE_ROOT"] = self.workspace_root
        self.user_id = "test_user_isolation"
        self.repo = SQLitePipelineRepository(db_path=os.path.join(self.workspace_root, "test_repo.db"))
        app.state.pipeline_repository = self.repo
        self.client = TestClient(app)
        self.preview_mgr = PreviewManager()
        self.active_missions = []

    def tearDown(self):
        for m_id in self.active_missions:
            try:
                self.preview_mgr.stop_preview(m_id)
            except Exception:
                pass
        time.sleep(0.3)
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_sequential_missions_have_strict_isolation_and_no_content_leak(self):
        """Sequential test running Mission A (Student) then Mission B (E-Commerce)."""

        # -------------------------------------------------------------
        # MISSION A: Student Management Portal
        # -------------------------------------------------------------
        mission_a_id = "mission_student_portal_001"
        self.active_missions.append(mission_a_id)
        request_a = "Build a Student Management Portal with student registration, academic departments, and GPA tracking."
        task_a = {"id": mission_a_id, "request": request_a, "user_id": self.user_id}

        workspace_a = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id=self.user_id,
            mission_id=mission_a_id,
        )
        context_a = {"workspace": workspace_a, "task": task_a}

        planning_agent = PlanningAgent()
        plan_a = asyncio.run(planning_agent.run(task_a, context_a))
        context_a["Planning Agent"] = plan_a

        coding_agent = CodingAgent()
        coding_a = asyncio.run(coding_agent.run(task_a, context_a))
        self.assertEqual(coding_a["status"], "completed")
        context_a["Coding Agent"] = coding_a

        # Verify files generated for Mission A
        self.assertTrue(workspace_a.path_exists("index.html"))
        self.assertTrue(workspace_a.path_exists("app.js"))
        self.assertTrue(workspace_a.path_exists("styles.css"))
        self.assertTrue(workspace_a.path_exists("app.py"))
        self.assertTrue(workspace_a.path_exists("tests/test_app.py"))

        html_a = workspace_a.read_file("index.html")
        js_a = workspace_a.read_file("app.js")

        self.assertIn("student", html_a.lower())
        self.assertIn("gpa", html_a.lower())
        self.assertIn("department", html_a.lower())

        # Build Agent for Mission A -> Starts preview server
        build_agent = BuildAgent()
        build_a = asyncio.run(build_agent.run(task_a, context_a))
        self.assertEqual(build_a["status"], "completed")
        web_preview_a = build_a["output"]["web_preview"]
        self.assertTrue(web_preview_a["ready"])
        port_a = web_preview_a["port"]
        url_a = web_preview_a["url"]

        # HTTP GET Mission A
        req_a = urllib.request.Request(url_a, headers={"User-Agent": "Swarm-Test"})
        with urllib.request.urlopen(req_a, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            body_a = resp.read().decode("utf-8")
            self.assertIn("student", body_a.lower())
            self.assertIn("gpa", body_a.lower())

        # -------------------------------------------------------------
        # MISSION B: E-Commerce Website
        # -------------------------------------------------------------
        mission_b_id = "mission_ecommerce_store_002"
        self.active_missions.append(mission_b_id)
        request_b = "Build an E-Commerce Website with product catalog, shopping cart, and secure checkout."
        task_b = {"id": mission_b_id, "request": request_b, "user_id": self.user_id}

        workspace_b = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id=self.user_id,
            mission_id=mission_b_id,
        )
        context_b = {"workspace": workspace_b, "task": task_b}

        plan_b = asyncio.run(planning_agent.run(task_b, context_b))
        context_b["Planning Agent"] = plan_b

        coding_b = asyncio.run(coding_agent.run(task_b, context_b))
        self.assertEqual(coding_b["status"], "completed")
        context_b["Coding Agent"] = coding_b

        # 1. STRICT WORKSPACE ISOLATION CHECK
        self.assertNotEqual(str(workspace_a.root_path), str(workspace_b.root_path))
        self.assertTrue(workspace_b.path_exists("index.html"))
        self.assertTrue(workspace_b.path_exists("app.js"))
        self.assertTrue(workspace_b.path_exists("styles.css"))
        self.assertTrue(workspace_b.path_exists("app.py"))
        self.assertTrue(workspace_b.path_exists("tests/test_app.py"))

        html_b = workspace_b.read_file("index.html")
        js_b = workspace_b.read_file("app.js")

        # 2. E-COMMERCE DOMAIN CONTENT CHECKS
        self.assertIn("product", html_b.lower())
        self.assertIn("cart", html_b.lower())
        self.assertIn("checkout", html_b.lower())
        self.assertIn("order", html_b.lower())

        self.assertIn("cart", js_b.lower())
        self.assertIn("products", js_b.lower())
        self.assertIn("order", js_b.lower())

        # 3. ZERO ACADEMIC / STUDENT LEAKAGE CHECKS
        prohibited_terms = [
            "gpa",
            "academic departments",
            "dean miller",
            "defaultstudents",
            "dean's honor roll",
            "academic cohort",
            "student code",
            "student directory",
            "register student",
        ]
        for term in prohibited_terms:
            self.assertNotIn(term, html_b.lower(), f"E-Commerce HTML leaked student term '{term}'")
            self.assertNotIn(term, js_b.lower(), f"E-Commerce JS leaked student term '{term}'")

        # Build Agent for Mission B -> Starts preview server on distinct port
        build_b = asyncio.run(build_agent.run(task_b, context_b))
        self.assertEqual(build_b["status"], "completed")
        web_preview_b = build_b["output"]["web_preview"]
        self.assertTrue(web_preview_b["ready"])
        port_b = web_preview_b["port"]
        url_b = web_preview_b["url"]

        # 4. PREVIEW PORT ISOLATION
        self.assertNotEqual(port_a, port_b, "Missions must have isolated preview server ports")

        # HTTP GET Mission B
        req_b = urllib.request.Request(url_b, headers={"User-Agent": "Swarm-Test"})
        with urllib.request.urlopen(req_b, timeout=5.0) as resp_b:
            self.assertEqual(resp_b.status, 200)
            body_b = resp_b.read().decode("utf-8")
            self.assertIn("cart", body_b.lower())
            self.assertIn("product", body_b.lower())
            for term in prohibited_terms:
                self.assertNotIn(term, body_b.lower(), f"HTTP Response for Mission B leaked '{term}'")

        # 5. TESTING AGENT VERIFICATION IN BOTH WORKSPACES
        testing_agent = TestingAgent()
        context_a["Build Agent"] = build_a
        test_res_a = asyncio.run(testing_agent.run(task_a, context_a))
        self.assertEqual(test_res_a["status"], "completed")
        self.assertTrue(test_res_a["output"]["success"])
        self.assertEqual(test_res_a["output"]["failed"], 0)
        self.assertGreaterEqual(test_res_a["output"]["passed"], 1)

        context_b["Build Agent"] = build_b
        test_res_b = asyncio.run(testing_agent.run(task_b, context_b))
        self.assertEqual(test_res_b["status"], "completed")
        self.assertTrue(test_res_b["output"]["success"])
        self.assertEqual(test_res_b["output"]["failed"], 0)
        self.assertGreaterEqual(test_res_b["output"]["passed"], 1)
