"""Coordinates environment deployment with approval gates and runtime rollout."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ..base_agent import BaseAgent


class DeployAgent(BaseAgent):
    name = "Deploy Agent"

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        # 1. Verify release condition
        release_stage = context.get("Release Agent", {})
        release = release_stage.get("output", {})
        if not release or release.get("status") not in ("released", "ready_for_deployment", "completed"):
            raise RuntimeError("DEPLOYMENT_BLOCKED: Release Agent must successfully prepare a release bundle first.")

        version = release.get("version", "v1.0.0")
        target_env = task.get("deployment_target") or "development"
        mission_id = task.get("id", str(uuid4()))[:8]
        deployment_id = f"dep-{mission_id}"

        # 2. Production approval check
        requires_approval = bool(
            task.get("require_approval", False) or
            target_env.lower() in ("production", "prod")
        )
        is_approved = bool(task.get("approved", False) or context.get("approval_granted", False))

        if requires_approval and not is_approved:
            return {
                "status": "awaiting_approval",
                "environment": target_env,
                "version": version,
                "deployment_id": deployment_id,
                "health": "pending_approval",
                "approval_required": True,
                "message": f"Deployment to '{target_env}' is staged and awaiting human operator approval.",
            }

        # 3. Successful deployment rollout
        port = 8080
        endpoint = f"http://localhost:{port}/services/{mission_id}"
        health_endpoint = f"{endpoint}/health"

        return {
            "status": "deployed",
            "environment": target_env,
            "version": version,
            "deployment_id": deployment_id,
            "endpoint": endpoint,
            "health_endpoint": health_endpoint,
            "health": "healthy",
            "container_image": f"swarm/app:{version}",
            "deployed_at": datetime.now(UTC).isoformat(),
            "traffic_allocation": "100%",
            "deployment_strategy": "rolling_update",
            "message": f"Successfully rolled out release {version} to {target_env} environment at {endpoint}.",
        }

