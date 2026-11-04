"""Repository boundary for pipeline history and failure memory storage."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = None  # type: ignore[assignment,misc]


class DuplicateUserError(ValueError):
    """Raised when attempting to create a user with an email that already exists."""


class PipelineRepository(Protocol):
    storage_name: str

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]: ...
    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]: ...
    async def get(self, pipeline_id: str) -> dict[str, Any] | None: ...
    async def list(self, limit: int = 20, user_id: str | None = None) -> list[dict[str, Any]]: ...

    # Self-Healing Failure Memory API
    async def save_failure_memory(self, record: dict[str, Any]) -> dict[str, Any]: ...
    async def list_failure_memory(self, limit: int = 50) -> list[dict[str, Any]]: ...
    async def find_matching_healing_pattern(self, error_signature: str) -> dict[str, Any] | None: ...

    # Live Website Preview Metadata API
    async def save_preview_metadata(self, record: dict[str, Any]) -> dict[str, Any]: ...
    async def get_preview_metadata(self, mission_id: str) -> dict[str, Any] | None: ...

    async def init(self) -> None: ...
    async def get_status(self) -> dict[str, Any]: ...
    async def close(self) -> None: ...


class InMemoryPipelineRepository:
    """Safe development fallback; data is stored in memory for dev session."""

    storage_name = "in-memory (temporary)"

    def __init__(self) -> None:
        self._pipelines: dict[str, dict[str, Any]] = {}
        self._failures: list[dict[str, Any]] = []
        self._previews: dict[str, dict[str, Any]] = {}

    async def init(self) -> None:
        pass

    async def get_status(self) -> dict[str, Any]:
        return {
            "connected": True,
            "storage": self.storage_name,
            "database_name": "in_memory",
            "counts": {
                "pipeline_history": len(self._pipelines),
                "failure_memory": len(self._failures),
            },
        }

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        self._pipelines[pipeline["task"]["id"]] = deepcopy(pipeline)
        return deepcopy(pipeline)

    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]:
        self._pipelines[pipeline_id] = deepcopy(pipeline)
        return deepcopy(pipeline)

    async def get(self, pipeline_id: str) -> dict[str, Any] | None:
        pipeline = self._pipelines.get(pipeline_id)
        return deepcopy(pipeline) if pipeline else None

    async def list(self, limit: int = 20, user_id: str | None = None) -> list[dict[str, Any]]:
        items = list(self._pipelines.values())
        if user_id:
            items = [p for p in items if p.get("task", {}).get("user_id") == user_id]
        values = sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)
        return deepcopy(values[:limit])

    async def save_failure_memory(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        item.setdefault("created_at", datetime.now(UTC).isoformat())
        self._failures.insert(0, item)
        return item

    async def list_failure_memory(self, limit: int = 50) -> list[dict[str, Any]]:
        return deepcopy(self._failures[:limit])

    async def find_matching_healing_pattern(self, error_signature: str) -> dict[str, Any] | None:
        sig_lower = error_signature.lower()
        for fail in self._failures:
            # Verified-only solutions: success must be true and verification_result != 'FAIL'
            if not fail.get("success", False) or fail.get("verification_result") == "FAIL":
                continue
            known = fail.get("error_signature", "").lower()
            known_cat = (fail.get("error_category") or "").lower()
            if known in sig_lower or sig_lower in known or (known_cat and known_cat in sig_lower):
                return deepcopy(fail)
        return None

    async def save_preview_metadata(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        item.setdefault("updated_at", datetime.now(UTC).isoformat())
        self._previews[item["mission_id"]] = item
        return item

    async def get_preview_metadata(self, mission_id: str) -> dict[str, Any] | None:
        item = self._previews.get(mission_id)
        return deepcopy(item) if item else None

    async def close(self) -> None:
        return None


class SQLitePipelineRepository:
    """Persistent SQLite repository for missions, telemetry, and failure memory."""

    storage_name = "sqlite"

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._init_db()

    async def init(self) -> None:
        pass

    async def get_status(self) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_get_status)

    def _sync_get_status(self) -> dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        try:
            p_count = conn.execute("SELECT COUNT(*) FROM pipelines").fetchone()[0]
            f_count = conn.execute("SELECT COUNT(*) FROM failure_memory").fetchone()[0]
            counts = {
                "pipeline_history": p_count,
                "failure_memory": f_count,
                "users": 1,
            }
            return {
                "status": "connected",
                "connected": True,
                "storage": self.storage_name,
                "storage_type": "sqlite",
                "database_name": Path(self.db_path).name,
                "ping_ms": 0.2,
                "counts": counts,
                "document_counts": counts,
                "setup_instructions": "Running local SQLite fallback. Launch MongoDB with: docker run -p 27017:27017 mongo",
                "instructions": "Running local SQLite fallback. Launch MongoDB with: docker run -p 27017:27017 mongo",
            }
        except Exception as exc:
            return {
                "status": "disconnected",
                "connected": False,
                "storage": self.storage_name,
                "storage_type": "sqlite",
                "error": str(exc),
            }
        finally:
            conn.close()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS pipelines (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        status TEXT,
                        progress INTEGER,
                        updated_at TEXT,
                        payload JSON
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS failure_memory (
                        failure_id TEXT PRIMARY KEY,
                        pipeline_id TEXT,
                        user_id TEXT,
                        failed_agent TEXT,
                        error_category TEXT,
                        error_signature TEXT,
                        error_message TEXT,
                        stack_trace_hash TEXT,
                        affected_component TEXT,
                        affected_files JSON,
                        git_diff TEXT,
                        root_cause TEXT,
                        fix_description TEXT,
                        files_modified JSON,
                        attempts INTEGER DEFAULT 1,
                        tech_stack TEXT,
                        verification_result TEXT,
                        success INTEGER,
                        healed_at TEXT,
                        created_at TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS mission_previews (
                        mission_id TEXT PRIMARY KEY,
                        workspace_path TEXT,
                        preview_url TEXT,
                        port INTEGER,
                        process_id INTEGER,
                        preview_status TEXT,
                        framework TEXT,
                        entry_point TEXT,
                        startup_timestamp TEXT,
                        updated_at TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_pipelines_user ON pipelines(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_pipelines_updated ON pipelines(updated_at DESC)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_failure_sig ON failure_memory(error_signature)")

                # Gracefully migrate existing sqlite tables if columns don't exist yet
                existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(failure_memory)").fetchall()]
                columns_to_add = [
                    ("error_category", "TEXT"),
                    ("affected_files", "JSON"),
                    ("git_diff", "TEXT"),
                    ("attempts", "INTEGER DEFAULT 1"),
                    ("tech_stack", "TEXT"),
                    ("verification_result", "TEXT"),
                ]
                for col_name, col_type in columns_to_add:
                    if col_name not in existing_cols:
                        try:
                            conn.execute(f"ALTER TABLE failure_memory ADD COLUMN {col_name} {col_type}")
                        except Exception:
                            pass

                conn.execute("CREATE INDEX IF NOT EXISTS idx_failure_cat ON failure_memory(error_category)")
        finally:
            conn.close()

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_create, pipeline)

    def _sync_create(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        pipeline_id = pipeline["task"]["id"]
        user_id = pipeline["task"].get("user_id")
        status = pipeline.get("status", "running")
        progress = pipeline.get("progress", 0)
        updated_at = pipeline.get("updated_at", datetime.now(UTC).isoformat())

        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO pipelines (id, user_id, status, progress, updated_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
                    (pipeline_id, user_id, status, progress, updated_at, json.dumps(pipeline)),
                )
            return deepcopy(pipeline)
        finally:
            conn.close()

    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]:
        return await self.create(pipeline)

    async def get(self, pipeline_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get, pipeline_id)

    def _sync_get(self, pipeline_id: str) -> dict[str, Any] | None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT payload FROM pipelines WHERE id = ?", (pipeline_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    async def list(self, limit: int = 20, user_id: str | None = None) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list, limit, user_id)

    def _sync_list(self, limit: int, user_id: str | None) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            if user_id:
                cursor = conn.execute(
                    "SELECT payload FROM pipelines WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                    (user_id, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT payload FROM pipelines ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [json.loads(r[0]) for r in rows]
        finally:
            conn.close()

    async def save_failure_memory(self, record: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_save_failure, record)

    def _sync_save_failure(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        now_iso = datetime.now(UTC).isoformat()
        item.setdefault("created_at", now_iso)
        item.setdefault("healed_at", now_iso)

        files_mod = json.dumps(item.get("files_modified", []))
        affected_files_json = json.dumps(item.get("affected_files", []))
        success_int = 1 if item.get("success", False) else 0

        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO failure_memory
                    (failure_id, pipeline_id, user_id, failed_agent, error_category, error_signature, error_message,
                     stack_trace_hash, affected_component, affected_files, git_diff, root_cause, fix_description,
                     files_modified, attempts, tech_stack, verification_result, success, healed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["failure_id"],
                        item.get("pipeline_id"),
                        item.get("user_id"),
                        item.get("failed_agent"),
                        item.get("error_category"),
                        item.get("error_signature"),
                        item.get("error_message"),
                        item.get("stack_trace_hash"),
                        item.get("affected_component"),
                        affected_files_json,
                        item.get("git_diff"),
                        item.get("root_cause"),
                        item.get("fix_description"),
                        files_mod,
                        int(item.get("attempts", 1)),
                        item.get("tech_stack"),
                        item.get("verification_result", "PASS" if success_int == 1 else "FAIL"),
                        success_int,
                        item.get("healed_at"),
                        item.get("created_at"),
                    ),
                )
            return item
        finally:
            conn.close()

    async def list_failure_memory(self, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list_failures, limit)

    def _sync_list_failures(self, limit: int) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT failure_id, pipeline_id, user_id, failed_agent, error_signature, error_message,
                       stack_trace_hash, affected_component, root_cause, fix_description, files_modified,
                       success, healed_at, created_at, error_category, git_diff, verification_result, attempts
                FROM failure_memory ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "failure_id": r[0],
                    "pipeline_id": r[1],
                    "user_id": r[2],
                    "failed_agent": r[3],
                    "error_signature": r[4],
                    "error_message": r[5],
                    "stack_trace_hash": r[6],
                    "affected_component": r[7],
                    "root_cause": r[8],
                    "healing_action": r[9],
                    "fix_description": r[9],
                    "files_modified": json.loads(r[10]) if r[10] else [],
                    "success": bool(r[11]),
                    "status": "healed" if r[11] else "failed",
                    "healed_at": r[12],
                    "created_at": r[13],
                    "error_category": r[14],
                    "git_diff": r[15],
                    "verification_result": r[16],
                    "attempts": r[17] if len(r) > 17 else 1,
                    "db_persisted": True,
                })
            return results
        finally:
            conn.close()

    async def find_matching_healing_pattern(self, error_signature: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_find_pattern, error_signature)

    def _sync_find_pattern(self, error_signature: str) -> dict[str, Any] | None:
        conn = sqlite3.connect(self.db_path)
        try:
            # Query verified-only solutions: success = 1 and verification_result != 'FAIL'
            cursor = conn.execute(
                """
                SELECT failure_id, pipeline_id, failed_agent, error_signature, root_cause,
                       fix_description, files_modified, success, healed_at, error_category, git_diff
                FROM failure_memory 
                WHERE success = 1 AND (verification_result IS NULL OR verification_result != 'FAIL')
                ORDER BY created_at DESC LIMIT 50
                """
            )
            sig_lower = error_signature.lower()
            for r in cursor.fetchall():
                known_sig = (r[3] or "").lower()
                known_cat = (r[9] or "").lower()
                if known_sig in sig_lower or sig_lower in known_sig or (known_cat and known_cat in sig_lower):
                    return {
                        "failure_id": r[0],
                        "pipeline_id": r[1],
                        "failed_agent": r[2],
                        "error_signature": r[3],
                        "root_cause": r[4],
                        "fix_description": r[5],
                        "files_modified": json.loads(r[6]) if r[6] else [],
                        "success": bool(r[7]),
                        "healed_at": r[8],
                        "error_category": r[9],
                        "git_diff": r[10],
                    }
            return None
        finally:
            conn.close()

    async def save_preview_metadata(self, record: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_save_preview, record)

    def _sync_save_preview(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        now_iso = datetime.now(UTC).isoformat()
        item.setdefault("updated_at", now_iso)
        item.setdefault("startup_timestamp", now_iso)
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO mission_previews
                    (mission_id, workspace_path, preview_url, port, process_id, preview_status, framework, entry_point, startup_timestamp, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("mission_id"),
                        item.get("workspace_path"),
                        item.get("preview_url"),
                        item.get("port"),
                        item.get("process_id") or item.get("pid"),
                        item.get("preview_status") or item.get("status"),
                        item.get("framework"),
                        item.get("entry_point"),
                        item.get("startup_timestamp"),
                        item.get("updated_at"),
                    ),
                )
            return item
        finally:
            conn.close()

    async def get_preview_metadata(self, mission_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get_preview, mission_id)

    def _sync_get_preview(self, mission_id: str) -> dict[str, Any] | None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT mission_id, workspace_path, preview_url, port, process_id, preview_status, framework, entry_point, startup_timestamp, updated_at
                FROM mission_previews WHERE mission_id = ?
                """,
                (mission_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "mission_id": row[0],
                "workspace_path": row[1],
                "preview_url": row[2],
                "port": row[3],
                "process_id": row[4],
                "pid": row[4],
                "preview_status": row[5],
                "status": row[5],
                "framework": row[6],
                "entry_point": row[7],
                "startup_timestamp": row[8],
                "updated_at": row[9],
            }
        finally:
            conn.close()

    async def close(self) -> None:
        return None


class MongoPipelineRepository:
    """MongoDB implementation used in persistent environments."""

    storage_name = "mongodb"

    def __init__(self, url: str, database_name: str) -> None:
        if AsyncIOMotorClient is None:
            raise RuntimeError("MongoDB support requires the 'motor' package. Install backend requirements first.")
        self.url = url
        self.database_name = database_name
        self.client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=2500)
        self.db = self.client[database_name]
        self.pipelines_coll = self.db["pipeline_history"]
        self.failures_coll = self.db["failure_memory"]
        self.previews_coll = self.db["mission_previews"]

    async def init(self) -> None:
        """Create indexes according to the autonomous DevOps swarm schema."""
        try:
            await self.pipelines_coll.create_index("task.id", unique=True)
            await self.pipelines_coll.create_index("pipeline_id")
            await self.pipelines_coll.create_index("updated_at")
            await self.pipelines_coll.create_index("task.user_id")

            await self.failures_coll.create_index("failure_id", unique=True)
            await self.failures_coll.create_index("pipeline_id")
            await self.failures_coll.create_index("error_signature")
            await self.failures_coll.create_index("error_category")
            await self.failures_coll.create_index("created_at")

            await self.previews_coll.create_index("mission_id", unique=True)
        except Exception:
            pass

    async def get_status(self) -> dict[str, Any]:
        """Verify real connectivity to MongoDB and return collection statistics."""
        import time
        t0 = time.perf_counter()
        try:
            await self.db.command("ping")
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            p_count = await self.pipelines_coll.count_documents({})
            f_count = await self.failures_coll.count_documents({})
            u_count = await self.db["users"].count_documents({}) if "users" in await self.db.list_collection_names() else 0
            
            # Mask credentials if present
            masked_url = self.url
            if "@" in self.url:
                prefix = self.url.split("@")[0].split("://")[0] + "://***:***@"
                suffix = self.url.split("@")[1]
                masked_url = prefix + suffix

            counts = {
                "pipeline_history": p_count,
                "failure_memory": f_count,
                "users": u_count,
            }

            return {
                "status": "connected",
                "connected": True,
                "storage": self.storage_name,
                "storage_type": "mongodb",
                "database_name": self.database_name,
                "url": masked_url,
                "ping_ms": latency_ms,
                "ping_latency_ms": latency_ms,
                "collections": ["pipeline_history", "failure_memory", "users"],
                "counts": counts,
                "document_counts": counts,
            }
        except Exception as exc:
            return {
                "status": "disconnected",
                "connected": False,
                "storage": self.storage_name,
                "storage_type": "mongodb",
                "database_name": self.database_name,
                "error": str(exc),
                "setup_instructions": "Ensure MongoDB is running locally on port 27017 or set MONGODB_URL in backend/.env.",
                "instructions": "Ensure MongoDB is running locally on port 27017 or set MONGODB_URL in backend/.env.",
            }

    def _normalize_pipeline_doc(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        doc = deepcopy(pipeline)
        task = doc.get("task", {})
        pipeline_id = task.get("id") or doc.get("pipeline_id") or "unknown"
        stages = doc.get("stages", [])

        # Build and test summary extraction
        build_stage = next((s for s in stages if s.get("agent") == "Build Agent"), None)
        test_stage = next((s for s in stages if s.get("agent") == "Testing Agent"), None)
        deploy_stage = next((s for s in stages if s.get("agent") == "Deploy Agent"), None)

        build_results = build_stage.get("output") if build_stage else None
        test_results = test_stage.get("output") if test_stage else None
        deploy_results = deploy_stage.get("output") if deploy_stage else None

        # Section 6.A Pipeline History schema normalization
        doc["pipeline_id"] = pipeline_id
        doc["mission_description"] = task.get("request") or doc.get("mission_description") or ""
        doc["project_identifier"] = task.get("project_id") or pipeline_id
        doc["pipeline_status"] = doc.get("status", "running")
        doc["current_stage"] = doc.get("current_agent")
        doc["agent_execution_results"] = stages
        doc["build_results"] = build_results
        doc["test_results"] = test_results
        doc["deployment_result"] = deploy_results
        doc["execution_logs"] = doc.get("logs", [])
        doc["start_timestamp"] = task.get("created_at") or doc.get("created_at")
        doc["end_timestamp"] = doc.get("updated_at")
        
        # Calculate total duration if available
        if doc.get("start_timestamp") and doc.get("end_timestamp"):
            try:
                t_start = datetime.fromisoformat(doc["start_timestamp"])
                t_end = datetime.fromisoformat(doc["end_timestamp"])
                doc["total_execution_duration"] = round((t_end - t_start).total_seconds(), 2)
            except Exception:
                pass
        
        return doc

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        doc = self._normalize_pipeline_doc(pipeline)
        await self.pipelines_coll.replace_one({"task.id": doc["task"]["id"]}, deepcopy(doc), upsert=True)
        return pipeline

    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]:
        doc = self._normalize_pipeline_doc(pipeline)
        await self.pipelines_coll.replace_one({"task.id": pipeline_id}, deepcopy(doc), upsert=True)
        return pipeline

    async def get(self, pipeline_id: str) -> dict[str, Any] | None:
        doc = await self.pipelines_coll.find_one({"$or": [{"task.id": pipeline_id}, {"pipeline_id": pipeline_id}]}, {"_id": 0})
        return doc

    async def list(self, limit: int = 20, user_id: str | None = None) -> list[dict[str, Any]]:
        query = {"task.user_id": user_id} if user_id else {}
        cursor = self.pipelines_coll.find(query, {"_id": 0}).sort("updated_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def save_failure_memory(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        now_iso = datetime.now(UTC).isoformat()
        item.setdefault("created_at", now_iso)
        item.setdefault("healed_at", now_iso)
        item.setdefault("timestamp", now_iso)

        # Section 6.B Failure Memory schema normalization
        item["agent_name"] = item.get("failed_agent") or item.get("agent_name")
        item["failed_stage"] = item.get("failed_stage") or item.get("failed_agent")
        item["error_type"] = item.get("error_category") or item.get("error_type")
        item["corrective_action_attempted"] = item.get("fix_description") or item.get("healing_action")
        item["retry_count"] = item.get("attempts", 1)
        item["recovery_status"] = item.get("status") or ("healed" if item.get("success") else "failed")
        item["diagnostic_details"] = {
            "error_signature": item.get("error_signature"),
            "stack_trace_hash": item.get("stack_trace_hash"),
            "root_cause": item.get("root_cause"),
            "affected_component": item.get("affected_component"),
            "git_diff": item.get("git_diff"),
        }

        await self.failures_coll.replace_one({"failure_id": item["failure_id"]}, deepcopy(item), upsert=True)
        item.pop("_id", None)
        return item

    async def list_failure_memory(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self.failures_coll.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def list_failures(self, limit: int = 50, user_id: str | None = None) -> list[dict[str, Any]]:
        query = {"user_id": user_id} if user_id else {}
        cursor = self.failures_coll.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_matching_healing_pattern(self, error_signature: str) -> dict[str, Any] | None:
        escaped_sig = re.escape(error_signature)
        return await self.failures_coll.find_one(
            {"error_signature": {"$regex": escaped_sig, "$options": "i"}, "success": True},
            {"_id": 0}
        )

    async def save_preview_metadata(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        now_iso = datetime.now(UTC).isoformat()
        item.setdefault("updated_at", now_iso)
        item.setdefault("startup_timestamp", now_iso)
        await self.previews_coll.replace_one({"mission_id": item["mission_id"]}, deepcopy(item), upsert=True)
        item.pop("_id", None)
        return item

    async def get_preview_metadata(self, mission_id: str) -> dict[str, Any] | None:
        return await self.previews_coll.find_one({"mission_id": mission_id}, {"_id": 0})

    async def close(self) -> None:
        self.client.close()


def _is_mongo_reachable(url: str, timeout_ms: int = 400) -> bool:
    try:
        from pymongo import MongoClient
        client = MongoClient(url, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command('ping')
        client.close()
        return True
    except Exception:
        return False


def get_sqlite_db_path() -> str:
    """Return the absolute path to the SQLite devops_swarm.db file."""
    env_path = os.getenv("SQLITE_DATABASE_PATH") or os.getenv("SQLITE_DB_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_absolute():
            return str(p)
        if p.exists():
            return str(p.resolve())
        backend_p = Path(__file__).resolve().parent.parent.parent / env_path
        if backend_p.exists():
            return str(backend_p.resolve())
        return str((Path(__file__).resolve().parent.parent.parent / env_path).resolve())
    return str((Path(__file__).resolve().parent.parent.parent / "devops_swarm.db").resolve())


def create_pipeline_repository() -> PipelineRepository:
    """Select persistence engine: MongoDB if configured and reachable, else SQLite."""
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
    except Exception:
        pass

    mongo_url = os.getenv("MONGODB_URL")
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")
    sqlite_path = get_sqlite_db_path()

    if mongo_url and not use_sqlite:
        if _is_mongo_reachable(mongo_url):
            try:
                return MongoPipelineRepository(mongo_url, os.getenv("MONGODB_DATABASE", "devops_swarm"))
            except Exception:
                pass

    return SQLitePipelineRepository(sqlite_path)


class UserRepository(Protocol):
    storage_name: str

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]: ...
    async def get_by_email(self, email: str) -> dict[str, Any] | None: ...
    async def get_by_id(self, user_id: str) -> dict[str, Any] | None: ...
    async def close(self) -> None: ...


class InMemoryUserRepository:
    """Safe development fallback storing user records in memory."""

    storage_name = "in-memory (users)"

    def __init__(self) -> None:
        self._users_by_id: dict[str, dict[str, Any]] = {}
        self._users_by_email: dict[str, dict[str, Any]] = {}

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        email_key = user_data["email"].lower().strip()
        if email_key in self._users_by_email:
            raise DuplicateUserError(f"User with email '{user_data['email']}' already exists.")
        user = deepcopy(user_data)
        user.setdefault("created_at", datetime.now(UTC).isoformat())
        self._users_by_id[user["id"]] = user
        self._users_by_email[email_key] = user
        return deepcopy(user)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        user = self._users_by_email.get(email.lower().strip())
        return deepcopy(user) if user else None

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        user = self._users_by_id.get(user_id)
        return deepcopy(user) if user else None

    async def list_users(self) -> list[dict[str, Any]]:
        return list(self._users_by_id.values())

    async def close(self) -> None:
        return None


class SqliteUserRepository:
    """SQLite implementation for local user storage."""

    storage_name = "sqlite (users)"

    def __init__(self, db_path: str = "devops_swarm.db") -> None:
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.commit()

    async def init_indexes(self) -> None:
        """Indexes are ensured synchronously in _init_db."""
        return None

    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._create_user_sync, user)

    def _create_user_sync(self, user: dict[str, Any]) -> dict[str, Any]:
        full_name = (user.get("full_name") or user.get("name") or "").strip()
        password_hash = user.get("password_hash") or user.get("hashed_password") or ""
        email = user["email"].strip().lower()
        user_id = user["id"]
        created_at = user.get("created_at", datetime.now(UTC).isoformat())
        updated_at = user.get("updated_at", created_at)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (id, email, full_name, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, email, full_name, password_hash, created_at, updated_at),
                )
                conn.commit()
                res = deepcopy(user)
                res.setdefault("full_name", full_name)
                res.setdefault("name", full_name)
                res.setdefault("password_hash", password_hash)
                res.setdefault("hashed_password", password_hash)
                return res
            except sqlite3.IntegrityError as exc:
                raise DuplicateUserError(f"User with email '{user['email']}' already exists.") from exc

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_by_email_sync, email)

    def _get_by_email_sync(self, email: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res.setdefault("name", res.get("full_name", ""))
            res.setdefault("hashed_password", res.get("password_hash", ""))
            return res

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_by_id_sync, user_id)

    def _get_by_id_sync(self, user_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res.setdefault("name", res.get("full_name", ""))
            res.setdefault("hashed_password", res.get("password_hash", ""))
            return res

    async def list_users(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_users_sync)

    def _list_users_sync(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            records = []
            for row in cursor.fetchall():
                r = dict(row)
                r.setdefault("name", r.get("full_name", ""))
                r.setdefault("hashed_password", r.get("password_hash", ""))
                records.append(r)
            return records

    async def close(self) -> None:
        return None


class MongoUserRepository:
    """MongoDB implementation for permanent user persistence when MongoDB is running."""

    storage_name = "mongodb (users)"

    def __init__(self, url: str, database_name: str) -> None:
        if AsyncIOMotorClient is None:
            raise RuntimeError("MongoDB support requires the 'motor' package.")
        self.client = AsyncIOMotorClient(url)
        self.db = self.client[database_name]
        self.users_coll = self.db["users"]

    async def init_indexes(self) -> None:
        try:
            await self.users_coll.create_index("email", unique=True)
        except Exception:
            pass

    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        doc = deepcopy(user)
        doc["email"] = doc["email"].strip().lower()
        try:
            await self.users_coll.insert_one(doc)
        except Exception as exc:
            raise DuplicateUserError(f"User with email '{user['email']}' already exists.") from exc
        doc.pop("_id", None)
        return doc

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await self.users_coll.find_one({"email": email.strip().lower()}, {"_id": 0})

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await self.users_coll.find_one({"id": user_id}, {"_id": 0})

    async def list_users(self) -> list[dict[str, Any]]:
        cursor = self.users_coll.find({}, {"_id": 0}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def close(self) -> None:
        self.client.close()


def create_user_repository() -> UserRepository:
    mongo_url = os.getenv("MONGODB_URL")
    if mongo_url and _is_mongo_reachable(mongo_url):
        return MongoUserRepository(mongo_url, os.getenv("MONGODB_DATABASE", "devops_swarm"))
    return SqliteUserRepository(get_sqlite_db_path())

