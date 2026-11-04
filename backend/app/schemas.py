"""HTTP request models for the dashboard API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field



class PipelineRequest(BaseModel):
    request: str = Field(min_length=3, max_length=1000, examples=["Build a student management portal"])
    goals_and_requirements: str | None = Field(default=None, description="Detailed project goals and requirements")
    language: str | None = Field(default="python", description="Programming language (e.g. Python, TypeScript, Go)")
    framework: str | None = Field(default=None, description="Framework (e.g. FastAPI, Flask, React, Node)")
    required_features: list[str] | None = Field(default=None, description="List of required application features")
    testing_requirements: list[str] | str | None = Field(default=None, description="Unit, integration, or contract test specifications")
    security_requirements: list[str] | str | None = Field(default=None, description="Authentication, secret scanning, or compliance gates")
    deployment_target: str | None = Field(default="development", description="Target environment (development, staging, production)")
    build_and_deployment_preferences: dict[str, Any] | str | None = Field(default=None, description="Build containerization or cloud rollout preferences")
    require_approval: bool | None = Field(default=False, description="Require manual operator approval before production release")
    user_id: str | None = Field(default=None, description="Optional authenticated user ID")

    def to_mission_task(self, fallback_user_id: str | None = None) -> dict[str, Any]:
        """Convert input payload to structured mission task context."""
        from datetime import UTC, datetime
        from uuid import uuid4

        pipeline_id = f"pipe_{uuid4().hex[:12]}"
        now_iso = datetime.now(UTC).isoformat()
        
        testing_list = [self.testing_requirements] if isinstance(self.testing_requirements, str) else (self.testing_requirements or [])
        security_list = [self.security_requirements] if isinstance(self.security_requirements, str) else (self.security_requirements or [])
        build_prefs = {"preferences": self.build_and_deployment_preferences} if isinstance(self.build_and_deployment_preferences, str) else (self.build_and_deployment_preferences or {})
        features_list = [self.required_features] if isinstance(self.required_features, str) else (self.required_features or [])

        # Build composite request string for LLM awareness while preserving original
        parts = [self.request.strip()]
        if self.language:
            parts.append(f"Language: {self.language}")
        if self.framework:
            parts.append(f"Framework: {self.framework}")
        if features_list:
            parts.append(f"Features: {', '.join(features_list)}")
        if testing_list:
            parts.append(f"Testing: {', '.join(testing_list)}")
        if security_list:
            parts.append(f"Security: {', '.join(security_list)}")

        full_request_desc = " | ".join(parts)

        return {
            "id": pipeline_id,
            "pipeline_id": pipeline_id,
            "request": full_request_desc,
            "mission_goal": self.request.strip(),
            "goals_and_requirements": self.goals_and_requirements or self.request.strip(),
            "language": self.language or "python",
            "framework": self.framework,
            "required_features": features_list,
            "testing_requirements": testing_list,
            "security_requirements": security_list,
            "deployment_target": self.deployment_target or "development",
            "build_and_deployment_preferences": build_prefs,
            "require_approval": bool(self.require_approval or (self.deployment_target == "production")),
            "user_id": self.user_id or fallback_user_id or "anonymous",
            "created_at": now_iso,
            "status": "pending",
        }

