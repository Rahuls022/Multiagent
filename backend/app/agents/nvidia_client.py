"""Backwards-compatible adapter connecting NvidiaNimClient to unified LLMClient."""

from __future__ import annotations

from typing import Any

from app.llm import LLMClient


class NvidiaNimClient:
    """Adapter maintaining compatibility while routing to unified LLMClient."""

    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client or LLMClient()
        self.model = self._client.model
        self.api_key = self._client.api_key
        self.timeout_seconds = self._client.timeout_seconds

    @property
    def is_configured(self) -> bool:
        return self._client.is_configured

    async def create_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Request structured JSON using the configured LLM provider."""
        return await self._client.create_json(system_prompt=system_prompt, user_prompt=user_prompt)

