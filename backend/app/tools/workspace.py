"""Sandboxed workspace manager and controlled file/shell execution tools."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class WorkspaceManager:
    """Provides safe, sandboxed file, shell, and local Git operations confined to a specific mission workspace."""

    def __init__(self, workspace_root: Path | str | None = None, user_id: str = "anonymous", mission_id: str = "default") -> None:
        if workspace_root is None:
            workspace_root = os.getenv("WORKSPACE_ROOT", Path(__file__).parents[2] / "workspaces")
        user_str = str(user_id) if user_id else "anonymous"
        mission_str = str(mission_id) if mission_id else "default"
        safe_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_str)
        safe_mission = re.sub(r"[^a-zA-Z0-9_\-]", "_", mission_str)
        self.root_path = Path(workspace_root).resolve() / safe_user / safe_mission
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.audit_log: list[dict[str, Any]] = []

        # Resource Quota Configuration
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", str(5 * 1024 * 1024)))
        self.max_files_changed = int(os.getenv("MAX_FILES_CHANGED", "150"))
        self.max_output_size = int(os.getenv("MAX_OUTPUT_SIZE", "100000"))
        self.command_timeout_seconds = float(os.getenv("COMMAND_TIMEOUT_SECONDS", "60.0"))
        self.files_written_count = 0

    @property
    def workspace_dir(self) -> Path:
        return self.root_path

    def resolve_path(self, relative_path: str | Path) -> Path:
        """Resolve a relative path and verify it cannot escape the workspace root."""
        clean_rel = str(relative_path).lstrip("/\\")
        target = (self.root_path / clean_rel).resolve()
        try:
            target.relative_to(self.root_path)
        except ValueError as exc:
            raise PermissionError(f"Access denied: path '{relative_path}' escapes workspace boundary.") from exc
        return target

    def read_file(self, relative_path: str | Path) -> str:
        """Read text contents of a file within the workspace."""
        path = self.resolve_path(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found in workspace: {relative_path}")
        content = path.read_text(encoding="utf-8", errors="replace")
        self._log_action("read_file", {"path": str(relative_path), "bytes": len(content.encode("utf-8"))})
        return content

    def write_file(self, relative_path: str | Path, content: str) -> dict[str, Any]:
        """Atomically create or overwrite a file within the workspace, enforcing resource quotas."""
        path = self.resolve_path(relative_path)
        size_bytes = len(content.encode("utf-8"))
        if size_bytes > self.max_file_size:
            raise ValueError(f"File size {size_bytes} bytes exceeds quota limit of {self.max_file_size} bytes.")
        if self.files_written_count >= self.max_files_changed:
            raise ValueError(f"Maximum files changed limit ({self.max_files_changed}) reached for this mission.")

        path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        path.write_text(content, encoding="utf-8")
        self.files_written_count += 1
        loc = len(content.splitlines())
        res = {
            "path": str(relative_path).replace("\\", "/"),
            "lines": loc,
            "bytes": size_bytes,
            "created": is_new,
        }
        self._log_action("write_file", res)
        return res
        self._log_action("write_file", res)
        return res

    def list_files(self, relative_dir: str | Path = ".") -> list[dict[str, Any]]:
        """List all files and subdirectories under the given directory."""
        dir_path = self.resolve_path(relative_dir)
        if not dir_path.is_dir():
            return []
        items = []
        for p in sorted(dir_path.rglob("*")):
            rel = p.relative_to(self.root_path).as_posix()
            items.append({
                "path": rel,
                "is_dir": p.is_dir(),
                "size_bytes": p.stat().st_size if p.is_file() else 0,
            })
        self._log_action("list_files", {"dir": str(relative_dir), "count": len(items)})
        return items

    def search_files(self, query: str, relative_dir: str | Path = ".") -> list[dict[str, Any]]:
        """Search code files for exact or case-insensitive query substring."""
        dir_path = self.resolve_path(relative_dir)
        matches = []
        query_lower = query.lower()
        for p in dir_path.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                try:
                    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines, start=1):
                        if query_lower in line.lower():
                            matches.append({
                                "file": p.relative_to(self.root_path).as_posix(),
                                "line_number": idx,
                                "line_content": line.strip(),
                            })
                except Exception:
                    continue
        self._log_action("search_files", {"query": query, "matches": len(matches)})
        return matches

    def create_directory(self, relative_path: str | Path) -> dict[str, Any]:
        """Create a new directory within the workspace."""
        path = self.resolve_path(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        res = {"path": str(relative_path).replace("\\", "/"), "created": True}
        self._log_action("create_directory", res)
        return res

    def path_exists(self, relative_path: str | Path) -> bool:
        """Check if a relative path exists within workspace boundaries."""
        try:
            return self.resolve_path(relative_path).exists()
        except ValueError:
            return False

    def run_command(self, command: str, timeout_seconds: float | None = None) -> dict[str, Any]:
        """Execute a controlled shell command strictly within the workspace directory."""
        # Safeguard: Rejects any attempt to push to remote Git repositories
        cmd_lower = command.lower().strip()
        if re.search(r"\bgit\s+push\b", cmd_lower):
            raise PermissionError("Autonomous push to remote repository is strictly forbidden by governance policy.")

        timeout = timeout_seconds if timeout_seconds is not None else self.command_timeout_seconds
        t0 = time.perf_counter()

        # Sanitize environment: Ensure Python interpreter from virtualenv is prioritized
        env = os.environ.copy()
        venv_scripts = Path(sys.executable).parent
        env["PATH"] = f"{venv_scripts}{os.pathsep}{env.get('PATH', '')}"
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # Set PYTHONPATH to include workspace root so local modules are importable
        env["PYTHONPATH"] = f"{self.root_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.root_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code = -1
            stdout = exc.stdout or ""
            stderr = f"Command timed out after {timeout} seconds"
        except Exception as exc:
            exit_code = -1
            stdout = ""
            stderr = str(exc)

        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        sanitized_stdout = self._redact_secrets(stdout)
        sanitized_stderr = self._redact_secrets(stderr)

        # Output truncation protection
        if len(sanitized_stdout) > self.max_output_size:
            sanitized_stdout = sanitized_stdout[:self.max_output_size] + f"\n... [Output truncated to {self.max_output_size} bytes]"
        if len(sanitized_stderr) > self.max_output_size:
            sanitized_stderr = sanitized_stderr[:self.max_output_size] + f"\n... [Stderr truncated to {self.max_output_size} bytes]"

        result = {
            "command": command,
            "exit_code": exit_code,
            "stdout": sanitized_stdout,
            "stderr": sanitized_stderr,
            "duration_ms": duration_ms,
            "success": exit_code == 0,
        }
        self._log_action("run_command", {"command": command, "exit_code": exit_code, "duration_ms": duration_ms})
        return result

    # =========================================================================
    # Sandboxed Git Operations
    # =========================================================================

    def git_init(self, committer_name: str = "Autonomous DevOps Swarm", committer_email: str = "swarm@autonomous-devops.local") -> dict[str, Any]:
        """Initialize local git repository inside the sandboxed workspace."""
        git_dir = self.root_path / ".git"
        if not git_dir.exists():
            self.run_command("git init")
            self.run_command(f'git config user.name "{committer_name}"')
            self.run_command(f'git config user.email "{committer_email}"')
            res = {"initialized": True, "path": str(self.root_path)}
        else:
            res = {"initialized": False, "already_exists": True}
        self._log_action("git_init", res)
        return res

    def git_status(self) -> dict[str, Any]:
        """Return workspace git status (untracked, modified, staged files)."""
        res = self.run_command("git status --porcelain")
        lines = [ln for ln in res["stdout"].splitlines() if ln.strip()]
        untracked = []
        modified = []
        staged = []
        for line in lines:
            code = line[:2]
            fpath = line[3:].strip()
            if "??" in code:
                untracked.append(fpath)
            elif "M" in code or "A" in code:
                if code[0] in ("M", "A"):
                    staged.append(fpath)
                if code[1] in ("M", "D"):
                    modified.append(fpath)
            else:
                modified.append(fpath)
        status_info = {
            "clean": len(lines) == 0,
            "untracked": untracked,
            "modified": modified,
            "staged": staged,
            "total_changed": len(lines),
        }
        self._log_action("git_status", status_info)
        return status_info

    def git_diff(self, staged: bool = False) -> str:
        """Return unified git diff for working tree or staged changes."""
        cmd = "git diff --cached" if staged else "git diff"
        res = self.run_command(cmd)
        diff_text = res["stdout"]
        self._log_action("git_diff", {"staged": staged, "bytes": len(diff_text)})
        return diff_text

    def git_add(self, paths: list[str] | None = None) -> dict[str, Any]:
        """Stage files for commit."""
        if not paths:
            cmd = "git add ."
        else:
            quoted = " ".join(f'"{p}"' for p in paths)
            cmd = f"git add {quoted}"
        res = self.run_command(cmd)
        self._log_action("git_add", {"paths": paths or "all", "success": res["success"]})
        return res

    def git_commit(self, message: str) -> dict[str, Any]:
        """Commit staged changes locally with a descriptive message. Remote pushes are forbidden."""
        safe_msg = message.replace('"', '\\"')
        res = self.run_command(f'git commit -m "{safe_msg}"')
        log_res = self.git_log(max_count=1)
        commit_hash = log_res[0].get("hash") if log_res else None
        res["commit_hash"] = commit_hash
        self._log_action("git_commit", {"message": message, "commit_hash": commit_hash, "success": res["success"]})
        return res

    def git_log(self, max_count: int = 5, limit: int | None = None) -> list[dict[str, Any]]:
        """Return recent commit log entries."""
        count = limit if limit is not None else max_count
        res = self.run_command(f'git log -n {count} --pretty=format:"%H|%an|%ad|%s"')
        commits = []
        if res["success"] and res["stdout"]:
            for line in res["stdout"].splitlines():
                parts = line.strip().split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    })
        return commits

    def _redact_secrets(self, text: str) -> str:
        """Strip known API keys or credentials from outputs."""
        sensitive_vars = ["OPENAI_API_KEY", "LLM_API_KEY", "NVIDIA_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"]
        redacted = text
        for var in sensitive_vars:
            val = os.environ.get(var, "").strip()
            if val and len(val) > 6 and val in redacted:
                redacted = redacted.replace(val, f"[{var}_REDACTED]")
        return redacted

    def _log_action(self, action: str, details: dict[str, Any]) -> None:
        self.audit_log.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "details": details,
        })
