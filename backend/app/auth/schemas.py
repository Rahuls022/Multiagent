"""Pydantic schemas for user registration, authentication, and profiles."""

from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field, field_validator


class UserRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100, description="Full name of user")
    email: str = Field(min_length=3, max_length=150, description="Unique email address for login")
    password: str = Field(min_length=6, max_length=128, description="Secure password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", clean):
            raise ValueError("Invalid email format")
        return clean


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
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", clean):
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
    email: str = Field(min_length=3, max_length=150, description="Registered email address")
    password: str = Field(min_length=1, description="Account password")
    remember_me: bool = Field(default=False, description="Whether to remember session across browser restarts")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", clean):
            raise ValueError("Invalid email format")
        domain = clean.split("@")[-1]
        if domain.startswith("gmail.") and domain != "gmail.com":
            raise ValueError("Only valid Gmail addresses ending with @gmail.com are allowed")
        return clean


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str
    name: str = ""
    full_name: str = ""

    def __init__(self, **data: Any) -> None:
        if "full_name" in data and not data.get("name"):
            data["name"] = data["full_name"]
        elif "name" in data and not data.get("full_name"):
            data["full_name"] = data["name"]
        super().__init__(**data)

    def model_post_init(self, __context: Any) -> None:
        if not self.full_name and self.name:
            self.full_name = self.name
        if not self.name and self.full_name:
            self.name = self.full_name


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 86400
