import asyncio
import unittest

from app.agents.development_supervisor import DevelopmentSupervisor
from app.agents.healing_agent import SelfHealingAgent
from app.database import InMemoryPipelineRepository
from main import SimulatedFailingBuildAgent


class SelfHealingSystemTests(unittest.TestCase):
    def test_self_healing_agent_heals_failed_stage_and_saves_to_db(self):
        repository = InMemoryPipelineRepository()
        healing_agent = SelfHealingAgent(repository=repository)
        
        failed_stage = {
            "agent": "Build Agent",
            "status": "failed",
            "output": {"error": "COMPILER_ERROR: Missing headers"},
            "logs": [],
            "events": [],
        }
        task = {"id": "test-task-101", "request": "Build a portal"}
        
        healed_stage = asyncio.run(healing_agent.heal(failed_stage, task, {}))
        
        self.assertEqual(healed_stage["status"], "healed")
        self.assertTrue(healed_stage["output"]["healed"])
        
        # Verify failure memory was persisted in DB
        failures = asyncio.run(repository.list_failure_memory())
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["failed_agent"], "Build Agent")
        self.assertEqual(failures[0]["status"], "healed")

    def test_supervisor_autonomously_recovers_simulated_failure(self):
        repository = InMemoryPipelineRepository()
        failing_pipeline = [SimulatedFailingBuildAgent()]
        healing_agent = SelfHealingAgent(repository=repository)
        
        supervisor = DevelopmentSupervisor(
            pipeline=failing_pipeline,
            repository=repository,
            healing_agent=healing_agent
        )
        
        result = asyncio.run(supervisor.run_pipeline("Build a resilient portal"))
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stages"][0]["status"], "healed")
        
        failures = asyncio.run(repository.list_failure_memory())
        self.assertGreaterEqual(len(failures), 1)
        self.assertEqual(failures[0]["mission_request"], "Build a resilient portal")
