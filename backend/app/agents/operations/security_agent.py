"""Real security gate agent for checking secrets, vulnerabilities, and dangerous commands."""

from __future__ import annotations

from typing import Any
from pathlib import Path

from ..base_agent import BaseAgent
from app.tools.workspace import WorkspaceManager
from app.tools.security_scanner import SecurityScanner


class SecurityAgent(BaseAgent):
    name = "Security Agent"

    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        workspace: WorkspaceManager | None = context.get("workspace")
        if workspace is None:
            workspace_root = context.get("workspace_root")
            if workspace_root and Path(workspace_root).exists():
                workspace_dir = Path(workspace_root)
            else:
                from uuid import uuid4
                workspace = WorkspaceManager(
                    user_id=task.get("user_id", "default"),
                    mission_id=task.get("id", str(uuid4())),
                )
                context["workspace"] = workspace
                workspace_dir = workspace.workspace_dir
        else:
            workspace_dir = workspace.workspace_dir

        scanner = SecurityScanner()
        scan_res = scanner.scan_workspace(workspace_dir)

        result = {
            "status": "completed" if scan_res["passed"] else "failed",
            "success": scan_res["passed"],
            "vulnerabilities": scan_res["vulnerabilities"],
            "secrets_found": scan_res["secrets_found"],
            "scanned_files": scan_res["scanned_files"],
            "findings": scan_res["findings"],
            "checks": ["Dependencies", "Secrets", "Basic vulnerabilities", "Dangerous Commands", "Path Traversal"],
            "message": scan_res["message"],
        }

        if not scan_res["passed"]:
            raise RuntimeError(
                f"SECURITY_GATE_FAILED: Found {scan_res['vulnerabilities']} vulnerabilities "
                f"({scan_res['secrets_found']} secrets) in workspace."
            )

        return result

    def validate(self, output: dict[str, Any]) -> tuple[bool, str]:
        if not output:
            return False, "Security Agent returned empty output."
        if not output.get("success", False) or output.get("secrets_found", 0) > 0:
            return False, f"Security check failed: {output.get('message', 'Vulnerabilities detected')}"
        return True, "Security gate passed"

