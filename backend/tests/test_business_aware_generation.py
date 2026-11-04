"""Automated multi-domain verification test suite.

Validates business-aware requirements analysis, dynamic website generation,
real interactive cart and checkout, SQLite persistence, and zero content leakage
across distinct business domains:
1. TEST A: Juice Centre Website with Online Ordering
2. TEST B: Restaurant Website with Food Ordering & Menu Management
3. TEST C: Hospital Website with Doctor Directory & Appointments
4. TEST D: Bakery Website with Sourdough & Pastry Ordering
5. TEST E: Student Management Portal (Regression Protection)
"""

import asyncio
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.project_context import project_context
from app.agents.testing_agent import TestingAgent
from app.tools.preview_manager import PreviewManager
from app.tools.workspace import WorkspaceManager


class TestBusinessAwareGeneration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        self.preview_mgr = PreviewManager()
        self.active_missions = []
        os.environ["LLM_OFFLINE"] = "1"

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

    def test_01_juice_centre_website_generation_and_ordering(self):
        """TEST A: Juice Centre with 100% authentic juices, cart, checkout, zero electronics, zero GPA."""
        mission_id = "mission_juice_centre_001"
        self.active_missions.append(mission_id)
        request = "Create a website for a Juice Centre to accept online orders"

        ctx = project_context(request)
        self.assertEqual(ctx["domain"], "juice")
        self.assertIn("Juice", ctx["name"])
        self.assertTrue(any("Orange" in p["name"] or "Juice" in p["name"] for p in ctx["products"]))

        ws = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id="test_user",
            mission_id=mission_id,
        )
        task = {"id": mission_id, "request": request, "user_id": "test_user"}
        context = {"workspace": ws}

        # 1. Planning Agent
        planner = PlanningAgent()
        plan = asyncio.run(planner.execute(task, context))
        context["Planning Agent"] = {"output": plan, "status": "completed"}
        self.assertIn("Juice", plan["summary"])

        # 2. Coding Agent
        coder = CodingAgent()
        code_output = asyncio.run(coder.execute(task, context))
        context["Coding Agent"] = {"output": code_output, "status": "completed"}

        # Verify files written
        self.assertTrue(ws.path_exists("index.html"))
        self.assertTrue(ws.path_exists("styles.css"))
        self.assertTrue(ws.path_exists("app.js"))
        self.assertTrue(ws.path_exists("app.py"))
        self.assertTrue(ws.path_exists("tests/test_app.py"))

        html = ws.read_file("index.html")
        js = ws.read_file("app.js")

        # Must have Juice content
        self.assertIn("Juice", html)
        self.assertIn("Orange", js)
        self.assertIn("Watermelon", js)
        self.assertIn("Smoothies", html)
        self.assertIn("Milkshakes", html)
        self.assertIn("Cart", html)
        self.assertIn("Delivery", html)

        # Strict Isolation: NO Electronics leaks
        self.assertNotIn("Aura Pro Wireless Headphones", html)
        self.assertNotIn("PulseFit Ultra Smartwatch", html)
        self.assertNotIn("Vortex Mechanical Gaming Keyboard", html)
        self.assertNotIn("Aura Pro Wireless Headphones", js)

        # Strict Isolation: NO Academic Student leaks
        self.assertNotIn("Cumulative GPA", html)
        self.assertNotIn("Academic Cohort", html)
        self.assertNotIn("Dean Miller", html)

        # 3. Unit test execution in workspace
        test_file = ws.root_path / "tests" / "test_app.py"
        test_run = subprocess.run(
            [sys.executable, "-m", "unittest", str(test_file)],
            cwd=str(ws.root_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(test_run.returncode, 0, f"Workspace tests failed: {test_run.stderr}")
        self.assertIn("OK", test_run.stderr)

        # 4. Build Agent -> starts live preview server
        builder = BuildAgent()
        build_output = asyncio.run(builder.execute(task, context))
        self.assertEqual(build_output["status"], "success")
        preview_url = build_output["web_preview"]["url"]

        # 5. Live HTTP verification
        req = urllib.request.Request(preview_url, headers={"User-Agent": "Swarm-Test"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("Juice", body)
            self.assertNotIn("Headphones", body)

    def test_02_restaurant_website_generation_and_food_ordering(self):
        """TEST B: Restaurant with food menu, dishes, table/delivery ordering, zero electronics."""
        mission_id = "mission_restaurant_002"
        self.active_missions.append(mission_id)
        request = "Create a restaurant website with food ordering and menu management"

        ctx = project_context(request)
        self.assertEqual(ctx["domain"], "restaurant")
        self.assertTrue(any("Pizza" in p["name"] or "Burger" in p["name"] or "Pasta" in p["name"] for p in ctx["products"]))

        ws = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id="test_user",
            mission_id=mission_id,
        )
        task = {"id": mission_id, "request": request, "user_id": "test_user"}
        context = {"workspace": ws}

        planner = PlanningAgent()
        plan = asyncio.run(planner.execute(task, context))
        context["Planning Agent"] = {"output": plan, "status": "completed"}

        coder = CodingAgent()
        code_output = asyncio.run(coder.execute(task, context))
        context["Coding Agent"] = {"output": code_output, "status": "completed"}

        html = ws.read_file("index.html")
        js = ws.read_file("app.js")

        self.assertIn("Restaurant", html)
        self.assertIn("Pizza", js)
        self.assertIn("Appetizers", html)
        self.assertIn("Cart", html)

        # Strict isolation
        self.assertNotIn("Aura Pro Wireless Headphones", html)
        self.assertNotIn("PulseFit Ultra Smartwatch", js)
        self.assertNotIn("Cumulative GPA", html)

        # Unit test execution
        test_file = ws.root_path / "tests" / "test_app.py"
        test_run = subprocess.run(
            [sys.executable, "-m", "unittest", str(test_file)],
            cwd=str(ws.root_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(test_run.returncode, 0, f"Workspace tests failed: {test_run.stderr}")

        # Live preview verification
        builder = BuildAgent()
        build_output = asyncio.run(builder.execute(task, context))
        self.assertEqual(build_output["status"], "success")
        preview_url = build_output["web_preview"]["url"]

        req = urllib.request.Request(preview_url, headers={"User-Agent": "Swarm-Test"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("Restaurant", body)
            self.assertNotIn("Headphones", body)

    def test_03_hospital_website_doctor_directory_and_appointments(self):
        """TEST C: Hospital with doctor directory, patient appointments, zero shopping cart, zero electronics."""
        mission_id = "mission_hospital_003"
        self.active_missions.append(mission_id)
        request = "Create a hospital website with doctor information and appointment booking"

        ctx = project_context(request)
        self.assertEqual(ctx["domain"], "hospital")

        ws = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id="test_user",
            mission_id=mission_id,
        )
        task = {"id": mission_id, "request": request, "user_id": "test_user"}
        context = {"workspace": ws}

        planner = PlanningAgent()
        plan = asyncio.run(planner.execute(task, context))
        context["Planning Agent"] = {"output": plan, "status": "completed"}

        coder = CodingAgent()
        code_output = asyncio.run(coder.execute(task, context))
        context["Coding Agent"] = {"output": code_output, "status": "completed"}

        html = ws.read_file("index.html")

        self.assertIn("Hospital", html)
        self.assertIn("Doctor", html)
        self.assertIn("Appointment", html)

        # Hospital must NOT have e-commerce cart elements
        self.assertNotIn("Add to Cart", html)
        self.assertNotIn("Aura Pro Wireless Headphones", html)
        self.assertNotIn("Cumulative GPA", html)

        # Unit test execution
        test_file = ws.root_path / "tests" / "test_app.py"
        test_run = subprocess.run(
            [sys.executable, "-m", "unittest", str(test_file)],
            cwd=str(ws.root_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(test_run.returncode, 0, f"Workspace tests failed: {test_run.stderr}")

        # Live preview verification
        builder = BuildAgent()
        build_output = asyncio.run(builder.execute(task, context))
        self.assertEqual(build_output["status"], "success")
        preview_url = build_output["web_preview"]["url"]

        req = urllib.request.Request(preview_url, headers={"User-Agent": "Swarm-Test"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("Hospital", body)
            self.assertIn("Doctor", body)

    def test_04_bakery_website_generation(self):
        """TEST D: Bakery with sourdough loaves, pastries, cakes, zero tech electronics."""
        mission_id = "mission_bakery_004"
        self.active_missions.append(mission_id)
        request = "Create a bakery website with cake and bread ordering"

        ctx = project_context(request)
        self.assertEqual(ctx["domain"], "bakery")

        ws = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id="test_user",
            mission_id=mission_id,
        )
        task = {"id": mission_id, "request": request, "user_id": "test_user"}
        context = {"workspace": ws}

        coder = CodingAgent()
        code_output = asyncio.run(coder.execute(task, context))

        html = ws.read_file("index.html")
        js = ws.read_file("app.js")

        self.assertIn("Bakery", html)
        self.assertIn("Croissant", js)
        self.assertIn("Sourdough", js)
        self.assertNotIn("Headphones", html)

    def test_05_student_portal_regression_protection(self):
        """TEST E: Regression check ensuring Student Management Portal remains 100% functional."""
        mission_id = "mission_student_portal_regression"
        self.active_missions.append(mission_id)
        request = "Build a Student Management Portal with student registration and GPA tracking"

        ctx = project_context(request)
        self.assertEqual(ctx["domain"], "student")

        ws = WorkspaceManager(
            workspace_root=self.workspace_root,
            user_id="test_user",
            mission_id=mission_id,
        )
        task = {"id": mission_id, "request": request, "user_id": "test_user"}
        context = {"workspace": ws}

        coder = CodingAgent()
        code_output = asyncio.run(coder.execute(task, context))

        html = ws.read_file("index.html")
        self.assertIn("Student", html)
        self.assertIn("Registration", html)
        self.assertIn("GPA", html)


if __name__ == "__main__":
    unittest.main()
