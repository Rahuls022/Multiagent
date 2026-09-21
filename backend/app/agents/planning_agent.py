"""Agent that creates a project-specific, presentation-ready delivery plan."""

from typing import Any

from .base_agent import BaseAgent
from .nvidia_client import NvidiaNimClient
from .project_context import project_context


class PlanningAgent(BaseAgent):
    name = "Planning Agent"

    def __init__(self, client: NvidiaNimClient | None = None) -> None:
        self.client = client or NvidiaNimClient()

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        request = task["request"].strip()
        project = project_context(request)

        if self.client.is_configured:
            try:
                llm_result = await self.client.create_json(
                    system_prompt=(
                        "You are an expert Principal Solutions Architect & AI Systems Planner. "
                        "Return ONE valid JSON object ONLY. "
                        "Create a thorough, production-grade architectural delivery plan for the requested software. "
                        "Include fields: summary, goal, architecture (with frontend, backend, database, security), "
                        "domain_models (array of objects with name and fields array), "
                        "implementation_steps (array of objects with step, title, detail, deliverables), "
                        "features (array of strings), api_contract (array of objects with method, path, description), "
                        "acceptance_criteria (array of strings), handoff (string)."
                    ),
                    user_prompt=(
                        f"User request mission: {request}\n"
                        f"Synthesized project hints: {project}"
                    ),
                )
                if isinstance(llm_result, dict):
                    llm_result.setdefault("request", request)
                    llm_result.setdefault("project", project)
                    return llm_result
            except Exception:
                # Fall back to structured synthesized plan if LLM is unavailable or fails
                pass

        # Synthesized high-detail architecture plan
        actor = project["actor"]
        kind = project["kind"]
        plural = project["plural"]
        name = project["name"]
        primary_action = project["primary_action"]
        domain_models = project.get("domain_models", [])
        routes = project.get("routes", [])

        model_names = [m["name"] for m in domain_models] if domain_models else [project.get("pascal_entity", "Record")]

        steps = [
            {
                "step": 1,
                "title": f"Requirements & Domain Architecture for {name}",
                "detail": f"Analyze core user journeys for {actor}s to {primary_action}. Map security requirements, tenant boundaries, and audit logging needs.",
                "deliverables": ["User journey specification", "Domain boundary context map"],
            },
            {
                "step": 2,
                "title": f"Database Modeling & Persistence ({', '.join(model_names)})",
                "detail": f"Design relational schemas for {', '.join(model_names)}. Define field validations, unique constraints, foreign keys, and indexes.",
                "deliverables": [f"{m_name} schema migration scripts" for m_name in model_names],
            },
            {
                "step": 3,
                "title": "FastAPI REST Contract & Service Layer",
                "detail": f"Implement typed endpoints for {', '.join(r['path'] for r in routes[:3]) if routes else '/api/records'}. Add request validation, error responses, and dependency injection.",
                "deliverables": ["OpenAPI 3.0 specification", "Pydantic validation schemas", "FastAPI route controllers"],
            },
            {
                "step": 4,
                "title": f"React UI & {project.get('feature_slug', 'records').capitalize()} Workspace",
                "detail": f"Construct interactive user interfaces ({', '.join(project.get('ui', ['Dashboard']))}) with async data fetching, loading spinners, empty states, and error toasts.",
                "deliverables": ["React workspace components", "Form validation state hooks", "Tailwind / CSS design tokens"],
            },
            {
                "step": 5,
                "title": "Authentication, Permissions & Security Audit",
                "detail": "Implement JWT / session-based auth, password hashing, CORS protection, rate limiting, and RBAC permission checks across all API routes.",
                "deliverables": ["Auth middleware", "Role-based access guard", "Security vulnerability scan report"],
            },
            {
                "step": 6,
                "title": "End-to-End Verification & Automated Testing",
                "detail": f"Validate end-to-end mission workflow: verify that a {actor} can successfully {primary_action} under high load and error conditions.",
                "deliverables": ["Pytest API suite", "Frontend interaction unit tests", "CI/CD automated release pipeline"],
            },
        ]

        return {
            "summary": f"Comprehensive Architectural & Delivery Plan for {name}",
            "request": request,
            "project": project,
            "goal": f"Deliver a high-performance, resilient {kind} allowing {actor}s to {primary_action} seamlessly.",
            "architecture": {
                "frontend": f"Modern React 19 SPA featuring {', '.join(project.get('ui', ['Dashboard']))}, modular state management, and real-time API syncing.",
                "backend": f"FastAPI Python service layer utilizing Pydantic v2 schemas, asynchronous controllers, and structured error handling.",
                "database": f"MongoDB / PostgreSQL persistent storage for {plural} with indexing on query lookup keys and audit timestamps.",
                "security": "OAuth2 / JWT Token Bearer authentication, strict CORS origin policies, input sanitization, and role-based permissions.",
            },
            "domain_models": domain_models,
            "implementation_steps": steps,
            "features": project.get("features", []),
            "api_contract": routes,
            "acceptance_criteria": [
                f"A {actor} can log in and successfully {primary_action}.",
                f"All input validation errors return HTTP 422 with clear JSON diagnostic details.",
                f"Saved {plural} persist correctly across page refreshes and server restarts.",
                "System maintains response latencies under 200ms for routine API operations.",
            ],
            "handoff": "Pass architectural context, domain models, and API specs to the Coding Agent to generate complete runnable source code.",
        }
