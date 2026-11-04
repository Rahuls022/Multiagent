"""Authentication and user safety package."""

from .dependencies import get_current_user, get_optional_user
from .repository import (
    DuplicateUserError,
    InMemoryUserRepository,
    MongoUserRepository,
    SqliteUserRepository,
    UserRepository,
    create_user_repository,
)
from .schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserSignupRequest,
    UserResponse,
)
from app.schemas import UserSignupRequest
from .security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

__all__ = [
    "get_current_user",
    "get_optional_user",
    "DuplicateUserError",
    "SqliteUserRepository",
    "UserRepository",
    "InMemoryUserRepository",
    "MongoUserRepository",
    "SqliteUserRepository",
    "create_user_repository",
    "UserRegisterRequest",
    "UserSignupRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]
