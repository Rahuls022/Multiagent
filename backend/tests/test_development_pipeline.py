import asyncio
import unittest

from app.agents import DevelopmentSupervisor
from app.database import InMemoryPipelineRepository


class DevelopmentPipelineTests(unittest.TestCase):
    def test_default_pipeline_completes_in_order(self):
        repository = InMemoryPipelineRepository()
        result = asyncio.run(DevelopmentSupervisor(repository=repository).run_pipeline("Build a student portal"))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(
            [stage["agent"] for stage in result["stages"]],
            ["Planning Agent", "Coding Agent", "Build Agent", "Testing Agent"],
        )
        self.assertTrue(all(stage["status"] == "completed" for stage in result["stages"]))
        saved = asyncio.run(repository.get(result["task"]["id"]))
        self.assertEqual(saved["status"], "completed")
        self.assertEqual(len(asyncio.run(repository.list())), 1)
