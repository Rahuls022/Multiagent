"""Persistent and In-Memory Settings Repository for Autonomous DevOps Swarm."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

DEFAULT_SYSTEM_SETTINGS: dict[str, Any] = {
    "theme": "dark",
    "general": {
        "projectName": "Autonomous DevOps Swarm",
        "description": "Multi-Agent Autonomous DevOps & Continuous Healing Engine",
        "defaultBranch": "main",
        "defaultTargetEnv": "development",
        "activeEnvironment": "production",
        "logVerbosity": "INFO",
        "timezone": "UTC",
        "telemetryInterval": "2000ms",
        "autoStartOnSubmit": True,
    },
    "autonomous": {
        "autonomousMode": True,
        "autonomyLevel": "supervised",
        "autoHealing": True,
        "autoRetryFailedJobs": True,
        "requireHumanApproval": False,
        "maxRemediationAttempts": 2,
        "rollbackOnFailedFix": True,
    },
    "safety": {
        "approvalBeforeProduction": False,
        "approvalBeforeDatabase": True,
        "approvalBeforeInfra": True,
        "protectedEnvironments": {
            "production": True,
            "staging": False,
            "development": False,
        },
        "riskPolicy": "medium",
        "maskSecretsInUi": True,
        "preventSecretCommit": True,
        "sessionTimeoutMinutes": 60,
    },
    "selfHealing": {
        "autoDiagnosis": True,
        "autoRemediation": True,
        "runHealthChecks": True,
        "detectionInterval": "30s",
        "verifyAfterFix": True,
        "rollbackIfVerifyFails": True,
    },
    "buildTesting": {
        "astCompilation": True,
        "unitTests": True,
        "integrationTests": True,
        "securityChecks": True,
        "dependencyChecks": True,
        "qualityGates": True,
        "minSuccessRate": 85,
        "blockDeploymentOnFail": True,
        "testTimeoutSec": 180,
    },
    "agents": {
        "globalOrchestrator": {"enabled": True, "maxPhases": 5, "strategy": "adaptive"},
        "developmentSupervisor": {"enabled": True, "autoHandoff": True},
        "operationsSupervisor": {"enabled": True, "autoRollback": True},
        "observerAgent": {"enabled": True, "heartbeatIntervalSec": 5},
        "roster": {
            "Planning Agent": {"enabled": True, "timeoutSec": 120, "maxRetries": 2, "model": "gpt-4o-mini"},
            "Coding Agent": {"enabled": True, "timeoutSec": 180, "maxRetries": 2, "model": "gpt-4o-mini"},
            "Build Agent": {"enabled": True, "timeoutSec": 60, "maxRetries": 3},
            "Testing Agent": {"enabled": True, "timeoutSec": 90, "maxRetries": 2},
            "Self-Healing Agent": {"enabled": True, "timeoutSec": 120, "maxRetries": 2},
            "Security Agent": {"enabled": True, "timeoutSec": 45, "maxRetries": 1},
            "Release Agent": {"enabled": True, "timeoutSec": 60, "maxRetries": 1},
            "Deploy Agent": {"enabled": True, "timeoutSec": 120, "maxRetries": 2},
            "Monitor Agent": {"enabled": True, "timeoutSec": 30, "maxRetries": 3},
        },
    },
    "agentConfig": {
        "maxActiveAgents": 6,
        "executionTimeout": "5m",
        "maxParallelTasks": 3,
        "agentHealthMonitoring": True,
        "autoAgentRestart": True,
        "agentFailureRecovery": True,
    },
    "resourceLimits": {
        "cpuLimit": 80,
        "memoryLimit": 4,
        "maxConcurrentJobs": 5,
        "executionTimeoutMinutes": 10,
    },
    "workspace": {
        "workspaceRoot": "workspaces",
        "enforcePathConfinement": True,
        "autoCleanEphemeral": True,
        "retainFailedArtifactsDays": 7,
        "gitAutoCheckpoint": True,
    },
    "integrations": {
        "github": {"connected": True, "repo": "autonomous-devops-swarm", "branch": "main"},
        "docker": {"connected": True, "registry": "docker.io/swarm-ci"},
        "nvidia": {"connected": True, "provider": "openai", "model": "gpt-4o-mini"},
        "kubernetes": {"connected": False, "cluster": "k8s-prod-cluster-01"},
        "jenkins": {"connected": False, "server": "https://ci.devops.internal"},
        "slack": {"connected": False, "channel": "#devops-swarm"},
        "webhook": {"connected": True, "endpoint": "https://api.internal.devops/hooks/swarm"},
    },
    "secrets": {
        "githubToken": "ghp_a8f9c2d1e4b5g7h9j0k2m4n6p8r0t2v4",
        "dockerKey": "dckr_pat_9x8w7v6u5t4s3r2q1p0o9n8m7",
        "nvidiaKey": "",
        "webhookSecret": "whsec_5k4j3h2g1f0e9d8c7b6a5",
    },
    "notifications": {
        "pipelineFailures": True,
        "selfHealingActions": True,
        "deploymentFailures": True,
        "criticalErrors": True,
        "agentFailures": True,
        "databaseFailures": True,
        "channel": "dashboard",
        "emailAddress": "devops-alerts@organization.com",
        "slackChannel": "#devops-swarm-alerts",
        "webhookUrl": "https://api.internal.devops/hooks/swarm",
        "alertSeverity": "critical",
    },
    "audit": {
        "recordAgentActions": True,
        "recordSelfHealing": True,
        "recordConfigChanges": True,
        "recordDeployments": True,
        "retentionDays": "30 days",
    },
    "advanced": {
        "systemMode": "live",
        "sandboxStrictness": "standard",
        "concurrencyLimit": 5,
        "ipcBufferSize": "64KB",
        "debugProfiling": False,
    },
}


class SettingsRepository(Protocol):
    """Protocol for settings persistence and audit trail."""

    async def get_settings(self) -> dict[str, Any]: ...
    async def save_settings(self, settings: dict[str, Any], user_id: str | None = None) -> dict[str, Any]: ...
    async def reset_settings(self, user_id: str | None = None) -> dict[str, Any]: ...
    async def add_audit_event(self, event: dict[str, Any]) -> dict[str, Any]: ...
    async def list_audit_events(self, limit: int = 50) -> list[dict[str, Any]]: ...


class InMemorySettingsRepository:
    """In-memory settings repository for fast testing."""

    def __init__(self) -> None:
        self._settings = deepcopy(DEFAULT_SYSTEM_SETTINGS)
        self._audit_logs: list[dict[str, Any]] = [
            {
                "id": "audit_seed_001",
                "timestamp": datetime.now(UTC).isoformat(),
                "user_id": "system",
                "action": "SYSTEM_INITIALIZED",
                "section": "General",
                "details": "Enterprise DevOps Swarm settings initialized to factory defaults.",
            }
        ]

    async def get_settings(self) -> dict[str, Any]:
        return deepcopy(self._settings)

    async def save_settings(self, settings: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
        merged = deepcopy(self._settings)
        for k, v in settings.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k].update(v)
            else:
                merged[k] = v
        self._settings = merged
        await self.add_audit_event({
            "id": f"audit_{uuid4().hex[:10]}",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id or "admin",
            "action": "SETTINGS_UPDATED",
            "section": "All",
            "details": "Configuration changes saved and persisted.",
        })
        return deepcopy(self._settings)

    async def reset_settings(self, user_id: str | None = None) -> dict[str, Any]:
        self._settings = deepcopy(DEFAULT_SYSTEM_SETTINGS)
        await self.add_audit_event({
            "id": f"audit_{uuid4().hex[:10]}",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id or "admin",
            "action": "SETTINGS_RESET",
            "section": "All",
            "details": "All configurations reset to recommended factory defaults.",
        })
        return deepcopy(self._settings)

    async def add_audit_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if "id" not in event:
            event["id"] = f"audit_{uuid4().hex[:10]}"
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(UTC).isoformat()
        self._audit_logs.insert(0, event)
        return event

    async def list_audit_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._audit_logs[:limit])


class SqliteSettingsRepository:
    """Persistent SQLite-backed settings repository."""

    def __init__(self, db_path: str | Path = "devops_swarm.db") -> None:
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_settings (
                        key TEXT PRIMARY KEY,
                        value_json TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        updated_by TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings_audit (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        user_id TEXT,
                        action TEXT NOT NULL,
                        section TEXT,
                        details TEXT
                    )
                    """
                )
                # Seed default settings if none present
                row = conn.execute("SELECT value_json FROM system_settings WHERE key = 'active_settings'").fetchone()
                if not row:
                    now = datetime.now(UTC).isoformat()
                    conn.execute(
                        "INSERT INTO system_settings (key, value_json, updated_at, updated_by) VALUES (?, ?, ?, ?)",
                        ("active_settings", json.dumps(DEFAULT_SYSTEM_SETTINGS), now, "system"),
                    )
                    conn.execute(
                        "INSERT INTO settings_audit (id, timestamp, user_id, action, section, details) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            "audit_init_001",
                            now,
                            "system",
                            "SYSTEM_INITIALIZED",
                            "General",
                            "Enterprise DevOps Swarm settings initialized to factory defaults.",
                        ),
                    )
        finally:
            conn.close()

    async def get_settings(self) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_get_settings)

    def _sync_get_settings(self) -> dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT value_json FROM system_settings WHERE key = 'active_settings'").fetchone()
            if row:
                loaded = json.loads(row[0])
                # Ensure all default top-level sections exist even if older schema stored
                merged = deepcopy(DEFAULT_SYSTEM_SETTINGS)
                for k, v in loaded.items():
                    if isinstance(v, dict) and isinstance(merged.get(k), dict):
                        merged[k].update(v)
                    else:
                        merged[k] = v
                return merged
            return deepcopy(DEFAULT_SYSTEM_SETTINGS)
        finally:
            conn.close()

    async def save_settings(self, settings: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_save_settings, settings, user_id)

    def _sync_save_settings(self, settings: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
        current = self._sync_get_settings()
        merged = deepcopy(current)
        for k, v in settings.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k].update(v)
            else:
                merged[k] = v

        now = datetime.now(UTC).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO system_settings (key, value_json, updated_at, updated_by)
                    VALUES ('active_settings', ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value_json = excluded.value_json,
                        updated_at = excluded.updated_at,
                        updated_by = excluded.updated_by
                    """,
                    (json.dumps(merged), now, user_id or "admin"),
                )
                audit_id = f"audit_{uuid4().hex[:10]}"
                conn.execute(
                    "INSERT INTO settings_audit (id, timestamp, user_id, action, section, details) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        audit_id,
                        now,
                        user_id or "admin",
                        "SETTINGS_UPDATED",
                        "All",
                        "Configuration changes saved and persisted to database.",
                    ),
                )
            return merged
        finally:
            conn.close()

    async def reset_settings(self, user_id: str | None = None) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_reset_settings, user_id)

    def _sync_reset_settings(self, user_id: str | None = None) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO system_settings (key, value_json, updated_at, updated_by)
                    VALUES ('active_settings', ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value_json = excluded.value_json,
                        updated_at = excluded.updated_at,
                        updated_by = excluded.updated_by
                    """,
                    (json.dumps(DEFAULT_SYSTEM_SETTINGS), now, user_id or "admin"),
                )
                audit_id = f"audit_{uuid4().hex[:10]}"
                conn.execute(
                    "INSERT INTO settings_audit (id, timestamp, user_id, action, section, details) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        audit_id,
                        now,
                        user_id or "admin",
                        "SETTINGS_RESET",
                        "All",
                        "All configurations reset to recommended factory defaults.",
                    ),
                )
            return deepcopy(DEFAULT_SYSTEM_SETTINGS)
        finally:
            conn.close()

    async def add_audit_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_add_audit, event)

    def _sync_add_audit(self, event: dict[str, Any]) -> dict[str, Any]:
        audit_id = event.get("id") or f"audit_{uuid4().hex[:10]}"
        now = event.get("timestamp") or datetime.now(UTC).isoformat()
        user_id = event.get("user_id") or "system"
        action = event.get("action") or "EVENT"
        section = event.get("section") or "General"
        details = event.get("details") or ""

        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO settings_audit (id, timestamp, user_id, action, section, details) VALUES (?, ?, ?, ?, ?, ?)",
                    (audit_id, now, user_id, action, section, details),
                )
            return {"id": audit_id, "timestamp": now, "user_id": user_id, "action": action, "section": section, "details": details}
        finally:
            conn.close()

    async def list_audit_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list_audit, limit)

    def _sync_list_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "SELECT id, timestamp, user_id, action, section, details FROM settings_audit ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "user_id": r[2],
                    "action": r[3],
                    "section": r[4],
                    "details": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()


def create_settings_repository(db_path: str | Path = "devops_swarm.db", is_in_memory: bool = False) -> SettingsRepository:
    """Factory to produce settings repository."""
    if is_in_memory:
        return InMemorySettingsRepository()
    return SqliteSettingsRepository(db_path=db_path)

