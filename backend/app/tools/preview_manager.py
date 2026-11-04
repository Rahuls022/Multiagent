"""Preview Manager: manages mission-specific frontend preview servers, framework detection, and secure workspace file exploration."""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional


class PreviewServer:
    def __init__(
        self,
        mission_id: str,
        workspace_dir: Path,
        port: int,
        process: subprocess.Popen,
        framework: str,
        entry_point: str,
        user_id: str = "anonymous",
    ) -> None:
        self.mission_id = mission_id
        self.workspace_dir = workspace_dir
        self.port = port
        self.process = process
        self.framework = framework
        self.entry_point = entry_point
        self.user_id = user_id
        self.started_at = datetime.now(UTC).isoformat()
        self.status = "starting"
        self.preview_url = f"http://127.0.0.1:{port}"
        self.logs: deque[str] = deque(maxlen=200)
        self.error: Optional[str] = None

    def is_alive(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None

    def append_log(self, text: str) -> None:
        for line in text.splitlines():
            line_str = line.strip()
            if line_str:
                self.logs.append(line_str)


class PreviewManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._servers: dict[str, PreviewServer] = {}
        self._lock = threading.RLock()
        self._port_min = 9101
        self._port_max = 9999
        self._initialized = True

    def allocate_port(self) -> int:
        """Find an available, unbound TCP port on 127.0.0.1."""
        with self._lock:
            busy_ports = {srv.port for srv in self._servers.values() if srv.is_alive()}
            for port in range(self._port_min, self._port_max):
                if port in busy_ports:
                    continue
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        s.bind(("127.0.0.1", port))
                        return port
                except OSError:
                    continue
            raise RuntimeError("No available preview port found in range 9101-9999.")

    def detect_frontend(self, workspace_dir: Path) -> dict[str, Any]:
        """Detect frontend framework, entry point, and directory to serve."""
        ws = Path(workspace_dir).resolve()

        # 1. Check for package.json
        pkg_paths = [ws / "package.json", ws / "frontend" / "package.json"]
        for pkg_path in pkg_paths:
            if pkg_path.is_file():
                try:
                    import json
                    pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
                    deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                    scripts = pkg_data.get("scripts", {})
                    framework = "Node.js Web App"
                    if "vite" in deps or "@vitejs/plugin-react" in deps:
                        framework = "Vite / React"
                    elif "next" in deps:
                        framework = "Next.js"
                    elif "react" in deps:
                        framework = "React"
                    elif "vue" in deps:
                        framework = "Vue"

                    entry_candidates = [
                        pkg_path.parent / "index.html",
                        pkg_path.parent / "src" / "main.jsx",
                        pkg_path.parent / "src" / "index.jsx",
                        pkg_path.parent / "src" / "App.jsx",
                    ]
                    entry_rel = "package.json"
                    for ec in entry_candidates:
                        if ec.exists():
                            entry_rel = ec.relative_to(ws).as_posix()
                            break

                    return {
                        "framework": framework,
                        "type": "node",
                        "package_json": pkg_path.relative_to(ws).as_posix(),
                        "serve_dir": pkg_path.parent,
                        "entry_point": entry_rel,
                        "scripts": scripts,
                    }
                except Exception:
                    pass

        # 2. Check for HTML entry point
        html_candidates = [
            ws / "index.html",
            ws / "frontend" / "index.html",
            ws / "frontend" / "dist" / "index.html",
            ws / "dist" / "index.html",
            ws / "public" / "index.html",
            ws / "static" / "index.html",
        ]
        for hc in html_candidates:
            if hc.is_file():
                return {
                    "framework": "HTML5 / SPA",
                    "type": "static",
                    "serve_dir": hc.parent,
                    "entry_point": hc.relative_to(ws).as_posix(),
                }

        # Any other html files
        all_html = list(ws.rglob("*.html"))
        if all_html:
            first = all_html[0]
            return {
                "framework": "HTML5 / Web App",
                "type": "static",
                "serve_dir": first.parent,
                "entry_point": first.relative_to(ws).as_posix(),
            }

        # 3. Check for Python backend with potential web UI
        py_candidates = [ws / "app.py", ws / "main.py", ws / "backend" / "app.py"]
        for pc in py_candidates:
            if pc.is_file():
                return {
                    "framework": "Python Service / REST API",
                    "type": "python",
                    "serve_dir": pc.parent,
                    "entry_point": pc.relative_to(ws).as_posix(),
                }

        return {
            "framework": "Unknown / Static Files",
            "type": "static",
            "serve_dir": ws,
            "entry_point": ".",
        }

    def start_preview(
        self,
        mission_id: str,
        workspace_dir: Path | str,
        user_id: str = "anonymous",
        timeout_seconds: float = 12.0,
    ) -> dict[str, Any]:
        """Start a dedicated preview server for the specified mission workspace."""
        ws_path = Path(workspace_dir).resolve()
        if not ws_path.exists():
            raise FileNotFoundError(f"Workspace directory does not exist: {ws_path}")

        with self._lock:
            existing = self._servers.get(mission_id)
            if existing and existing.is_alive():
                # Already running!
                return {
                    "status": "running",
                    "ready": True,
                    "url": existing.preview_url,
                    "preview_url": existing.preview_url,
                    "port": existing.port,
                    "pid": existing.process.pid,
                    "framework": existing.framework,
                    "entry_point": existing.entry_point,
                    "logs": list(existing.logs),
                }

            detection = self.detect_frontend(ws_path)
            port = self.allocate_port()
            serve_dir = detection.get("serve_dir", ws_path)

            # File Synchronization Guarantee:
            # Ensure serve_dir, ws_path, and frontend/ all contain index.html, styles.css, app.js
            for asset_name in ["index.html", "styles.css", "app.js"]:
                ws_f = ws_path / asset_name
                serve_f = serve_dir / asset_name
                front_f = ws_path / "frontend" / asset_name

                if ws_f.is_file() and not serve_f.is_file():
                    try:
                        serve_f.write_text(ws_f.read_text(encoding="utf-8"), encoding="utf-8")
                    except Exception:
                        pass
                if serve_f.is_file() and not ws_f.is_file():
                    try:
                        ws_f.write_text(serve_f.read_text(encoding="utf-8"), encoding="utf-8")
                    except Exception:
                        pass
                if ws_f.is_file() and not front_f.is_file():
                    try:
                        front_f.write_text(ws_f.read_text(encoding="utf-8"), encoding="utf-8")
                    except Exception:
                        pass
                if front_f.is_file() and not ws_f.is_file():
                    try:
                        ws_f.write_text(front_f.read_text(encoding="utf-8"), encoding="utf-8")
                    except Exception:
                        pass

            # Build execution command
            # For static HTML apps: Launch python's standard http.server with fallback handling
            cmd: list[str] = []
            env = os.environ.copy()

            if detection["type"] == "node" and (serve_dir / "node_modules").exists():
                # Has node_modules: run npm dev or vite
                cmd = ["npm", "run", "dev", "--", "--port", str(port), "--host", "127.0.0.1"]
            else:
                # Use Python HTTP server bound to 127.0.0.1
                cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]

            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(serve_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                )
            except Exception as exc:
                raise RuntimeError(f"Failed to spawn preview server process: {exc}") from exc

            server = PreviewServer(
                mission_id=mission_id,
                workspace_dir=ws_path,
                port=port,
                process=proc,
                framework=detection["framework"],
                entry_point=detection["entry_point"],
                user_id=user_id,
            )
            self._servers[mission_id] = server

            # Background thread to capture stdout/stderr non-blockingly
            def _log_reader():
                try:
                    for line in iter(proc.stdout.readline, ""):
                        server.append_log(line)
                except Exception:
                    pass

            t = threading.Thread(target=_log_reader, daemon=True)
            t.start()

        # Health Check: wait until server responds
        start_t = time.perf_counter()
        target_url = f"http://127.0.0.1:{port}"
        healthy = False

        while time.perf_counter() - start_t < timeout_seconds:
            if not server.is_alive():
                exit_code = proc.poll()
                err_text = "\n".join(server.logs)
                server.status = "failed"
                server.error = f"Process exited prematurely with code {exit_code}. Logs: {err_text}"
                raise RuntimeError(server.error)

            try:
                req = urllib.request.Request(target_url, headers={"User-Agent": "Autonomous-DevOps-Swarm/1.0"})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status in (200, 301, 302, 304, 404):
                        healthy = True
                        break
            except Exception:
                time.sleep(0.3)

        if not healthy:
            server.status = "timeout"
            server.error = f"Health check timed out after {timeout_seconds}s waiting for {target_url}"
            # Terminate unresponsive process
            self.stop_preview(mission_id)
            raise TimeoutError(server.error)

        server.status = "running"
        server.append_log(f"Preview server successfully verified healthy on {target_url}")

        return {
            "status": "running",
            "ready": True,
            "url": target_url,
            "preview_url": target_url,
            "port": port,
            "pid": proc.pid,
            "framework": detection["framework"],
            "entry_point": detection["entry_point"],
            "logs": list(server.logs),
        }

    def get_server(self, mission_id: str) -> PreviewServer | None:
        """Retrieve registered server instance if present."""
        with self._lock:
            return self._servers.get(mission_id)

    def get_status(self, mission_id: str) -> dict[str, Any]:
        """Check status of a mission's preview server."""
        with self._lock:
            server = self._servers.get(mission_id)
            if not server:
                return {
                    "mission_id": mission_id,
                    "pipeline_id": mission_id,
                    "status": "stopped",
                    "ready": False,
                    "url": None,
                    "preview_url": None,
                    "port": None,
                    "pid": None,
                    "framework": None,
                    "logs": [],
                }

            is_alive = server.is_alive()
            curr_status = "running" if is_alive else (server.status if server.status != "running" else "stopped")

            return {
                "mission_id": mission_id,
                "pipeline_id": mission_id,
                "status": curr_status,
                "ready": is_alive,
                "url": server.preview_url if is_alive else None,
                "preview_url": server.preview_url if is_alive else None,
                "port": server.port if is_alive else None,
                "pid": server.process.pid if (server.process and is_alive) else None,
                "framework": server.framework,
                "entry_point": server.entry_point,
                "started_at": server.started_at,
                "logs": list(server.logs),
                "error": server.error,
            }

    def stop_preview(self, mission_id: str) -> dict[str, Any]:
        """Gracefully stop a running preview server process."""
        with self._lock:
            server = self._servers.get(mission_id)
            if not server or not server.process:
                return {"mission_id": mission_id, "status": "stopped"}

            proc = server.process
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2.0)
                except Exception:
                    try:
                        if sys.platform == "win32":
                            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                        else:
                            proc.kill()
                    except Exception:
                        pass

            server.status = "stopped"
            return {"mission_id": mission_id, "status": "stopped"}

    def stop_all(self) -> None:
        """Terminate all running preview servers."""
        with self._lock:
            for srv in list(self._servers.values()):
                if srv.process and srv.process.poll() is None:
                    try:
                        srv.process.terminate()
                        srv.process.wait(timeout=1.0)
                    except Exception:
                        try:
                            if sys.platform == "win32":
                                subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.process.pid)], capture_output=True)
                            else:
                                srv.process.kill()
                        except Exception:
                            pass
                    srv.status = "stopped"
            self._servers.clear()

    def get_logs(self, mission_id: str) -> list[str]:
        """Retrieve collected preview startup and runtime logs."""
        with self._lock:
            server = self._servers.get(mission_id)
            return list(server.logs) if server else []

    # =========================================================================
    # Workspace File Exploration & Safe Content Reader
    # =========================================================================

    def _resolve_safe_path(self, workspace_dir: Path, relative_path: str | Path) -> Path:
        """Resolve a relative path, enforcing strict boundary check against directory traversal."""
        root = Path(workspace_dir).resolve()
        clean_rel = str(relative_path).lstrip("/\\")
        target = (root / clean_rel).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise PermissionError(f"Access denied: path '{relative_path}' escapes workspace boundary.") from exc
        return target

    def list_workspace_files(self, workspace_dir: Path) -> list[dict[str, Any]]:
        """List actual generated workspace files with category, size, and extension."""
        root = Path(workspace_dir).resolve()
        if not root.is_dir():
            return []

        results = []
        for p in sorted(root.rglob("*")):
            # Skip hidden git internal metadata
            if ".git" in p.parts:
                continue
            rel = p.relative_to(root).as_posix()
            ext = p.suffix.lower().lstrip(".")
            is_dir = p.is_dir()
            size = p.stat().st_size if not is_dir else 0

            category = "other"
            if is_dir:
                category = "folder"
            elif ext in ("html", "jsx", "tsx", "vue", "css", "scss", "svg"):
                category = "frontend"
            elif ext in ("py", "ts", "js", "go", "rs", "java"):
                if "test" in rel.lower():
                    category = "tests"
                elif "app" in rel.lower() or "main" in rel.lower() or "server" in rel.lower() or "route" in rel.lower():
                    category = "backend"
                else:
                    category = "code"
            elif ext in ("json", "yaml", "yml", "toml", "ini", "env"):
                category = "config"
            elif ext in ("sql", "db", "sqlite"):
                category = "database"
            elif p.name.lower() in ("dockerfile", "docker-compose.yml", "readme.md"):
                category = "devops"

            results.append({
                "path": rel,
                "name": p.name,
                "is_dir": is_dir,
                "size_bytes": size,
                "extension": ext,
                "category": category,
            })
        return results

    def read_workspace_file(self, workspace_dir: Path, relative_path: str | Path) -> dict[str, Any]:
        """Read actual file content with syntax metadata, protecting against path traversal."""
        safe_path = self._resolve_safe_path(workspace_dir, relative_path)
        if not safe_path.is_file():
            raise FileNotFoundError(f"File not found in workspace: {relative_path}")

        try:
            content = safe_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise IOError(f"Could not read file {relative_path}: {exc}") from exc

        ext = safe_path.suffix.lower().lstrip(".")
        lang_map = {
            "py": "python",
            "js": "javascript",
            "jsx": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "html": "html",
            "css": "css",
            "json": "json",
            "sql": "sql",
            "md": "markdown",
            "yml": "yaml",
            "yaml": "yaml",
            "sh": "bash",
            "dockerfile": "dockerfile",
        }
        language = lang_map.get(ext, ext or "text")
        if safe_path.name.lower() == "dockerfile":
            language = "dockerfile"

        lines = content.splitlines()
        return {
            "path": str(relative_path).replace("\\", "/"),
            "name": safe_path.name,
            "content": content,
            "lines": len(lines),
            "lines_count": len(lines),
            "size_bytes": len(content.encode("utf-8")),
            "language": language,
            "extension": ext,
        }
