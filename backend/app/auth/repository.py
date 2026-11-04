"""User repository implementation supporting MongoDB and in-memory development fallback."""

from __future__ import annotations

import os
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Protocol

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = None  # type: ignore[assignment,misc]


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
            raise ValueError(f"User with email '{user_data['email']}' already exists.")
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

    async def close(self) -> None:
        return None


class MongoUserRepository:
    """Persistent user repository using MongoDB."""

    storage_name = "mongodb (users)"

    def __init__(self, url: str, database_name: str) -> None:
        if AsyncIOMotorClient is None:
            raise RuntimeError("MongoDB support requires the 'motor' package.")
        self.client = AsyncIOMotorClient(url)
        self.db = self.client[database_name]
        self.users_coll = self.db["users"]

    async def init_indexes(self) -> None:
        """Ensure unique index on email."""
        await self.users_coll.create_index("email", unique=True)

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        user = deepcopy(user_data)
        user["email"] = user["email"].lower().strip()
        user.setdefault("created_at", datetime.now(UTC).isoformat())
        existing = await self.get_by_email(user["email"])
        if existing:
            raise ValueError(f"User with email '{user['email']}' already exists.")
        await self.users_coll.insert_one(deepcopy(user))
        user.pop("_id", None)
        return user

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await self.users_coll.find_one({"email": email.lower().strip()}, {"_id": 0})

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await self.users_coll.find_one({"id": user_id}, {"_id": 0})

    async def close(self) -> None:
        self.client.close()


def create_user_repository() -> UserRepository:
    """Create MongoDB or InMemory user repository based on environment."""
    mongo_url = os.getenv("MONGODB_URL")
    if mongo_url:
        try:
            from app.database.repository import _is_mongo_reachable
            if _is_mongo_reachable(mongo_url):
                return MongoUserRepository(mongo_url, os.getenv("MONGODB_DATABASE", "devops_swarm"))
        except Exception:
            pass
    return InMemoryUserRepository()
