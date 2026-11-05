---
name: deployment-automation
description: Use when orchestrating application rollout, managing isolated preview servers, allocating ports, and verifying live endpoints
---

# Deployment Automation

## Overview
Automate application deployment into sandboxed local runtime environments. Select the correct entry point, allocate an available TCP port, spawn isolated HTTP server processes, and verify live HTTP response reachability.

**Announce at start:** "I'm using the deployment-automation skill to allocate isolated preview ports, start local servers, and verify live endpoints."

## Core Principles
1. **Isolated Workspace Binding**: Deploy ONLY the current mission's workspace directory. Never cross-mount or reuse an older mission's application files.
2. **Framework Detection**: Detect static HTML5 SPAs, Vite/React apps, or FastAPI backends, and configure appropriate runtime handlers.
3. **Port Allocation & Conflict Prevention**: Dynamically locate and bind an unused TCP port (`9101-9999`) on `127.0.0.1` without collision.
4. **Endpoint Health Probing**: Execute live HTTP socket or urllib GET probes to confirm the server returns status 200 OK before declaring deployment successful.
5. **Preview URL Propagation**: Supply the exact, verified live URL (`http://127.0.0.1:<port>`) to the orchestrator and Website Viewer.

