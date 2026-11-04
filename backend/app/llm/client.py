"""Unified provider abstraction for calling LLM inference APIs with structured output."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
    else:
        load_dotenv()
except Exception:
    pass

logger = logging.getLogger("autonomous_devops.llm")


def _repair_multiline_quotes(text: str) -> str:
    """Convert Python-style triple quotes inside JSON to properly escaped JSON string literals."""
    def _replacer(m: re.Match) -> str:
        return json.dumps(m.group(1))

    # Match triple double-quotes or triple single-quotes
    text = re.sub(r'"""([\s\S]*?)"""', _replacer, text)
    text = re.sub(r"'''([\s\S]*?)'''", _replacer, text)
    return text


def _repair_code_fields(text: str) -> str:
    """Safely escape unescaped quotes and newlines inside "code": "..." properties."""
    parts = re.split(r'("code":\s*")', text)
    if len(parts) <= 1:
        return text
    result = [parts[0]]
    for i in range(1, len(parts), 2):
        tag = parts[i]
        rest = parts[i + 1]
        # Look for closing quote followed by comma/next field or closing brace
        end_match = re.search(r'"\s*(?:,\s*"\w+"|\s*\})', rest)
        if end_match:
            end_idx = end_match.start()
            raw_code = rest[:end_idx]
            after = rest[end_idx:]  # begins with the closing quote
            escaped_code = json.dumps(raw_code)
            result.append('"code": ' + escaped_code + after[1:])
        else:
            result.append(tag + rest)
    return "".join(result)


def extract_json(raw_text: str) -> dict[str, Any] | list[Any]:
    """Robustly extract JSON object or array from LLM completion text,

    handling markdown code fences (```json ... ```), Python-style triple quotes,
    unescaped newlines or internal quotes inside code strings, or conversational preamble.
    """
    raw_stripped = raw_text.strip()
    candidates_to_try = [
        raw_stripped,
        _repair_code_fields(raw_stripped),
        _repair_multiline_quotes(raw_stripped),
        _repair_code_fields(_repair_multiline_quotes(raw_stripped)),
    ]

    for text in candidates_to_try:
        # 1. Direct parse attempt (with strict=False to allow unescaped newlines in strings)
        try:
            data = json.loads(text, strict=False)
            if isinstance(data, (dict, list)):
                return data
        except (json.JSONDecodeError, ValueError):
            pass

        # 2. Markdown code block extraction
        fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(fence_pattern, text, flags=re.IGNORECASE)
        for candidate in matches:
            cleaned_candidate = candidate.strip()
            for cand_version in [
                cleaned_candidate,
                _repair_code_fields(cleaned_candidate),
                _repair_multiline_quotes(cleaned_candidate),
                _repair_code_fields(_repair_multiline_quotes(cleaned_candidate)),
            ]:
                try:
                    data = json.loads(cand_version, strict=False)
                    if isinstance(data, (dict, list)):
                        return data
                except (json.JSONDecodeError, ValueError):
                    continue

        # 3. Outer bracket search for JSON object or array
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            snippet = text[first_brace : last_brace + 1]
            try:
                data = json.loads(snippet, strict=False)
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, ValueError):
                pass

        first_bracket = text.find("[")
        last_bracket = text.rfind("]")
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            snippet = text[first_bracket : last_bracket + 1]
            try:
                data = json.loads(snippet, strict=False)
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, ValueError):
                pass

    raise ValueError(f"Could not parse valid JSON from LLM response:\n{raw_text[:500]}")


class BaseLLMProvider(ABC):
    """Abstract base provider for LLM API integration."""

    @abstractmethod
    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        response_format_json: bool = False,
    ) -> dict[str, Any]:
        """Perform completion returning raw response dictionary containing 'content', 'model', 'usage'."""


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for OpenAI, Groq, OpenRouter, Together, DeepSeek, vLLM, Ollama, and NVIDIA NIM."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: float = 180.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.extra_headers = extra_headers or {}

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        response_format_json: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format_json and "nvidia" not in self.base_url:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }

        return await asyncio.to_thread(self._post_with_retry, payload, headers)

    def _post_with_retry(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        max_retries = 3
        backoff = 1.5

        for attempt in range(1, max_retries + 1):
            request = Request(
                self.base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw_data = json.loads(response.read().decode("utf-8"))
                    content = raw_data["choices"][0]["message"]["content"]
                    usage = raw_data.get("usage", {})
                    return {
                        "content": content,
                        "model": raw_data.get("model", self.model),
                        "usage": usage,
                    }
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:600]
                status_code = exc.code

                if status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    sleep_time = backoff * (2 ** (attempt - 1))
                    logger.warning("LLM API returned %s. Retrying in %.1fs...", status_code, sleep_time)
                    import time
                    time.sleep(sleep_time)
                    continue

                clean_err = self._sanitize_error(body)
                raise RuntimeError(f"LLM API returned HTTP {status_code}: {clean_err}") from None
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < max_retries:
                    logger.warning("LLM request timed out or network error (%s). Retrying (attempt %d/%d)...", exc, attempt, max_retries)
                    import time
                    time.sleep(2.0 * attempt)
                    continue
                clean_msg = self._sanitize_error(str(exc))
                raise RuntimeError(f"Could not reach LLM endpoint ({self.base_url}): {clean_msg}") from None

        raise RuntimeError("LLM request failed after maximum retries.")

    def _sanitize_error(self, message: str) -> str:
        """Strip raw API key if present in error response."""
        if self.api_key and self.api_key in message:
            return message.replace(self.api_key, "[REDACTED_API_KEY]")
        return message


class GeminiProvider(BaseLLMProvider):
    """Native Google Gemini REST client."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", timeout_seconds: float = 60.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        response_format_json: bool = False,
    ) -> dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Directive:\n{system_prompt}\n\nUser Task:\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if response_format_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        headers = {"Content-Type": "application/json"}
        return await asyncio.to_thread(self._post, url, payload, headers)

    def _post(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
                candidate = data["candidates"][0]
                content = candidate["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata", {})
                return {"content": content, "model": self.model, "usage": usage}
        except HTTPError as exc:
            err = exc.read().decode("utf-8", errors="replace")[:600]
            if self.api_key in err:
                err = err.replace(self.api_key, "[REDACTED_API_KEY]")
            raise RuntimeError(f"Gemini API error (HTTP {exc.code}): {err}") from None
        except Exception as exc:
            raise RuntimeError(f"Failed to communicate with Gemini API: {exc}") from None


class LLMClient:
    """Universal client consumed across all swarm agents."""

    def __init__(
        self,
        provider_name: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        if provider_name is not None:
            self.provider_name = provider_name.lower().strip()
        else:
            self.provider_name = (os.getenv("LLM_PROVIDER") or self._detect_provider()).lower().strip()

        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = (
                os.getenv("LLM_API_KEY")
                or self._key_for_provider(self.provider_name)
                or ""
            ).strip()

        if model is not None:
            self.model = model.strip()
        else:
            self.model = (
                os.getenv("LLM_MODEL")
                or os.getenv("NVIDIA_MODEL")
                or self._default_model_for_provider(self.provider_name)
            ).strip()

        self.base_url = base_url if base_url is not None else os.getenv("LLM_BASE_URL")
        if timeout_seconds is not None:
            self.timeout_seconds = float(timeout_seconds)
        else:
            self.timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "180.0"))

        self._provider = self._build_provider()
        self.metrics = {
            "requests_count": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_latency_ms": 0.0,
            "estimated_cost_usd": 0.0,
        }

    def get_metrics(self) -> dict[str, Any]:
        """Return aggregated LLM telemetry metrics."""
        return deepcopy(self.metrics)

    def reset_metrics(self) -> None:
        """Reset telemetry metrics counters."""
        self.metrics = {
            "requests_count": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_latency_ms": 0.0,
            "estimated_cost_usd": 0.0,
        }

    def _record_metrics(self, resp: dict[str, Any], duration_ms: float) -> None:
        self.metrics["requests_count"] += 1
        self.metrics["total_latency_ms"] += duration_ms

        usage = resp.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens") or usage.get("promptTokenCount") or 0
        comp_tokens = usage.get("completion_tokens") or usage.get("candidatesTokenCount") or 0
        total_tokens = usage.get("total_tokens") or usage.get("totalTokenCount") or (prompt_tokens + comp_tokens)

        # Fallback estimation if provider doesn't report token counts (approx 4 chars per token)
        if total_tokens == 0 and resp.get("content"):
            comp_tokens = len(resp.get("content", "")) // 4
            total_tokens = comp_tokens

        self.metrics["prompt_tokens"] += prompt_tokens
        self.metrics["completion_tokens"] += comp_tokens
        self.metrics["total_tokens"] += total_tokens

        # Estimated cost calculation ($ per 1M tokens)
        rate_prompt = 0.20 / 1_000_000
        rate_comp = 0.20 / 1_000_000
        if "gpt-4o-mini" in self.model:
            rate_prompt, rate_comp = 0.15 / 1_000_000, 0.60 / 1_000_000
        elif "gpt-4o" in self.model:
            rate_prompt, rate_comp = 5.00 / 1_000_000, 15.00 / 1_000_000

        call_cost = (prompt_tokens * rate_prompt) + (comp_tokens * rate_comp)
        self.metrics["estimated_cost_usd"] += call_cost

    def _is_mock(self) -> bool:
        """Return True if this client subclass or injected provider is a mock / test double."""
        if type(self) is not LLMClient:
            return True
        provider = getattr(self, "_provider", None)
        if provider is not None:
            if not isinstance(provider, BaseLLMProvider):
                return True
            if hasattr(provider, "_mock_return_value") or hasattr(provider, "mock_calls"):
                return True
            cls_name = type(provider).__name__.lower()
            if "mock" in cls_name or cls_name.startswith("fake"):
                return True
        return False

    @property
    def is_configured(self) -> bool:
        if self._is_mock():
            return True
        if os.getenv("LLM_OFFLINE", "0").lower() in ("1", "true", "yes"):
            return False
        if self.provider_name in ("ollama", "local"):
            return True
        return bool(self.api_key)

    def verify_configured(self) -> None:
        """Ensure LLM API key is configured or raise explicit descriptive error."""
        if not self.is_configured:
            raise RuntimeError("LLM API key is not configured.")

    async def create_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """Request structured JSON completion from the configured LLM provider."""
        self.verify_configured()
        sys_directive = (
            f"{system_prompt}\n\nIMPORTANT: You MUST respond with a single, valid JSON object ONLY. "
            "Do NOT include conversational chatter or surrounding explanation outside the JSON."
        )

        import time
        start_t = time.perf_counter()
        resp = await self._provider.complete(
            system_prompt=sys_directive,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format_json=True,
        )
        duration_ms = (time.perf_counter() - start_t) * 1000.0
        self._record_metrics(resp, duration_ms)

        content = resp.get("content", "")
        parsed = extract_json(content)
        if not isinstance(parsed, dict):
            raise RuntimeError(f"Expected JSON object from LLM, got {type(parsed).__name__}")
        return parsed

    async def create_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> str:
        """Request text completion from the configured LLM provider."""
        self.verify_configured()
        import time
        start_t = time.perf_counter()
        resp = await self._provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format_json=False,
        )
        duration_ms = (time.perf_counter() - start_t) * 1000.0
        self._record_metrics(resp, duration_ms)
        return resp.get("content", "").strip()

    def _detect_provider(self) -> str:
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            return "gemini"
        if os.getenv("NVIDIA_API_KEY"):
            return "nvidia"
        return "openai"

    def _default_model_for_provider(self, provider: str) -> str:
        defaults = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-2.0-flash",
            "groq": "llama-3.3-70b-versatile",
            "anthropic": "claude-3-5-sonnet-latest",
            "nvidia": "meta/llama-3.1-70b-instruct",
            "ollama": "llama3.2",
            "local": "llama3.2",
        }
        return defaults.get(provider, "gpt-4o-mini")

    def _key_for_provider(self, provider: str) -> str:
        key_map = {
            "openai": ["OPENAI_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "nvidia": ["NVIDIA_API_KEY"],
        }
        for var in key_map.get(provider, []):
            val = os.getenv(var)
            if val:
                return val
        return ""

    def _build_provider(self) -> BaseLLMProvider:
        prov = self.provider_name
        if prov == "gemini":
            return GeminiProvider(api_key=self.api_key, model=self.model, timeout_seconds=self.timeout_seconds)

        # Standard OpenAI-compatible endpoints
        endpoint = "https://api.openai.com/v1/chat/completions"
        if self.base_url:
            endpoint = self.base_url if "/chat/completions" in self.base_url else f"{self.base_url.rstrip('/')}/chat/completions"
        elif prov == "groq":
            endpoint = "https://api.groq.com/openai/v1/chat/completions"
        elif prov == "nvidia":
            endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
        elif prov in ("ollama", "local"):
            endpoint = "http://localhost:11434/v1/chat/completions"

        return OpenAICompatibleProvider(
            api_key=self.api_key,
            model=self.model,
            base_url=endpoint,
            timeout_seconds=self.timeout_seconds,
        )
