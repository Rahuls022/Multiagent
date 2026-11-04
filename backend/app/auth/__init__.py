"""Authentication and user safety package."""

from .dependencies import get_current_user, get_optional_user
from .repository import (
    InMemoryUserRepository,
    MongoUserRepository,
    UserRepository,
    create_user_repository,
)
from .schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from .security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

__all__ = [
    "get_current_user",
    "get_optional_user",
    "UserRepository",
    "InMemoryUserRepository",
    "MongoUserRepository",
    "create_user_repository",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]
