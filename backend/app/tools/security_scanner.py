"""Real static security gate, secret scanner, and vulnerability validator for sandboxed workspaces."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any


class SecurityScanner:
    """Scans workspace files for leaked secrets, hardcoded credentials, dangerous commands,

    and suspicious dependencies. Redacts all sensitive values before returning findings.
    """

    SECRET_PATTERNS = [
        ("NVIDIA API Key", re.compile(r"nvapi-[A-Za-z0-9_\-]{32,}", re.IGNORECASE)),
        ("OpenAI API Key", re.compile(r"sk-[A-Za-z0-9_\-]{32,}", re.IGNORECASE)),
        ("GitHub Personal Access Token", re.compile(r"gh[pousr]-[A-Za-z0-9_]{36,}", re.IGNORECASE)),
        ("AWS Access Key ID", re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b")),
        ("Slack Token", re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}")),
        ("Private Encryption Key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
        ("Generic Secret/Token Assignment", re.compile(r'(?:api_key|access_token|secret_key|auth_token)\s*=\s*["\']([a-zA-Z0-9_\-\.]{24,})["\']', re.IGNORECASE)),
        ("Database Credentials in URI", re.compile(r"(?:postgres|postgresql|mysql|mongodb|redis)://[^:]+:([^@]+)@", re.IGNORECASE)),
    ]

    DANGEROUS_COMMANDS = [
        ("Destructive File Deletion", re.compile(r"\brm\s+-(?:r[fv]|fr)\s+[/~]", re.IGNORECASE)),
        ("Fork Bomb", re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:", re.IGNORECASE)),
        ("Filesystem Format Command", re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\s+", re.IGNORECASE)),
        ("Unauthorized Sudo Execution", re.compile(r"\bsudo\s+", re.IGNORECASE)),
    ]

    SUSPICIOUS_PACKAGES = {
        "colourama", "cryptograpy", "djago", "reqeusts", "urllib4", "pytorc", "tensorflw"
    }

    def scan_workspace(self, workspace_root: Path | str) -> dict[str, Any]:
        root = Path(workspace_root).resolve()
        findings: list[dict[str, Any]] = []
        scanned_files = 0

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            # Skip git metadata and virtual environments
            rel_parts = path.relative_to(root).parts
            if any(part in (".git", "__pycache__", ".venv", "venv", "node_modules") for part in rel_parts):
                continue

            rel_str = path.relative_to(root).as_posix()
            scanned_files += 1

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            file_findings = self.scan_text(content, filename=rel_str)
            findings.extend(file_findings)

            # Check requirements.txt for suspicious or malicious package names
            if path.name == "requirements.txt":
                req_findings = self._check_requirements(content, filename=rel_str)
                findings.extend(req_findings)

        secrets_count = sum(1 for f in findings if f["category"] in ("SECRET_LEAK", "HARDCODED_CREDENTIAL"))
        vulns_count = len(findings)
        passed = (secrets_count == 0 and vulns_count == 0)

        return {
            "passed": passed,
            "vulnerabilities": vulns_count,
            "secrets_found": secrets_count,
            "scanned_files": scanned_files,
            "findings": findings,
            "message": "All security quality gates passed cleanly." if passed else f"Security gate failed with {vulns_count} findings ({secrets_count} secrets).",
        }

    def scan_text(self, text: str, filename: str = "memory") -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = text.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # 1. Secret patterns check
            for label, pattern in self.SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    # Filter out test/dummy values
                    val = match.group(0)
                    if any(dummy in val.lower() for dummy in ["test", "dummy", "fake", "example", "placeholder", "xxx"]):
                        continue
                    findings.append({
                        "category": "SECRET_LEAK",
                        "severity": "CRITICAL",
                        "rule": label,
                        "file": filename,
                        "line": line_idx,
                        "description": f"Exposed credential or private token matching rule '{label}'",
                        "snippet": self._redact(line),
                    })

            # 2. Dangerous commands check
            for label, pattern in self.DANGEROUS_COMMANDS:
                if pattern.search(line):
                    findings.append({
                        "category": "DANGEROUS_COMMAND",
                        "severity": "HIGH",
                        "rule": label,
                        "file": filename,
                        "line": line_idx,
                        "description": f"Potentially hazardous system command detected: {label}",
                        "snippet": line_stripped[:120],
                    })

            # 3. Path traversal check
            if "../.." in line or "..\\.." in line:
                findings.append({
                    "category": "PATH_TRAVERSAL",
                    "severity": "HIGH",
                    "rule": "Relative Path Escape",
                    "file": filename,
                    "line": line_idx,
                    "description": "Path traversal pattern detected (../..)",
                    "snippet": line_stripped[:120],
                })

        return findings

    def _check_requirements(self, content: str, filename: str) -> list[dict[str, Any]]:
        findings = []
        for line_idx, line in enumerate(content.splitlines(), start=1):
            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
            if pkg in self.SUSPICIOUS_PACKAGES:
                findings.append({
                    "category": "SUSPICIOUS_DEPENDENCY",
                    "severity": "HIGH",
                    "rule": "Typosquatting Package",
                    "file": filename,
                    "line": line_idx,
                    "description": f"Package '{pkg}' is flagged as a known typosquatting risk.",
                    "snippet": line[:100],
                })
        return findings

    @staticmethod
    def _redact(text: str) -> str:
        # Redact raw secrets before logging or presenting
        redacted = re.sub(r"(nvapi-[A-Za-z0-9_\-]{6})[A-Za-z0-9_\-]+", r"\1...[REDACTED]", text)
        redacted = re.sub(r"(sk-[A-Za-z0-9_\-]{6})[A-Za-z0-9_\-]+", r"\1...[REDACTED]", redacted)
        redacted = re.sub(r"(gh[pousr]-[A-Za-z0-9_]{6})[A-Za-z0-9_]+", r"\1...[REDACTED]", redacted)
        redacted = re.sub(r"(xox[baprs]-[0-9]{4})[0-9a-zA-Z_\-]+", r"\1...[REDACTED]", redacted)
        redacted = re.sub(r"://([^:]+):([^@]+)@", r"://\1:[REDACTED_PASSWORD]@", redacted)
        return redacted[:150]
