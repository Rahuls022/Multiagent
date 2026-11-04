"""Real Planning Agent that produces a structured architectural specification using the LLM."""

from __future__ import annotations

import json
import re
from typing import Any

from .base_agent import BaseAgent
from app.llm import LLMClient
from app.skills import get_skill_registry
from app.tools.workspace import WorkspaceManager


class PlanningAgent(BaseAgent):
    name = "Planning Agent"

    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or LLMClient()

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        request = task.get("request", "").strip()
        if not request:
            raise ValueError("Mission request cannot be empty.")

        skill_reg = get_skill_registry()
        skill = skill_reg.get_skill_for_agent(self.name)
        skill_injection = skill_reg.get_prompt_injection(self.name)
        self.log(f"I'm using the {skill.name if skill else 'writing-plans'} skill to create the implementation plan.")

        system_prompt = (
            "You are an expert Principal Solutions Architect & Lead DevOps Engineer. "
            "You receive a natural language software development mission and produce a strict, production-grade implementation plan. "
            "You MUST respond with a single, valid JSON object containing EXACTLY these keys:\n"
            "- summary: string concise executive summary of the project\n"
            "- goal: string primary technical objective\n"
            "- requirements: list of strings (functional & non-functional requirements)\n"
            "- architecture: object with keys 'frontend', 'backend', 'database', 'security'\n"
            "- domain_models: list of objects, each with 'name' (string) and 'fields' (list of objects with 'name', 'type', 'description')\n"
            "- api_contract: list of objects, each with 'method' (GET/POST/PUT/DELETE/PATCH), 'path' (e.g. /health), 'description' (string)\n"
            "- files_to_create: list of objects, each with 'path' (string file path, e.g. 'app.py', 'tests/test_app.py'), 'language' (string, e.g. 'python'), 'purpose' (string)\n"
            "- files_to_modify: list of objects (empty if new project)\n"
            "- implementation_steps: list of objects, each with 'step' (integer), 'title' (string), 'detail' (string), 'deliverables' (list of strings)\n"
            "- acceptance_criteria: list of strings (testable quality gates)\n"
            "- testing_plan: list of objects with 'name', 'target', 'assertion'\n"
            "- deployment_plan: list of objects with 'step', 'command_or_spec'\n"
            "- handoff: string note explaining what the Coding Agent should build first.\n\n"
            "CRITICAL ARCHITECTURAL CONSTRAINTS:\n"
            "1. Target Stack: When the user requests a website, portal, dashboard, UI, or web application, you MUST plan BOTH frontend files ('index.html', 'styles.css', 'app.js') AND backend/test files ('app.py', 'tests/test_app.py'). For backend-only services, plan Python modules ('app.py', 'models.py', 'tests/test_app.py').\n"
            "2. File Count: Plan 3 to 5 essential, high-impact files so the Coding Agent can generate complete, runnable code without timing out.\n"
            "3. Dependencies: Use HTML5, modern vanilla JavaScript/CSS, and Python Standard Library or pre-installed FastAPI.\n"
            f"{skill_injection}"
        )

        user_prompt = f"Mission Objective: {request}"

        plan = {}
        try:
            plan = await self.client.create_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=2048,
            )
        except Exception as exc:
            import logging
            logging.getLogger("autonomous_devops.planning").warning(
                "Planning Agent LLM call encountered error (%s). Synthesizing resilient fallback plan.", exc
            )
            plan = self._fallback_plan(request)

        if not plan.get("files_to_create"):
            fallback = self._fallback_plan(request)
            for k, v in fallback.items():
                plan.setdefault(k, v)
            if not plan.get("files_to_create"):
                plan["files_to_create"] = fallback["files_to_create"]

        # Ensure required top-level keys exist
        plan.setdefault("request", request)
        plan.setdefault("summary", f"Implementation Plan for: {request}")
        plan.setdefault("requirements", [])
        plan.setdefault("files_to_create", [])
        plan.setdefault("domain_models", [])
        plan.setdefault("api_contract", [])
        plan.setdefault("implementation_steps", [])
        plan.setdefault("acceptance_criteria", [])
        plan["skills_used"] = [skill.name] if skill else ["writing-plans"]
        plan["skill_applied"] = {
            "name": skill.name if skill else "writing-plans",
            "source": "skills.sh",
            "role": "Structured implementation planning and acceptance criteria",
        }

        # Maintain UI compatibility metadata if not present
        if "project" not in plan:
            plan["project"] = {
                "name": request[:40],
                "actor": "User",
                "entity": "record",
                "pascal_entity": "Record",
                "plural": "records",
                "primary_action": "interact with the service",
                "feature_slug": "app",
            }

        # Save structured architectural plan to the mission workspace as plan.json
        workspace: WorkspaceManager | None = context.get("workspace")
        if workspace is None:
            from uuid import uuid4
            workspace = WorkspaceManager(
                user_id=task.get("user_id", "default"),
                mission_id=task.get("id", str(uuid4())),
            )
            context["workspace"] = workspace

        try:
            workspace.write_file("plan.json", json.dumps(plan, indent=2))
        except Exception as exc:
            import logging
            logging.getLogger("autonomous_devops.planning").warning("Could not write plan.json to workspace: %s", exc)

        return plan

    def _fallback_plan(self, request: str) -> dict[str, Any]:
        from .project_context import project_context
        ctx = project_context(request)
        domain = ctx.get("domain", "generic")
        req_lower = request.lower()
        is_web = bool(re.search(
            r"\b(portal|website|web|frontend|dashboard|ui|login|pages?|student|school|hospital|patient|store|shop|ecommerce|e-commerce)\b",
            req_lower,
        ))

        if domain == "student":
            files_to_create = [
                {"path": "frontend/package.json", "language": "json", "purpose": "Vite/React package configuration"},
                {"path": "frontend/index.html", "language": "html", "purpose": "Student portal HTML entrypoint"},
                {"path": "frontend/src/App.jsx", "language": "javascript", "purpose": "Student Portal root component"},
                {"path": "frontend/src/styles/App.css", "language": "css", "purpose": "Student Portal styling"},
                {"path": "index.html", "language": "html", "purpose": "Interactive Single Page Application portal"},
                {"path": "styles.css", "language": "css", "purpose": "Modern dark-themed responsive UI stylesheets"},
                {"path": "app.js", "language": "javascript", "purpose": "Client-side interactive state management"},
                {"path": "backend/main.py", "language": "python", "purpose": "FastAPI Student Management REST API"},
                {"path": "backend/database.py", "language": "python", "purpose": "SQLite database initialization and persistence"},
                {"path": "app.py", "language": "python", "purpose": "Application service entrypoint"},
                {"path": "tests/test_api.py", "language": "python", "purpose": "9-endpoint integration test suite"},
                {"path": "tests/test_students.py", "language": "python", "purpose": "Student business logic unit tests"},
            ]
            return {
                "request": request,
                "summary": "Implementation Plan for Student Management Portal",
                "goal": "Build and deploy a robust full-stack Student Management Portal with student registration, directory, profiles, search, and academic dashboard.",
                "requirements": [
                    "KPI Dashboard displaying total enrolled students, active status, academic departments, and cumulative GPA",
                    "Student enrollment registration form with input validation (name, email, phone, GPA, department)",
                    "Student directory with live search and department filtering",
                    "Student profile and edit modal with real-time updates",
                    "Delete confirmation modal and toast alert notifications",
                    "FastAPI REST API with endpoints: GET/POST /api/students, GET/PUT/DELETE /api/students/{id}, GET /api/health",
                    "Pydantic schema validation for request payloads",
                    "SQLite persistence with automatic table initialization and seed data",
                    "Comprehensive automated test suite covering 9 required verification scenarios",
                ],
                "architecture": {
                    "frontend": "React 18 + Vite + Responsive CSS Single Page Application",
                    "backend": "FastAPI + Pydantic REST API Service",
                    "database": "SQLite persistent database",
                    "security": "Pydantic payload validation, CORS middleware, strict ID checks",
                },
                "domain_models": [
                    {
                        "name": "Student",
                        "fields": [
                            {"name": "id", "type": "int", "description": "Primary key"},
                            {"name": "student_id", "type": "str", "description": "Unique student identifier (e.g. STU-1001)"},
                            {"name": "name", "type": "str", "description": "Full student name"},
                            {"name": "email", "type": "str", "description": "Academic email address"},
                            {"name": "department", "type": "str", "description": "Academic department or major"},
                            {"name": "phone", "type": "str", "description": "Contact telephone number"},
                            {"name": "gpa", "type": "float", "description": "Grade point average (0.00 - 4.00)"},
                            {"name": "status", "type": "str", "description": "Enrollment status (Active / Inactive)"},
                        ],
                    }
                ],
                "api_contract": [
                    {"method": "GET", "path": "/api/health", "description": "Service health check"},
                    {"method": "GET", "path": "/api/students", "description": "List all students with optional search and department filter"},
                    {"method": "POST", "path": "/api/students", "description": "Register a new student"},
                    {"method": "GET", "path": "/api/students/{student_id}", "description": "Get student details by ID"},
                    {"method": "PUT", "path": "/api/students/{student_id}", "description": "Update student record"},
                    {"method": "DELETE", "path": "/api/students/{student_id}", "description": "Delete student record"},
                ],
                "files_to_create": files_to_create,
                "files_to_modify": [],
                "implementation_steps": [
                    {"step": 1, "title": "Synthesize Frontend Portal & Components", "detail": "Construct dashboard KPIs, directory table, search filter, and registration forms", "deliverables": ["frontend/index.html", "frontend/src/App.jsx", "index.html", "styles.css", "app.js"]},
                    {"step": 2, "title": "Synthesize FastAPI Backend Service", "detail": "Implement REST endpoints, Pydantic schemas, and SQLite database persistence", "deliverables": ["backend/main.py", "backend/database.py", "app.py"]},
                    {"step": 3, "title": "Synthesize Automated Test Suite", "detail": "Implement 9 comprehensive test scenarios verifying all endpoints and validation rules", "deliverables": ["tests/test_api.py", "tests/test_students.py"]},
                ],
                "acceptance_criteria": [
                    "Live application preview renders interactive responsive Student Management Portal",
                    "KPI dashboard accurately computes enrolled count, department count, and GPA",
                    "Student registration form validates required fields and rejects invalid emails",
                    "FastAPI backend responds to all 6 REST endpoints",
                    "Automated test suite executes and passes 100% of 9 test scenarios",
                ],
                "testing_plan": [
                    {"name": "test_01_health_endpoint", "target": "/api/health", "assertion": "returns status healthy"},
                    {"name": "test_02_student_creation", "target": "/api/students", "assertion": "creates new student record"},
                    {"name": "test_03_student_listing", "target": "/api/students", "assertion": "lists enrolled students"},
                    {"name": "test_04_student_retrieval", "target": "/api/students/{id}", "assertion": "retrieves student by ID"},
                    {"name": "test_05_student_updating", "target": "/api/students/{id}", "assertion": "updates student attributes"},
                    {"name": "test_06_student_deletion", "target": "/api/students/{id}", "assertion": "deletes student and returns 404 subsequently"},
                    {"name": "test_07_invalid_email_validation", "target": "/api/students", "assertion": "returns 422 for malformed email"},
                    {"name": "test_08_duplicate_student_id_rejected", "target": "/api/students", "assertion": "returns 400 for duplicate student ID"},
                    {"name": "test_09_search_functionality", "target": "/api/students?q=Elena", "assertion": "filters students by query query string"},
                ],
                "deployment_plan": [
                    {"step": "1", "command_or_spec": "python -m unittest discover -v tests/"},
                    {"step": "2", "command_or_spec": "python app.py"},
                ],
                "handoff": "Coding Agent: Generate complete frontend portal and FastAPI backend with 9-endpoint test suite.",
                "project": ctx,
            }

        files_to_create = []
        if is_web:
            files_to_create = [
                {"path": "index.html", "language": "html", "purpose": "Single Page Application portal with navigation, dashboard, forms, and data tables"},
                {"path": "styles.css", "language": "css", "purpose": "Modern dark-themed responsive UI stylesheets"},
                {"path": "app.js", "language": "javascript", "purpose": "Client-side interactive state management and local persistence"},
                {"path": "app.py", "language": "python", "purpose": "Application service logic and handlers"},
                {"path": "tests/test_app.py", "language": "python", "purpose": "Comprehensive automated test suite"},
            ]
        else:
            files_to_create = [
                {"path": "app.py", "language": "python", "purpose": "Application service logic and handlers"},
                {"path": "tests/test_app.py", "language": "python", "purpose": "Comprehensive automated test suite"},
            ]

        return {
            "request": request,
            "summary": f"Implementation Plan for {ctx.get('name', request)}",
            "goal": f"Build and deploy a robust {ctx.get('kind', 'service')} to {ctx.get('primary_action', 'manage records')}.",
            "requirements": [f"Provide {f}" for f in ctx.get("features", ["core business operations", "data integrity", "robust API handlers"])],
            "architecture": {
                "frontend": "Modern Responsive HTML5 / JS Application" if is_web else "REST/JSON API",
                "backend": "Python Modular Service",
                "database": "SQLite (In-Memory / Local)",
                "security": "Input validation & strict sanitization",
            },
            "domain_models": ctx.get("domain_models", []),
            "api_contract": [
                {"method": "GET", "path": "/health", "description": "Service health check"},
                {"method": "GET", "path": f"/api/{ctx.get('plural', 'records')}", "description": f"List all {ctx.get('plural', 'records')}"},
                {"method": "POST", "path": f"/api/{ctx.get('plural', 'records')}", "description": f"Create new {ctx.get('entity', 'record')}"},
            ],
            "files_to_create": files_to_create,
            "files_to_modify": [],
            "implementation_steps": [
                {"step": 1, "title": "Implement Frontend Application & UI", "detail": "Construct responsive navigation, dashboard, forms, and live tables", "deliverables": ["index.html", "styles.css", "app.js"] if is_web else ["app.py"]},
                {"step": 2, "title": "Implement Domain Models & Service", "detail": "Create core entities and storage handlers", "deliverables": ["app.py"]},
                {"step": 3, "title": "Implement Automated Test Suite", "detail": "Create unit tests verifying functionality and edge cases", "deliverables": ["tests/test_app.py"]},
            ],
            "acceptance_criteria": [
                "Live application preview renders interactive responsive website",
                "All domain logic functions without errors",
                "Unit test suite passes 100% of test assertions",
                "Code syntax conforms to web and Python standards",
            ],
            "testing_plan": [
                {"name": "test_service_health", "target": "app.py", "assertion": "returns healthy status"},
                {"name": "test_core_operations", "target": "app.py", "assertion": "verifies create and list operations"},
            ],
            "deployment_plan": [
                {"step": "1", "command_or_spec": "python -m unittest discover -v"},
                {"step": "2", "command_or_spec": "python app.py"},
            ],
            "handoff": "Coding Agent: build frontend index.html/styles.css/app.js and backend app.py, then ensure tests pass 100%.",
            "project": ctx,
        }

    def validate(self, output: dict[str, Any]) -> tuple[bool, str]:
        if not output:
            return False, "Planning Agent returned empty output."
        if not output.get("files_to_create"):
            return False, "Planning Agent plan must specify at least one file in 'files_to_create'."
        return True, "Valid plan"
