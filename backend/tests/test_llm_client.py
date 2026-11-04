"""Unit tests for the LLM provider abstraction, structured JSON extraction, and key safety."""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from app.llm.client import LLMClient, extract_json, OpenAICompatibleProvider


class TestLLMClient(unittest.TestCase):
    def test_extract_json_from_raw_string(self):
        raw = '{"key": "value", "numbers": [1, 2, 3]}'
        result = extract_json(raw)
        self.assertEqual(result, {"key": "value", "numbers": [1, 2, 3]})

    def test_extract_json_from_markdown_code_fence(self):
        raw = (
            "Here is the architecture plan you requested:\n\n"
            "```json\n"
            "{\n"
            '  "summary": "Calculator Service",\n'
            '  "files_to_create": [{"path": "calc.py"}]\n'
            "}\n"
            "```\n\n"
            "Let me know if you need more details!"
        )
        result = extract_json(raw)
        self.assertEqual(result["summary"], "Calculator Service")
        self.assertEqual(len(result["files_to_create"]), 1)

    def test_extract_json_with_outer_preamble(self):
        raw = "Certainly! The configuration object is:\n{\"status\": \"ready\", \"code\": 200}\nHope this helps."
        result = extract_json(raw)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["code"], 200)

    def test_extract_json_malformed_raises_value_error(self):
        raw = "This is not JSON at all: {broken, non-closed bracket"
        with self.assertRaises(ValueError):
            extract_json(raw)

    def test_missing_api_key_raises_explicit_error(self):
        client = LLMClient(provider_name="openai", api_key="")
        self.assertFalse(client.is_configured)
        with self.assertRaises(RuntimeError) as ctx:
            client.verify_configured()
        self.assertIn("LLM API key is not configured.", str(ctx.exception))

    def test_redact_secrets_in_error_message(self):
        secret_key = "sk-test-secret-1234567890"
        provider = OpenAICompatibleProvider(api_key=secret_key, model="gpt-4o-mini")
        msg = f"HTTP 401 Unauthorized for key {secret_key}"
        sanitized = provider._sanitize_error(msg)
        self.assertNotIn(secret_key, sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)

    def test_client_create_json_with_mocked_provider(self):
        client = LLMClient(provider_name="openai", api_key="sk-dummy-key")
        mock_provider = MagicMock()

        async def fake_complete(**kwargs):
            return {
                "content": '```json\n{"summary": "Mocked Plan", "files_to_create": [{"path": "app.py"}]}\n```',
                "model": "gpt-4o-mini",
            }

        mock_provider.complete = fake_complete
        client._provider = mock_provider

        output = asyncio.run(client.create_json(system_prompt="sys", user_prompt="usr"))
        self.assertEqual(output["summary"], "Mocked Plan")
        self.assertEqual(output["files_to_create"][0]["path"], "app.py")


if __name__ == "__main__":
    unittest.main()
