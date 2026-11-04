"""Live verification script for OpenAI API connectivity and autonomous swarm execution.

Usage:
    python tests/verify_openai_live.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")

from app.llm import LLMClient


async def verify_openai_connection() -> bool:
    print("=" * 60)
    print("STEP 1: VERIFYING LIVE OPENAI API CONNECTIVITY")
    print("=" * 60)

    client = LLMClient()
    print(f"Provider: {client.provider_name}")
    print(f"Model:    {client.model}")
    print(f"Endpoint: {getattr(client._provider, 'base_url', 'default')}")

    if not client.is_configured:
        print("\n[ERROR] OpenAI API key is NOT configured.")
        print(f"Please add your key to {backend_dir / '.env'}:")
        print("    LLM_API_KEY=sk-proj-...")
        print("or set the environment variable:")
        print("    $env:LLM_API_KEY=\"sk-proj-...\"")
        print("\nDo NOT paste your key in chat or public logs.")
        return False

    masked_key = f"{client.api_key[:7]}...{client.api_key[-4:]}" if len(client.api_key) > 12 else "[CONFIGURED]"
    print(f"API Key:  {masked_key}")

    print("\nSending live test prompt to OpenAI API...")
    t0 = time.perf_counter()
    try:
        response = await client.create_json(
            system_prompt="You are a DevOps Swarm connectivity tester. Respond strictly with JSON.",
            user_prompt="Return a JSON object with 'status': 'connected', 'provider': 'openai', 'swarm_ready': true.",
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)
        print(f"SUCCESS: Received valid JSON response in {latency}ms!")
        print(f"Response: {response}")
        print("=" * 60)
        return True
    except Exception as exc:
        latency = round((time.perf_counter() - t0) * 1000, 2)
        print(f"\n[FAILED] Live API call failed after {latency}ms:")
        print(f"Details: {exc}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_openai_connection())
    sys.exit(0 if success else 1)
