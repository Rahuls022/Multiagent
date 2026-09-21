"""Repository boundary for pipeline history and failure memory storage."""

from __future__ import annotations

import os
from copy import deepcopy
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
