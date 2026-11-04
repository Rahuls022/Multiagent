"""User repository exports and implementations supporting SQLite, MongoDB, and in-memory development fallback."""

from __future__ import annotations

from app.database.repository import (
    DuplicateUserError,
    InMemoryUserRepository,
    MongoUserRepository,
    SqliteUserRepository,
    UserRepository,
    create_user_repository,
    get_sqlite_db_path,
)

__all__ = [
    "DuplicateUserError",
    "InMemoryUserRepository",
    "MongoUserRepository",
    "SqliteUserRepository",
    "UserRepository",
    "create_user_repository",
    "get_sqlite_db_path",
]
