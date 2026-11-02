# Multiagent

## Autonomous DevOps Swarm

An end-to-end multi-agent autonomous DevOps system featuring specialized AI agents collaborating across planning, code generation, testing, automated builds, operations monitoring, and self-healing.

---

## 🚀 Key Features

- **Multi-Agent Orchestration**: Global supervisor orchestrating tasks across specialized agents:
  - **Planning Agent**: Breaks user requirements into architectural specs, stories, and task plans.
  - **Coding Agent**: Generates complete source code files directly saved to isolated project workspaces on disk (`backend/workspaces/`).
  - **Testing Agent**: Creates and executes unit tests, integration tests, and validation suites.
  - **Build Agent**: Validates builds, dependencies, and container configurations.
  - **Observer / Operations Agent**: Monitors system health, logs, and container metrics.
  - **Self-Healing Agent**: Detects anomalies or pipeline failures, diagnosing root cause, dispatching remediations, and recording fixes to persistent Failure Memory.
- **Authentication & Security (`backend/app/auth.py`)**:
  - Secure user registration and login with input validation (8+ character passwords, email format verification).
  - Salted PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations.
  - Expiring signed JWT access tokens (`HS256`, 24h default / 30-day "Remember Me" mode) guarding all API endpoints.
- **Isolated Project Workspaces (`backend/app/workspace.py`)**:
  - Sandboxed directory isolation per user and project (`backend/workspaces/{user_id}/{project_id}/`).
  - Path traversal and security protections against directory escaping (`../`) and forbidden system files (`.env`, `.git`, `*.db`).
  - Real-time disk file reading, editing, saving, and deletion APIs.
- **Dual Database Persistence (`backend/app/database/`)**:
  - **Zero-Config SQLite**: Built-in default local database (`devops_swarm.db`), requiring no external dependencies or Docker.
  - **MongoDB Integration**: Automatic fallback to MongoDB when `MONGODB_URL` is configured.
  - **Failure Knowledge Base**: Persists diagnostic root causes and self-healing resolutions across runs.
- **Interactive UI (React + Vite - `frontend/src/App.jsx`)**:
  - **Auth Screen**: User sign-in and registration with session persistence in `localStorage`.
  - **Mission Control**: Live swarm pipeline monitoring, agent telemetry, and progress indicators.
  - **Code Explorer**: Multi-file tabbed editor with syntax highlighting, live editing, and direct "Save to Workspace" disk synchronization.
  - **Self-Healing Screen**: Interactive view of healed failures, diagnostic signatures, and simulated failure testing.
- **NVIDIA NIM Integration**: Powered by LLM inference (e.g., LLaMA-3.3-70b-instruct) via NVIDIA NIM, with automatic offline heuristic fallback.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── agents/                   # Specialized agents (Planning, Coding, Testing, Build, Healing, Observer)
│   │   ├── database/                 # SQLite and MongoDB persistence repositories
│   │   ├── auth.py                   # PBKDF2 hashing, JWT token handling & route guards
│   │   ├── schemas.py                # Pydantic schemas (Auth, Pipeline, Workspace)
│   │   └── workspace.py              # Isolated disk workspace & path sandbox manager
│   ├── tests/                        # Swarm unit and integration tests
│   │   ├── test_authentication.py    # Authentication & JWT test suite
│   │   ├── test_coding_agent_workspace.py # Disk workspace & file operations test suite
│   │   ├── test_self_healing.py      # Self-healing & failure recovery tests
│   │   └── test_4_agent_swarm.py     # Swarm orchestration tests
│   ├── workspaces/                   # Isolated disk storage for generated user projects
│   ├── devops_swarm.db               # Local SQLite database (auto-generated)
│   ├── .env.example                  # Environment configuration template
│   └── main.py                       # FastAPI application entrypoint
├── frontend/
│   ├── src/
│   │   ├── App.jsx                   # React UI (Auth screen, Mission Control, Code Explorer, Healing)
│   │   ├── App.css                   # Dashboard styling & layout
│   │   └── main.jsx                  # Frontend entrypoint
│   ├── package.json                  # Frontend dependencies
│   └── vite.config.js                # Vite configuration
├── docker-compose.yml                 # MongoDB service container (optional)
├── requirements.txt                   # Project root Python dependencies
├── package.json                       # Root workspace scripts
└── README.md                          # Project documentation
```

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm
- *(Optional)* Docker (only needed if using MongoDB instead of default SQLite)
- *(Optional)* NVIDIA NIM API Key

### 1. Backend Setup

```bash
# From project root, activate virtual environment:
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cd backend
cp .env.example .env
# Edit .env with your settings (JWT secret, optional NVIDIA_API_KEY, optional MONGODB_URL)
```

### 2. Database

- **Option A: SQLite (Default)**: No setup needed! The backend automatically creates and manages `backend/devops_swarm.db` on launch.
- **Option B: MongoDB (Optional)**: If you prefer MongoDB, start the Docker container:
  ```bash
  docker-compose up -d
  ```
  And configure `MONGODB_URL=mongodb://localhost:27017` in `backend/.env`.

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be running on `http://127.0.0.1:8000` (docs available at `http://127.0.0.1:8000/docs`).

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

---

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup`: Register a new user with PBKDF2 password hashing.
- `POST /api/auth/login`: Authenticate and receive an expiring JWT access token.
- `GET /api/auth/me`: Verify session and retrieve current user info (requires Bearer token).
- `POST /api/auth/logout`: End active user session.

### Swarm Pipelines
- `POST /api/pipelines`: Trigger an end-to-end swarm pipeline run (requires Bearer token).
- `POST /api/pipelines/development`: Run development workflow (Planning, Coding, Build, Testing).
- `POST /api/pipelines/simulate-failure`: Simulate build failure to demonstrate autonomous self-healing.
- `GET /api/pipelines`: Retrieve mission execution history.
- `GET /api/failures`: Retrieve stored self-healing failure memory and diagnostic patterns.

### Workspaces & Files
- `GET /api/workspace/projects`: List user's project workspaces.
- `GET /api/workspace/files`: List real files stored in a project workspace (`?project_id=...`).
- `GET /api/workspace/structure`: Get hierarchical directory tree of workspace files.
- `GET /api/workspace/file`: Read file contents from workspace disk (`?path=...`).
- `PUT /api/workspace/file`: Update/save file contents directly to disk.
- `DELETE /api/workspace/file`: Delete a file from the workspace.
- `POST /api/workspace/generate`: Directly run Planning and Coding agents into workspace disk.

---

## 🧪 Testing

Run backend test suites using Python's built-in `unittest`:

```bash

# Run authentication & JWT security tests
python -m unittest backend/tests/test_authentication.py

# Run workspace file persistence & sandboxing tests
python -m unittest backend/tests/test_coding_agent_workspace.py

# Run self-healing and failure memory tests
python -m unittest backend/tests/test_self_healing.py

# Run swarm orchestration tests
python -m unittest backend/tests/test_4_agent_swarm.py

```

Or run tests with `pytest`:

```bash

pytest backend/tests

```
