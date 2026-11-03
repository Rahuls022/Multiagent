"""HTTP request and response models for the dashboard and authentication API."""

from __future__ import annotations

import re
from pydantic import BaseModel, Field, field_validator


class PipelineRequest(BaseModel):
    request: str = Field(min_length=3, max_length=500, examples=["Build a student management portal"])
    project_id: str | None = Field(default=None, description="Optional target project workspace ID")


class WorkspaceFileUpdateRequest(BaseModel):
    project_id: str = Field(..., description="Project workspace identifier")
    path: str = Field(..., description="Relative path of the file to write or update")
    content: str = Field(..., description="Source code or text content to write")


class WorkspaceGenerateRequest(BaseModel):
    request: str = Field(min_length=3, max_length=500, description="Mission specification")
    project_id: str | None = Field(default=None, description="Optional target project workspace ID")


EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserSignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Please provide a valid email address (e.g. user@example.com)")
        domain = clean.split("@")[-1]
        if domain.startswith("gmail.") and domain != "gmail.com":
            raise ValueError("Only valid Gmail addresses ending with @gmail.com are allowed")
        return clean

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        password = info.data.get("password")
        if password is not None and v != password:
            raise ValueError("Passwords do not match")
        return v


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Whether to remember session across browser restarts")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Please provide a valid email address")
        domain = clean.split("@")[-1]
        if domain.startswith("gmail.") and domain != "gmail.com":
            raise ValueError("Only valid Gmail addresses ending with @gmail.com are allowed")
        return clean


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int
