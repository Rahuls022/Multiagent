# Multiagent

## Autonomous DevOps Swarm

An end-to-end multi-agent autonomous DevOps system featuring specialized AI agents collaborating across planning, code generation, testing, automated builds, operations monitoring, and self-healing.

---

## 🚀 Key Features

- **Multi-Agent Orchestration**: Global supervisor orchestrating tasks across specialized agents:
  - **Planning Agent**: Breaks user requirements into architectural specs, stories, and task plans.
  - **Coding Agent**: Implements features, generates code modules, and applies bug fixes.
  - **Testing Agent**: Creates and executes unit tests, integration tests, and validation suites.
  - **Build Agent**: Validates builds, dependencies, and container configurations.
  - **Observer / Operations Agent**: Monitors system health, logs, and container metrics.
  - **Self-Healing Agent**: Detects anomalies or pipeline failures, diagnosing root cause and dispatching remediations.
- **NVIDIA NIM Integration**: Powered by LLM inference (e.g., LLaMA-3.3-70b-instruct) via NVIDIA NIM.
- **MongoDB Persistence**: Real-time storage of agent task states, execution logs, and project context.
- **Interactive UI**: Modern React + Vite frontend dashboard for visualizing swarm status and agent telemetry in real-time.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── agents/            # Specialized agents (Planning, Coding, Testing, Build, Healing, Observer)
│   │   ├── database/          # MongoDB repository and connection
│   │   └── schemas.py         # Pydantic data schemas
│   ├── tests/                 # Swarm unit and integration tests
│   ├── main.py                # FastAPI application entrypoint
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/                   # React dashboard UI
│   ├── package.json           # Frontend dependencies
│   └── vite.config.js         # Vite configuration
├── docker-compose.yml         # MongoDB & local service containers
├── requirements.txt           # Project root Python dependencies
└── package.json               # Root workspace scripts
```

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm
- Docker (for MongoDB service)
- NVIDIA NIM API Key (or compatible LLM endpoint)

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY and MongoDB connection
```

### 2. Database

Start the local MongoDB service using Docker Compose:

```bash
docker-compose up -d
```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

---

## 🧪 Testing

Run backend agent swarm tests:

```bash
cd backend
pytest
```
