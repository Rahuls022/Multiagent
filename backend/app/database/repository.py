"""Repository boundary for pipeline history and failure memory storage."""

from __future__ import annotations

import os
from copy import deepcopy
import asyncio
import sqlite3
from pathlib import Path
from datetime import UTC, datetime
from typing import Any, Protocol

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:  # Unit tests and in-memory development do not need MongoDB installed.
    AsyncIOMotorClient = None  # type: ignore[assignment,misc]


class PipelineRepository(Protocol):
    storage_name: str

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]: ...
    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]: ...
    async def get(self, pipeline_id: str) -> dict[str, Any] | None: ...
    async def list(self, limit: int = 20) -> list[dict[str, Any]]: ...

    # Self-Healing Failure Memory API
    async def save_failure_memory(self, record: dict[str, Any]) -> dict[str, Any]: ...
    async def list_failure_memory(self, limit: int = 50) -> list[dict[str, Any]]: ...
    async def find_matching_healing_pattern(self, error_signature: str) -> dict[str, Any] | None: ...

    async def close(self) -> None: ...


class InMemoryPipelineRepository:
    """Safe development fallback; data is stored in memory for dev session."""

    storage_name = "in-memory (temporary)"

    def __init__(self) -> None:
        self._pipelines: dict[str, dict[str, Any]] = {}
        self._failures: list[dict[str, Any]] = []

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        self._pipelines[pipeline["task"]["id"]] = deepcopy(pipeline)
        return deepcopy(pipeline)

    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]:
        self._pipelines[pipeline_id] = deepcopy(pipeline)
        return deepcopy(pipeline)

    async def get(self, pipeline_id: str) -> dict[str, Any] | None:
        pipeline = self._pipelines.get(pipeline_id)
        return deepcopy(pipeline) if pipeline else None

    async def list(self, limit: int = 20) -> list[dict[str, Any]]:
        values = sorted(self._pipelines.values(), key=lambda item: item["updated_at"], reverse=True)
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
            if fail.get("error_signature", "").lower() in sig_lower or sig_lower in fail.get("error_signature", "").lower():
                return deepcopy(fail)
        return None

    async def close(self) -> None:
        return None


class MongoPipelineRepository:
    """MongoDB implementation used in persistent local and deployed environments."""

    storage_name = "mongodb"

    def __init__(self, url: str, database_name: str) -> None:
        if AsyncIOMotorClient is None:
            raise RuntimeError("MongoDB support requires the 'motor' package. Install backend requirements first.")
        self.client = AsyncIOMotorClient(url)
        self.db = self.client[database_name]
        self.pipelines_coll = self.db["pipeline_history"]
        self.failures_coll = self.db["failure_memory"]

    async def create(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        await self.pipelines_coll.insert_one(deepcopy(pipeline))
        return pipeline

    async def update(self, pipeline_id: str, pipeline: dict[str, Any]) -> dict[str, Any]:
        await self.pipelines_coll.replace_one({"task.id": pipeline_id}, deepcopy(pipeline), upsert=True)
        return pipeline

    async def get(self, pipeline_id: str) -> dict[str, Any] | None:
        return await self.pipelines_coll.find_one({"task.id": pipeline_id}, {"_id": 0})

    async def list(self, limit: int = 20) -> list[dict[str, Any]]:
        cursor = self.pipelines_coll.find({}, {"_id": 0}).sort("updated_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def save_failure_memory(self, record: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(record)
        item.setdefault("created_at", datetime.now(UTC).isoformat())
        await self.failures_coll.insert_one(deepcopy(item))
        item.pop("_id", None)
        return item

    async def list_failure_memory(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self.failures_coll.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_matching_healing_pattern(self, error_signature: str) -> dict[str, Any] | None:
        return await self.failures_coll.find_one(
            {"error_signature": {"$regex": error_signature, "$options": "i"}},
            {"_id": 0}
        )

    async def close(self) -> None:
        self.client.close()


def create_pipeline_repository() -> PipelineRepository:
    """Use MongoDB when configured; keep local development usable otherwise."""
    mongo_url = os.getenv("MONGODB_URL")
    if mongo_url:
        return MongoPipelineRepository(mongo_url, os.getenv("MONGODB_DATABASE", "devops_swarm"))
    return InMemoryPipelineRepository()


class UserRepository(Protocol):
    storage_name: str

    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]: ...
    async def get_by_email(self, email: str) -> dict[str, Any] | None: ...
    async def get_by_id(self, user_id: str) -> dict[str, Any] | None: ...
    async def list_users(self) -> list[dict[str, Any]]: ...
    async def close(self) -> None: ...


class InMemoryUserRepository:
    storage_name = "in-memory (temporary)"

    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {}

    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        email = user["email"].strip().lower()
        for existing in self._users.values():
            if existing["email"].lower() == email:
                raise ValueError("Duplicate email")
        doc = deepcopy(user)
        doc["email"] = email
        self._users[user["id"]] = doc
        return deepcopy(doc)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        email_clean = email.strip().lower()
        for user in self._users.values():
            if user["email"].lower() == email_clean:
                return deepcopy(user)
        return None

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        user = self._users.get(user_id)
        return deepcopy(user) if user else None

    async def list_users(self) -> list[dict[str, Any]]:
        return [deepcopy(u) for u in self._users.values()]

    async def close(self) -> None:
        return None


class SqliteUserRepository:
    """SQLite implementation providing permanent local user persistence."""

    storage_name = "sqlite"

    def __init__(self, db_path: str = "devops_swarm.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.commit()

    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._create_user_sync, user)

    def _create_user_sync(self, user: dict[str, Any]) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (id, email, full_name, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user["id"],
                    user["email"].strip().lower(),
                    user["full_name"].strip(),
                    user["password_hash"],
                    user.get("created_at", datetime.now(UTC).isoformat()),
                    user.get("updated_at", datetime.now(UTC).isoformat()),
                ),
            )
            conn.commit()
            return deepcopy(user)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_by_email_sync, email)

    def _get_by_email_sync(self, email: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_by_id_sync, user_id)

    def _get_by_id_sync(self, user_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def list_users(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_users_sync)

    def _list_users_sync(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    async def close(self) -> None:
        return None


class MongoUserRepository:
    """MongoDB implementation for permanent user persistence when MongoDB is running."""

    storage_name = "mongodb"

    def __init__(self, url: str, database_name: str) -> None:
        if AsyncIOMotorClient is None:
            raise RuntimeError("MongoDB support requires the 'motor' package. Install backend requirements first.")
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
        await self.users_coll.insert_one(doc)
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
    """Use MongoDB when configured; use SQLite for real persistent local storage otherwise."""
    mongo_url = os.getenv("MONGODB_URL")
    if mongo_url:
        return MongoUserRepository(mongo_url, os.getenv("MONGODB_DATABASE", "devops_swarm"))
    default_db_path = str(Path(__file__).resolve().parent.parent.parent / "devops_swarm.db")
    db_path = os.getenv("SQLITE_DATABASE_PATH", default_db_path)
    return SqliteUserRepository(db_path)
