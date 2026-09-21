"""Small OpenAI-compatible client for NVIDIA NIM chat models."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class NvidiaNimClient:
    """Call NVIDIA's hosted inference API without adding a runtime dependency."""

    base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    default_model = "meta/llama-3.3-70b-instruct"

    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.model = os.getenv("NVIDIA_MODEL", self.default_model).strip()
        self.timeout_seconds = float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "45"))

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def create_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Request a JSON object and reject non-object model responses."""
        if not self.is_configured:
            raise RuntimeError("NVIDIA_API_KEY is not configured")

        payload = {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": 2500,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = await asyncio.to_thread(self._post, payload)
        try:
            content = response["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("NVIDIA returned an invalid JSON agent response") from exc
        if not isinstance(result, dict):
            raise RuntimeError("NVIDIA returned a JSON value instead of an object")
        return result

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310: fixed HTTPS endpoint
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"NVIDIA API returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach NVIDIA API: {exc.reason}") from exc
