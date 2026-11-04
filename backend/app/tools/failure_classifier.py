"""Failure classifier and diagnosis engine for autonomous devops workflows."""

from __future__ import annotations

import re
from typing import Any


class FailureClassifier:
    """Classifies errors, tracebacks, test outputs, and security rejections into

    12 standardized failure categories with retryability rules and exponential backoff calculations.
    """

    CATEGORIES = {
        "SYNTAX_ERROR": {
            "retryable": True,
            "max_retries": 3,
            "patterns": [
                r"SyntaxError:",
                r"IndentationError:",
                r"TabError:",
                r"invalid syntax",
                r"unexpected EOF while parsing",
            ],
            "strategy": "Fix syntax and indentation errors using AST validation",
        },
        "TEST_ASSERTION_FAILURE": {
            "retryable": True,
            "max_retries": 3,
            "patterns": [
                r"AssertionError",
                r"FAIL:\s+test_",
                r"FAILED\s+\(failures=\d+\)",
                r"assert\s+.+\s+==\s+",
            ],
            "strategy": "Inspect failing test assertion, expected vs actual values, and correct the logic",
        },
        "IMPORT_OR_MODULE_ERROR": {
            "retryable": True,
            "max_retries": 3,
            "patterns": [
                r"ModuleNotFoundError:\s+No module named",
                r"ImportError:\s+cannot import name",
                r"ImportError:",
            ],
            "strategy": "Adjust import paths or missing internal modules/files",
        },
        "MISSING_DEPENDENCY": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [
                r"No module named '([a-zA-Z0-9_\-]+)'",
                r"DistributionNotFound",
                r"RequirementParseError",
            ],
            "strategy": "Add missing third-party package to requirements.txt and install dependency",
        },
        "RUNTIME_EXCEPTION": {
            "retryable": True,
            "max_retries": 3,
            "patterns": [
                r"ZeroDivisionError:",
                r"KeyError:",
                r"IndexError:",
                r"TypeError:",
                r"ValueError:",
                r"AttributeError:",
                r"FileNotFoundError:",
                r"UnboundLocalError:",
                r"RecursionError:",
            ],
            "strategy": "Patch runtime exception handling, boundary conditions, and type checks",
        },
        "PORT_CONFLICT": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [
                r"Address already in use",
                r"Errno 98",
                r"WSAEADDRINUSE",
                r"bind:\s+address already in use",
            ],
            "strategy": "Switch to an alternate available port or terminate competing process",
        },
        "TIMEOUT": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [
                r"TimeoutExpired",
                r"timed out",
                r"Command timed out",
                r"asyncio.exceptions.TimeoutError",
            ],
            "strategy": "Optimize execution bottleneck or increase command execution timeout threshold",
        },
        "ENVIRONMENT_CONFIG_ERROR": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [
                r"KeyError:\s*['\"][A-Z0-9_]+['\"]",
                r"Missing environment variable",
                r"PermissionError:",
                r"Access is denied",
            ],
            "strategy": "Provide missing environment defaults and sanitize configuration variables",
        },
        "DOCKER_BUILD_ERROR": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [
                r"docker build",
                r"failed to solve with frontend dockerfile",
                r"returned a non-zero code:",
                r"Dockerfile parse error",
            ],
            "strategy": "Correct Dockerfile instructions, base image tags, and build context copies",
        },
        "STATIC_ANALYSIS_VIOLATION": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [
                r"flake8",
                r"mypy",
                r"linter error",
                r"E999",
                r"F821 undefined name",
            ],
            "strategy": "Refactor code style and resolve unresolved variable names or missing types",
        },
        "SECURITY_GATE_VIOLATION": {
            "retryable": False,
            "max_retries": 1,
            "patterns": [
                r"SECURITY_GATE_FAILED",
                r"SECRET_LEAK",
                r"HARDCODED_CREDENTIAL",
                r"DANGEROUS_COMMAND",
                r"Exposed credential",
            ],
            "strategy": "Remove hardcoded credentials/tokens and replace with environment variable references",
        },
        "UNKNOWN_FAILURE": {
            "retryable": True,
            "max_retries": 2,
            "patterns": [],
            "strategy": "Perform deep diagnostic inspection of stderr and log traces",
        },
    }

    def classify(self, error_message: str, stderr: str = "", exit_code: int = 1) -> dict[str, Any]:
        combined_text = f"{error_message}\n{stderr}".strip()

        for category, config in self.CATEGORIES.items():
            for pattern in config["patterns"]:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    extracted_root_cause = self._extract_root_cause(combined_text, pattern)
                    return {
                        "category": category,
                        "retryable": config["retryable"],
                        "max_retries": config["max_retries"],
                        "strategy": config["strategy"],
                        "pattern_matched": pattern,
                        "root_cause": extracted_root_cause,
                        "exit_code": exit_code,
                    }

        return {
            "category": "UNKNOWN_FAILURE",
            "retryable": True,
            "max_retries": 2,
            "strategy": self.CATEGORIES["UNKNOWN_FAILURE"]["strategy"],
            "pattern_matched": None,
            "root_cause": combined_text[:300] if combined_text else "Unknown error occurred",
            "exit_code": exit_code,
        }

    def calculate_backoff(self, attempt: int, initial_delay: float = 1.0, factor: float = 2.0, max_delay: float = 10.0) -> float:
        if attempt <= 1:
            return initial_delay
        delay = initial_delay * (factor ** (attempt - 1))
        return min(delay, max_delay)

    def _extract_root_cause(self, text: str, matched_pattern: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in reversed(lines):
            if re.search(matched_pattern, line, re.IGNORECASE):
                return line
        return text[:200]
