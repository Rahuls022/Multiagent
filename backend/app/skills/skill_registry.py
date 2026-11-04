"""Skill Registry for Autonomous DevOps Swarm.

Integrates standard agent skills (from skills.sh) into specific swarm agents:
- Planning Agent: 'writing-plans'
- Coding Agent: 'frontend-design'
- Build Agent: 'systematic-debugging'
- Testing Agent: 'verification-before-completion'
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import re
from typing import Any

logger = logging.getLogger("autonomous_devops.skills")


@dataclass
class SkillDefinition:
    name: str
    description: str
    content: str
    path: Path
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def instructions(self) -> str:
        """Returns the markdown body excluding frontmatter."""
        text = self.content
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return text.strip()


class SkillRegistry:
    """Discovers, loads, and maps agent skills to individual swarm specialists."""

    AGENT_SKILL_MAP: dict[str, str] = {
        "Planning Agent": "writing-plans",
        "Coding Agent": "frontend-design",
        "Build Agent": "systematic-debugging",
        "Testing Agent": "verification-before-completion",
    }

    def __init__(self, skills_dir: Path | str | None = None) -> None:
        self.skills_dir = self._resolve_skills_dir(skills_dir)
        self._skills: dict[str, SkillDefinition] = {}
        self.reload()

    def _resolve_skills_dir(self, custom_path: Path | str | None) -> Path:
        if custom_path:
            p = Path(custom_path).resolve()
            if p.exists() and p.is_dir():
                return p

        # Check environment variables
        for env_var in ("SKILLS_DIR", "AGENT_SKILLS_DIR", "SWARM_SKILLS_DIR"):
            env_val = os.getenv(env_var)
            if env_val:
                p = Path(env_val).resolve()
                if p.exists() and p.is_dir():
                    return p

        # Check all parents from current file location up to filesystem root
        current = Path(__file__).resolve()
        for parent in [current.parent, *current.parents]:
            candidate = parent / ".agents" / "skills"
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Check current working directory and all its parents
        cwd = Path.cwd().resolve()
        for p in [cwd, *cwd.parents]:
            candidate = p / ".agents" / "skills"
            if candidate.exists() and candidate.is_dir():
                return candidate

        return (current.parent.parent.parent.parent / ".agents" / "skills").resolve()

    def reload(self) -> None:
        """Scan skills_dir and load all SKILL.md definitions."""
        self._skills.clear()
        if not self.skills_dir.exists():
            self.skills_dir = self._resolve_skills_dir(None)
            if not self.skills_dir.exists():
                logger.warning("Skills directory does not exist: %s", self.skills_dir)
                return

        for child in sorted(self.skills_dir.iterdir()):
            if child.is_dir():
                skill_file = child / "SKILL.md"
                if skill_file.is_file():
                    try:
                        skill = self._parse_skill_file(skill_file, child.name)
                        self._skills[skill.name] = skill
                    except Exception as exc:
                        logger.error("Failed to parse skill %s: %s", skill_file, exc)

        logger.info("Loaded %d skills from %s", len(self._skills), self.skills_dir)

    def _parse_skill_file(self, path: Path, dir_name: str) -> SkillDefinition:
        text = path.read_text(encoding="utf-8")
        name = dir_name
        description = ""
        meta: dict[str, Any] = {}

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                header = parts[1]
                for line in header.splitlines():
                    line = line.strip()
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        meta[k] = v
                        if k == "name":
                            name = v
                        elif k == "description":
                            description = v

        return SkillDefinition(
            name=name,
            description=description,
            content=text,
            path=path,
            metadata=meta,
        )

    def get_skill(self, name: str) -> SkillDefinition | None:
        return self._skills.get(name)

    def get_skill_for_agent(self, agent_name: str) -> SkillDefinition | None:
        skill_name = self.AGENT_SKILL_MAP.get(agent_name)
        if not skill_name:
            return None
        return self._skills.get(skill_name)

    def get_prompt_injection(self, agent_name: str) -> str:
        """Returns concise, high-impact skill guidance for LLM prompts."""
        skill = self.get_skill_for_agent(agent_name)
        if not skill:
            return ""

        name = skill.name
        desc_line = f"Skill Description: {skill.description}\n" if skill.description else ""
        if name == "writing-plans":
            return (
                "\n--- [APPLIED AGENT SKILL: writing-plans] ---\n"
                f"{desc_line}"
                "You are operating with the 'writing-plans' skill from skills.sh:\n"
                "1. Structure implementation plan for zero-context executor with bite-sized, testable tasks.\n"
                "2. Explicit File Structure: Map all files created/modified with single responsibilities.\n"
                "3. Task Right-Sizing: Every task ends with an independently testable deliverable.\n"
                "4. Step Granularity: Write test -> run fail -> implement minimal code -> run pass -> commit.\n"
                "5. Review Focus & Acceptance Criteria: Pin exact quality gates and constraints.\n"
                "---------------------------------------------------\n"
            )
        elif name == "frontend-design":
            return (
                "\n--- [APPLIED AGENT SKILL: frontend-design] ---\n"
                f"{desc_line}"
                "You are operating with the 'frontend-design' skill from skills.sh:\n"
                "1. Ground designs in subject matter: Extract domain, industry, and materials. Do NOT use generic AI templates.\n"
                "2. Distinctive Visual Identity: Deliberate typography, intentional palette (CSS variables), characteristic hero.\n"
                "3. Complete Interactive Functionality: Working navigation, catalog search/filter, full cart management, and checkout form.\n"
                "4. Avoid AI-generated cliché defaults: No generic SaaS card kit, no mismatched academic/student fields in e-commerce.\n"
                "5. Spend boldness in one place: Keep surrounding chrome clean, responsive, and functional.\n"
                "---------------------------------------------------\n"
            )
        elif name == "systematic-debugging":
            return (
                "\n--- [APPLIED AGENT SKILL: systematic-debugging] ---\n"
                f"{desc_line}"
                "You are operating with the 'systematic-debugging' skill from skills.sh:\n"
                "1. The Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.\n"
                "2. Read all compiler and AST error messages completely; note line numbers and exact tokens.\n"
                "3. Gather multi-layer boundary evidence across syntax check, imports, and compilation.\n"
                "---------------------------------------------------\n"
            )
        elif name == "verification-before-completion":
            return (
                "\n--- [APPLIED AGENT SKILL: verification-before-completion] ---\n"
                f"{desc_line}"
                "You are operating with the 'verification-before-completion' skill from skills.sh:\n"
                "1. The Iron Law: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.\n"
                "2. Identify verification command (e.g. python -m unittest discover -v).\n"
                "3. Run full command, read exit code and test output; count passed and failed assertions.\n"
                "4. Zero fake claims: Only report 'completed' when evidence confirms 100% test passing.\n"
                "---------------------------------------------------\n"
            )

        # Fallback to general instructions snippet
        return f"\n--- [APPLIED AGENT SKILL: {name}] ---\n{desc_line}{skill.instructions[:600]}\n-----------------------------------\n"

    def list_available_skills(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "path": str(s.path),
                "agent": [agent for agent, sk in self.AGENT_SKILL_MAP.items() if sk == s.name],
            }
            for s in self._skills.values()
        ]

    def list_agent_skills(self) -> dict[str, str]:
        return dict(self.AGENT_SKILL_MAP)


_instance: SkillRegistry | None = None


def get_skill_registry(reload: bool = False) -> SkillRegistry:
    global _instance
    if _instance is None:
        _instance = SkillRegistry()
    elif reload or len(_instance._skills) == 0:
        _instance.reload()
    return _instance
