import asyncio
import sys
import unittest
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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


if __name__ == "__main__":
    unittest.main()
