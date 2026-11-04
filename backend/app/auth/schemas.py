"""Pydantic schemas for user registration, authentication, and profiles."""

from __future__ import annotations

import re
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


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150, description="Registered email address")
    password: str = Field(min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", clean):
            raise ValueError("Invalid email format")
        return clean


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
