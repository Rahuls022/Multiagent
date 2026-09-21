"""HTTP request models for the dashboard API."""

from pydantic import BaseModel, Field


class PipelineRequest(BaseModel):
    request: str = Field(min_length=3, max_length=500, examples=["Build a student management portal"])
