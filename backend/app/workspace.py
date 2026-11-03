"""Workspace manager providing isolated, secure project workspaces for users."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class WorkspaceSecurityError(Exception):
    """Raised when an unsafe path or forbidden file operation is attempted."""


def sanitize_identifier(ident: str) -> str:
    """Sanitize user or project identifiers to prevent directory manipulation."""
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", ident.strip())
    return clean[:64] if clean else "default"


def detect_language(path: str) -> str:
    """Infer programming or markup language from file extension."""
    ext = Path(path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".json": "json",
        ".md": "markdown",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".txt": "plaintext",
    }
    return mapping.get(ext, "plaintext")


class WorkspaceManager:
    """Manages isolated disk directories for authenticated users and their projects."""

    FORBIDDEN_FILES = {".env", ".git", ".gitignore", ".env.local", "devops_swarm.db"}

    def __init__(self, root_dir: str | Path | None = None) -> None:
        if root_dir is None:
            default_root = Path(__file__).resolve().parent.parent / "workspaces"
            root_str = os.getenv("WORKSPACES_ROOT", str(default_root))
            self.root_dir = Path(root_str).resolve()
        else:
            self.root_dir = Path(root_dir).resolve()

        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get_user_dir(self, user_id: str, create: bool = False) -> Path:
        """Get the base workspace directory for a user, optionally creating it."""
        safe_user = sanitize_identifier(user_id)
        user_dir = (self.root_dir / safe_user).resolve()
        if create:
            user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def get_project_dir(self, user_id: str, project_id: str, create: bool = False) -> Path:
        """Resolve the specific project directory for a user, optionally creating it."""
        if not project_id or not str(project_id).strip():
            raise WorkspaceSecurityError("Project identifier cannot be empty.")
        if "\x00" in str(project_id):
            raise WorkspaceSecurityError("Null bytes are not allowed in project identifiers.")

        raw_proj = Path(str(project_id).strip().replace("\\", "/")).name
        if raw_proj in self.FORBIDDEN_FILES or raw_proj.startswith(".env"):
            raise WorkspaceSecurityError(f"Access to '{raw_proj}' is restricted.")

        safe_proj = sanitize_identifier(project_id)
        if safe_proj in self.FORBIDDEN_FILES or safe_proj.startswith(".env"):
            raise WorkspaceSecurityError(f"Access to '{safe_proj}' is restricted.")

        user_dir = self.get_user_dir(user_id, create=create)
        project_dir = (user_dir / safe_proj).resolve()
        try:
            project_dir.relative_to(user_dir)
        except ValueError as exc:
            raise WorkspaceSecurityError(f"Path traversal detected in project '{project_id}'.") from exc

        if create:
            project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def resolve_safe_path(
        self, user_id: str, project_id: str, relative_path: str, create: bool = False
    ) -> Path:
        """Validate and resolve a file path inside the project workspace.
        
        Prevents path traversal, absolute path injection, and access to protected files.
        """
        if not relative_path or not relative_path.strip():
            raise WorkspaceSecurityError("Relative file path cannot be empty.")

        # Reject null bytes
        if "\x00" in relative_path:
            raise WorkspaceSecurityError("Null bytes are not allowed in file paths.")

        # Strip leading slashes to prevent absolute root escapes
        clean_rel = relative_path.replace("\\", "/").strip().lstrip("/")

        # Check for forbidden hidden/system files
        file_name = Path(clean_rel).name
        if file_name in self.FORBIDDEN_FILES or file_name.startswith(".env"):
            raise WorkspaceSecurityError(f"Access to '{file_name}' is restricted.")

        project_dir = self.get_project_dir(user_id, project_id, create=create)
        target_path = (project_dir / clean_rel).resolve()

        # Enforce that the target stays strictly inside project_dir
        try:
            target_path.relative_to(project_dir)
        except ValueError as exc:
            raise WorkspaceSecurityError(
                f"Path traversal detected: '{relative_path}' escapes the workspace boundary."
            ) from exc

        return target_path

    def write_file(
        self, user_id: str, project_id: str, relative_path: str, content: str
    ) -> dict[str, Any]:
        """Write content to a file in the project workspace, tracking whether created or modified."""
        target_path = self.resolve_safe_path(user_id, project_id, relative_path, create=True)
        is_new = not target_path.exists()

        old_content = ""
        if not is_new:
            try:
                old_content = target_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        clean_rel = target_path.relative_to(self.get_project_dir(user_id, project_id)).as_posix()
        status = "created" if is_new else ("unchanged" if old_content == content else "modified")
        size = target_path.stat().st_size

        return {
            "path": clean_rel,
            "status": status,
            "size": size,
            "language": detect_language(clean_rel),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def read_file(self, user_id: str, project_id: str, relative_path: str) -> dict[str, Any]:
        """Read the real content of a file in the project workspace."""
        target_path = self.resolve_safe_path(user_id, project_id, relative_path)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File '{relative_path}' not found in project workspace.")

        content = target_path.read_text(encoding="utf-8", errors="replace")
        stat = target_path.stat()
        clean_rel = target_path.relative_to(self.get_project_dir(user_id, project_id)).as_posix()

        return {
            "path": clean_rel,
            "content": content,
            "size": stat.st_size,
            "language": detect_language(clean_rel),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
        }

    def delete_file(self, user_id: str, project_id: str, relative_path: str) -> bool:
        """Delete a file in the project workspace."""
        target_path = self.resolve_safe_path(user_id, project_id, relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File '{relative_path}' does not exist.")
        if target_path.is_dir():
            raise ValueError(f"'{relative_path}' is a directory, not a file.")

        target_path.unlink()
        return True

    def list_files(self, user_id: str, project_id: str) -> list[dict[str, Any]]:
        """List all files in the project workspace."""
        project_dir = self.get_project_dir(user_id, project_id)
        if not project_dir.exists():
            return []

        results: list[dict[str, Any]] = []
        for file_path in sorted(project_dir.rglob("*")):
            if file_path.is_file():
                rel = file_path.relative_to(project_dir).as_posix()
                stat = file_path.stat()
                results.append({
                    "path": rel,
                    "name": file_path.name,
                    "size": stat.st_size,
                    "language": detect_language(rel),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                })
        return results

    def get_structure(self, user_id: str, project_id: str) -> dict[str, Any]:
        """Return the hierarchical directory structure of the project."""
        project_dir = self.get_project_dir(user_id, project_id)
        safe_proj = sanitize_identifier(project_id)

        if not project_dir.exists():
            return {
                "project_id": safe_proj,
                "root": {
                    "name": project_dir.name,
                    "path": "/",
                    "type": "directory",
                    "children": [],
                },
                "total_files": 0,
            }

        def build_tree(current_dir: Path) -> dict[str, Any]:
            children = []
            for item in sorted(current_dir.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if item.is_dir():
                    children.append(build_tree(item))
                else:
                    rel = item.relative_to(project_dir).as_posix()
                    children.append({
                        "name": item.name,
                        "path": rel,
                        "type": "file",
                        "size": item.stat().st_size,
                        "language": detect_language(rel),
                    })
            rel_dir = current_dir.relative_to(project_dir).as_posix() if current_dir != project_dir else ""
            return {
                "name": current_dir.name,
                "path": rel_dir or "/",
                "type": "directory",
                "children": children,
            }

        return {
            "project_id": safe_proj,
            "root": build_tree(project_dir),
            "total_files": len(self.list_files(user_id, project_id)),
        }

    def list_projects(self, user_id: str) -> list[dict[str, Any]]:
        """List all projects created by a user."""
        user_dir = self.get_user_dir(user_id)
        if not user_dir.exists():
            return []
        projects = []
        for d in sorted(user_dir.iterdir()):
            if d.is_dir():
                file_count = sum(1 for f in d.rglob("*") if f.is_file())
                stat = d.stat()
                projects.append({
                    "project_id": d.name,
                    "name": d.name.replace("_", " ").title(),
                    "file_count": file_count,
                    "created_at": datetime.fromtimestamp(stat.st_ctime, UTC).isoformat(),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                })
        return projects


_workspace_manager_instance: WorkspaceManager | None = None


def get_workspace_manager() -> WorkspaceManager:
    """Return a singleton WorkspaceManager instance."""
    global _workspace_manager_instance
    if _workspace_manager_instance is None:
        _workspace_manager_instance = WorkspaceManager()
    return _workspace_manager_instance


def set_workspace_manager(manager: WorkspaceManager | None) -> None:
    """Explicitly set or reset the WorkspaceManager singleton."""
    global _workspace_manager_instance
    _workspace_manager_instance = manager
