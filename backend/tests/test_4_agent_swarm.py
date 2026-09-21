import asyncio
import unittest

from app.agents import BaseAgent, DevelopmentSupervisor, GlobalOrchestrator, ObserverAgent, OperationsSupervisor
from app.database import InMemoryPipelineRepository


class Test4AgentSwarm(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryPipelineRepository()

    def test_main_brain_global_orchestration_decomposes_and_delegates(self):
        """Test Agent 1: Main Brain receives request, decomposes into phases, delegates to supervisors, and aggregates results."""
        orchestrator = GlobalOrchestrator(repository=self.repository)
        result = asyncio.run(orchestrator.run_pipeline("Implement authentication service"))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        
        # Check high-level phase decomposition events
        events = [e["event"] for e in result["events"]]
        self.assertIn("REQUEST_DECOMPOSED", events)
        self.assertIn("PHASE_ASSIGNED", events)
        self.assertIn("PIPELINE_COMPLETED", events)
        
        # Verify 8 agents monitored by Swarm Observer
        self.assertIn("observer", result)
        self.assertEqual(result["observer"]["role"], "Control Tower")
        self.assertEqual(result["observer"]["agents_monitored"], 8)
        self.assertEqual(result["observer"]["failures_detected"], 0)

    def test_dev_supervisor_internal_feedback_loop(self):
        """Test Agent 2: Dev Supervisor handles build/test failure internally via re-coding/healing without involving Global Orchestrator."""
        class FlakyBuildAgent(BaseAgent):
            name = "Build Agent"
            attempt = 0

            async def execute(self, task, context):
                FlakyBuildAgent.attempt += 1
                if FlakyBuildAgent.attempt == 1:
                    raise RuntimeError("BUILD_ERROR: Syntax error in compiled file main.cpp")
                return {
                    "agent": self.name,
                    "status": "completed",
                    "output": "Build succeeded after internal re-code patch.",
                    "logs": [{"agent": self.name, "message": "Build clean"}],
                    "events": [{"agent": self.name, "event": "BUILD_COMPLETED"}],
                }

        from app.agents import SelfHealingAgent
        dev_supervisor = DevelopmentSupervisor(
            pipeline=[DevelopmentSupervisor().pipeline[0], DevelopmentSupervisor().pipeline[1], FlakyBuildAgent(), DevelopmentSupervisor().pipeline[3]],
            repository=self.repository,
            healing_agent=SelfHealingAgent(repository=self.repository),
        )
        result = asyncio.run(dev_supervisor.run_pipeline("Build microservice"))

        self.assertEqual(result["status"], "completed")
        events = [e["event"] for e in result["events"]]
        self.assertIn("DEV_INTERNAL_RETRY", events)
        self.assertIn("CODE_REVISE_REQUESTED", events)

    def test_ops_supervisor_autonomous_rollback_and_retry(self):
        """Test Agent 3: Ops Supervisor executes automatic rollback and retry when deployment fails."""
        class FlakyDeployAgent(BaseAgent):
            name = "Deploy Agent"
            attempt = 0

            async def execute(self, task, context):
                FlakyDeployAgent.attempt += 1
                if FlakyDeployAgent.attempt == 1:
                    raise RuntimeError("DEPLOY_ERROR: Target kubernetes pod crashloopbackoff")
                return {
                    "agent": self.name,
                    "status": "completed",
                    "output": "Deployment succeeded after rollback and container restart.",
                    "logs": [{"agent": self.name, "message": "Deploy ready"}],
                    "events": [{"agent": self.name, "event": "DEPLOYMENT_COMPLETED"}],
                }

        from app.agents import SelfHealingAgent
        ops_supervisor = OperationsSupervisor(
            pipeline=[OperationsSupervisor().pipeline[0], OperationsSupervisor().pipeline[1], FlakyDeployAgent(), OperationsSupervisor().pipeline[3]],
            repository=self.repository,
            healing_agent=SelfHealingAgent(repository=self.repository),
        )

        result = asyncio.run(ops_supervisor.run_pipeline({"id": "ops-test-1"}, {}))

        self.assertEqual(result["status"], "completed")
        events = [e["event"] for e in result["events"]]
        self.assertIn("DEPLOYMENT_ROLLBACK", events)
        self.assertIn("DEPLOYMENT_RETRY_INITIATED", events)

    def test_swarm_observer_control_tower_metrics_and_alerts(self):
        """Test Agent 4: Swarm Observer provides metrics, communication graph, stall detection, and alerting."""
        pipeline_data = {
            "stages": [
                {"agent": "Planning Agent", "status": "completed", "duration_ms": 120.0},
                {"agent": "Coding Agent", "status": "completed", "duration_ms": 6500.0},  # Exceeds SLA threshold (5000ms)
                {"agent": "Build Agent", "status": "failed", "duration_ms": 300.0},
            ],
            "events": [
                {"agent": "Global Orchestrator", "event": "REQUEST_DECOMPOSED", "timestamp": "2026-09-10T08:00:00Z"},
                {"agent": "Development Supervisor", "event": "PHASE_ASSIGNED", "timestamp": "2026-09-10T08:00:01Z"},
                {"agent": "Build Agent", "event": "BUILD_FAILED", "timestamp": "2026-09-10T08:00:05Z"},
                {"agent": "Build Agent", "event": "BUILD_FAILED", "timestamp": "2026-09-10T08:00:07Z"},
            ],
            "logs": [
                {"agent": "Planning Agent", "message": "Planning complete"},
                {"agent": "Coding Agent", "message": "Code written"},
            ],
        }

        observer = ObserverAgent()
        report = observer.inspect(pipeline_data)

        self.assertEqual(report["role"], "Control Tower")
        self.assertEqual(report["status"], "attention_required")
        self.assertIn("Coding Agent", report["stall_analysis"]["stalled_agents"])
        self.assertIn("Build Agent", report["failure_analysis"]["repeated_failures"])
        
        # Verify Alert Generator outputs
        alert_types = [a["type"] for a in report["alerts"]]
        self.assertIn("AGENT_FAILURE", alert_types)
        self.assertIn("STALLED_AGENT", alert_types)
        self.assertIn("REPEATED_FAILURE", alert_types)
        
        # Verify Performance Metrics
        self.assertEqual(report["performance_metrics"]["total_duration_ms"], 6920.0)
        self.assertEqual(len(report["communication_graph"]), 2)


if __name__ == "__main__":
    unittest.main()
