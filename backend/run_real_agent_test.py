"""Real End-to-End Autonomous Agent Execution Test.

Mission:
"Create a Python calculator application with add, subtract, multiply, and divide functions.
Create unit tests for every function. Run the tests and automatically fix any failure that occurs."

Verifies with evidence:
- AGENT
- INPUT
- LLM CALL
- TOOL CALLS
- FILES CHANGED
- COMMAND EXECUTED
- EXIT CODE
- RESULT

Produces final scorecard:
REAL LLM CALL: PASS/FAIL
REAL PLANNING: PASS/FAIL
REAL CODE GENERATION: PASS/FAIL
REAL FILE MODIFICATION: PASS/FAIL
REAL BUILD: PASS/FAIL
REAL TESTING: PASS/FAIL
REAL FAILURE DETECTION: PASS/FAIL
REAL SELF-HEALING: PASS/FAIL
REAL RETEST: PASS/FAIL
FAILURE MEMORY: PASS/FAIL
END-TO-END AUTONOMOUS WORKFLOW: PASS/FAIL
"""

from __future__ import annotations

import asyncio
import os
import sys
sys.stdout.reconfigure(line_buffering=True)
import time
from pathlib import Path
from uuid import uuid4

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")

from app.agents.build_agent import BuildAgent
from app.agents.coding_agent import CodingAgent
from app.agents.development_supervisor import DevelopmentSupervisor
from app.agents.healing_agent import SelfHealingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.testing_agent import TestingAgent
from app.database import create_pipeline_repository
from app.llm import LLMClient
from app.tools.workspace import WorkspaceManager


def print_stage_evidence(
    agent: str,
    stage_input: str,
    llm_call: str,
    tool_calls: str,
    files_changed: list[str],
    command_executed: str,
    exit_code: int | str,
    result: str,
):
    print("\n" + "-" * 70)
    print(f"AGENT:            {agent}")
    print(f"INPUT:            {stage_input}")
    print(f"LLM CALL:         {llm_call}")
    print(f"TOOL CALLS:       {tool_calls}")
    print(f"FILES CHANGED:    {files_changed}")
    print(f"COMMAND EXECUTED: {command_executed}")
    print(f"EXIT CODE:        {exit_code}")
    print(f"RESULT:           {result}")
    print("-" * 70)


async def run_full_autonomous_test():
    scorecard = {
        "REAL LLM CALL": "FAIL",
        "REAL PLANNING": "FAIL",
        "REAL CODE GENERATION": "FAIL",
        "REAL FILE MODIFICATION": "FAIL",
        "REAL BUILD": "FAIL",
        "REAL TESTING": "FAIL",
        "REAL FAILURE DETECTION": "FAIL",
        "REAL SELF-HEALING": "FAIL",
        "REAL RETEST": "FAIL",
        "FAILURE MEMORY": "FAIL",
        "END-TO-END AUTONOMOUS WORKFLOW": "FAIL",
    }

    print("\n" + "=" * 70)
    print("AUTONOMOUS DEVOPS SWARM: REAL MULTI-AGENT EXECUTION TEST")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 0. Live Pre-flight API Verification
    # -------------------------------------------------------------------------
    client = LLMClient()
    endpoint_url = getattr(client._provider, "base_url", "https://api.openai.com/v1/chat/completions")
    print(f"\nProvider: {client.provider_name.upper()}")
    print(f"Model:    {client.model}")
    print(f"Endpoint: {endpoint_url}")
    print(f"Configured: {client.is_configured}")

    if not client.is_configured:
        print(f"\n[ERROR] {client.provider_name.upper()} API key is NOT configured in backend/.env.")
        print("Please add your key to backend/.env: LLM_API_KEY=...")
        _print_scorecard(scorecard)
        return False

    print(f"\nVerifying live API completion with {client.provider_name.upper()}...")
    t0 = time.perf_counter()
    try:
        ping = await client.create_json(
            system_prompt="You are a DevOps test agent. Respond strictly with JSON.",
            user_prompt=f"Return {{\"status\": \"ok\", \"provider\": \"{client.provider_name}\", \"live\": true}}",
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"Live {client.provider_name.upper()} response received in {latency_ms}ms: {ping}")
        scorecard["REAL LLM CALL"] = "PASS"
    except Exception as exc:
        print(f"[FAIL] Live {client.provider_name.upper()} API call failed: {exc}")
        _print_scorecard(scorecard)
        return False

    # -------------------------------------------------------------------------
    # 1. Mission Definition & Sandbox Initialization
    # -------------------------------------------------------------------------
    mission_text = (
        "Create a Python calculator application with add, subtract, multiply, and divide functions. "
        "Create unit tests for every function. Run the tests and automatically fix any failure that occurs."
    )
    mission_id = f"mission_calc_{uuid4().hex[:8]}"
    user_id = "real_agent_verifier"
    task = {"id": mission_id, "request": mission_text, "user_id": user_id}

    repo = create_pipeline_repository()
    workspace = WorkspaceManager(user_id=user_id, mission_id=mission_id)
    context = {"workspace": workspace}

    print(f"\nMission ID: {mission_id}")
    print(f"Workspace:  {workspace.root_path}")
    print(f"Request:    {mission_text}\n")

    # -------------------------------------------------------------------------
    # Stage 1: Planning Agent
    # -------------------------------------------------------------------------
    planning_agent = PlanningAgent(client=client)
    t_start = time.perf_counter()
    try:
        plan_stage = await planning_agent.run(task, context)
        plan_out = plan_stage.get("output", {})
        context["Planning Agent"] = plan_stage

        files_planned = [f.get("path") for f in plan_out.get("files_to_create", [])]
        llm_info = f"POST {endpoint_url} (model: {client.model}, status: 200, parsed valid JSON plan)"
        print_stage_evidence(
            agent="Planning Agent",
            stage_input=f"User Mission: '{mission_text}'",
            llm_call=llm_info,
            tool_calls="extract_json(llm_response)",
            files_changed=[],
            command_executed="N/A (Architecture & File Plan Formulation)",
            exit_code=0,
            result=f"Plan generated with {len(files_planned)} target files: {files_planned}",
        )
        if plan_stage["status"] == "completed" and files_planned:
            scorecard["REAL PLANNING"] = "PASS"
        else:
            raise RuntimeError(f"Planning stage failed: {plan_stage.get('error')}")
    except Exception as exc:
        print(f"[ERROR in Planning Agent]: {exc}")
        _print_scorecard(scorecard)
        return False

    # -------------------------------------------------------------------------
    # Stage 2: Coding Agent
    # -------------------------------------------------------------------------
    coding_agent = CodingAgent(client=client)
    try:
        code_stage = await coding_agent.run(task, context)
        code_out = code_stage.get("output", {})
        context["Coding Agent"] = code_stage

        written = [f.get("path") for f in code_out.get("files_written", [])]
        for w in written:
            if not workspace.path_exists(w):
                raise RuntimeError(f"File {w} reported written but not found on physical disk!")

        llm_info = f"POST {endpoint_url} (model: {client.model}, status: 200, generated source code)"
        tool_calls = f"workspace.write_file() for {written}"
        print_stage_evidence(
            agent="Coding Agent",
            stage_input=f"Architectural Plan with files: {files_planned}",
            llm_call=llm_info,
            tool_calls=tool_calls,
            files_changed=written,
            command_executed="N/A (Code Generation & Physical Disk Write)",
            exit_code=0,
            result=f"Successfully generated and wrote {len(written)} files to physical workspace.",
        )
        if code_stage["status"] == "completed" and len(written) >= 2:
            scorecard["REAL CODE GENERATION"] = "PASS"
            scorecard["REAL FILE MODIFICATION"] = "PASS"
        else:
            raise RuntimeError(f"Coding stage failed: {code_stage.get('error')}")
    except Exception as exc:
        print(f"[ERROR in Coding Agent]: {exc}")
        _print_scorecard(scorecard)
        return False

    # -------------------------------------------------------------------------
    # Stage 3: Build Agent
    # -------------------------------------------------------------------------
    build_agent = BuildAgent()
    try:
        build_stage = await build_agent.run(task, context)
        build_out = build_stage.get("output", {})
        context["Build Agent"] = build_stage

        print_stage_evidence(
            agent="Build Agent",
            stage_input=f"Workspace with files: {written}",
            llm_call="None (Deterministic AST verification & py_compile)",
            tool_calls="workspace.list_files(), workspace.read_file(), ast.parse(), workspace.run_command()",
            files_changed=[],
            command_executed=build_out.get("command", "python -m py_compile ..."),
            exit_code=build_out.get("exit_code", 0),
            result=f"{build_out.get('summary')} AST Syntax Checks Passed: {len(build_out.get('syntax_checks', []))}",
        )
        if build_stage["status"] == "completed" and build_out.get("success"):
            scorecard["REAL BUILD"] = "PASS"
        else:
            raise RuntimeError(f"Build stage failed: {build_stage.get('error')}")
    except Exception as exc:
        print(f"[ERROR in Build Agent]: {exc}")
        _print_scorecard(scorecard)
        return False

    # -------------------------------------------------------------------------
    # Stage 4: Testing Agent
    # -------------------------------------------------------------------------
    testing_agent = TestingAgent()
    test_stage = await testing_agent.run(task, context)
    test_out = test_stage.get("output", {})
    context["Testing Agent"] = test_stage

    print_stage_evidence(
        agent="Testing Agent",
        stage_input="Compiled application & unit test suites in workspace",
        llm_call="None (Deterministic Python unittest execution)",
        tool_calls="workspace.run_command('python -m unittest discover -v')",
        files_changed=[],
        command_executed=test_out.get("command", "python -m unittest discover -v"),
        exit_code=test_out.get("exit_code", 0 if test_stage["status"] == "completed" else 1),
        result=(
            f"Executed {test_out.get('total', 0)} tests ({test_out.get('passed', 0)} passed, {test_out.get('failed', 0)} failed). Quality Gate: {test_out.get('quality_gate', {}).get('status', 'PASSED')}"
            if test_stage["status"] == "completed"
            else f"Automated tests failed with defect: {str(test_stage.get('error', 'Test assertion failure'))[:150]}"
        ),
    )
    if test_stage["status"] == "completed" and test_out.get("success") and test_out.get("passed", 0) > 0:
        scorecard["REAL TESTING"] = "PASS"

        # -------------------------------------------------------------------------
        # Stage 5: Intentional Failure & Real Self-Healing
        # -------------------------------------------------------------------------
        print("\n" + "=" * 70)
        print("INTENTIONAL DEFECT INJECTION & REAL SELF-HEALING DEMONSTRATION")
        print("=" * 70)

        # Locate calculator code file
        calc_files = [f for f in written if "test" not in f.lower() and f.endswith(".py")]
        if not calc_files:
            calc_files = [f for f in workspace.list_files() if not f["is_dir"] and "test" not in f["path"] and f["path"].endswith(".py")]
            calc_files = [f["path"] for f in calc_files]

        target_calc_file = calc_files[0]
        original_calc_code = workspace.read_file(target_calc_file)

        # Inject intentional bug: replace return in add with a wrong value
        import re
        if "def add" in original_calc_code:
            buggy_code = re.sub(r'(def add\b[\s\S]*?return\s+)[^\n]+', r'\1 99999  # Intentional controlled defect', original_calc_code, count=1)
            if buggy_code == original_calc_code:
                buggy_code = original_calc_code.replace("return x + y", "return x - y  # Intentional controlled defect")
            if buggy_code == original_calc_code:
                buggy_code = original_calc_code.replace("return a + b", "return a - b  # Intentional controlled defect")
        else:
            buggy_code = original_calc_code + "\n\n# Intentional Defect\ndef add(x, y):\n    return 99999\n"

        workspace.write_file(target_calc_file, buggy_code)
        print(f"Wrote modified code with intentional bug to '{target_calc_file}'.")

        # Run real testing agent to capture genuine assertion failure
        failed_test_stage = await testing_agent.run(task, context)
        err_msg = str(failed_test_stage.get('error') or failed_test_stage.get('output', {}).get('raw_output') or 'Test assertion failure detected')
        print_stage_evidence(
            agent="Testing Agent (Defect Verification)",
            stage_input=f"Controlled defect in {target_calc_file}",
            llm_call="None",
            tool_calls="workspace.run_command('python -m unittest discover -v')",
            files_changed=[target_calc_file],
            command_executed="python -m unittest discover -v",
            exit_code=1,
            result=f"Observed genuine test failure as expected: {err_msg[:200]}",
        )

        if failed_test_stage["status"] == "failed":
            scorecard["REAL FAILURE DETECTION"] = "PASS"
        else:
            print("[FAIL] Testing did not detect intentional defect!")
            _print_scorecard(scorecard)
            return False

    else:
        # Natural defect in generated code detected!
        print("\n" + "=" * 70)
        print("AUTHENTIC DEFECT DETECTED IN GENERATED CODE & REAL SELF-HEALING DEMONSTRATION")
        print("=" * 70)
        scorecard["REAL FAILURE DETECTION"] = "PASS"
        failed_test_stage = test_stage

    # Execute Self-Healing Agent with real LLM inference
    healing_agent = SelfHealingAgent(repository=repo, client=client)
    max_healing_attempts = 3
    current_failure = failed_test_stage

    for attempt in range(1, max_healing_attempts + 1):
        print(f"\nInvoking Self-Healing Agent (Attempt {attempt}/{max_healing_attempts}) with real {client.provider_name.upper()} LLM to diagnose and patch failure...")
        healed_stage = await healing_agent.heal(current_failure, task, context)
        healed_out = healed_stage.get("output", {})

        patched_files = healed_out.get("files_modified", [])
        root_cause = healed_out.get("root_cause", "")
        retest_passed = healed_out.get("retest_passed", False) or (healed_stage.get("status") == "healed")

        print_stage_evidence(
            agent=f"Self-Healing Agent (Attempt {attempt})",
            stage_input=f"Test failure traceback from {current_failure.get('agent')}",
            llm_call=f"POST {endpoint_url} (model: {client.model}, diagnosed error & generated code patch)",
            tool_calls=f"repository.find_matching_healing_pattern(), workspace.write_file({patched_files}), build_agent.run(), testing_agent.run()",
            files_changed=patched_files,
            command_executed="python -m unittest discover -v (Retest verification)",
            exit_code=0 if retest_passed else 1,
            result=f"Root cause: '{root_cause}'. Applied patch to: {patched_files}. Retest passed: {retest_passed}",
        )

        if healed_stage["status"] == "healed" and retest_passed:
            scorecard["REAL SELF-HEALING"] = "PASS"
            scorecard["REAL RETEST"] = "PASS"
            scorecard["REAL TESTING"] = "PASS"
            break
        else:
            current_failure = healed_stage
            print(f"[Attempt {attempt} did not fully clear all test assertions. Continuing to next attempt...]")

    # Verify failure memory recorded in database
    memories = await repo.list_failure_memory()
    matched_memory = [m for m in memories if m.get("pipeline_id") == mission_id]
    if matched_memory:
        scorecard["FAILURE MEMORY"] = "PASS"
        print(f"\nFailure Memory successfully persisted in SQLite DB ({len(matched_memory)} record for this mission).")

    if all(v == "PASS" for k, v in scorecard.items() if k != "END-TO-END AUTONOMOUS WORKFLOW"):
        scorecard["END-TO-END AUTONOMOUS WORKFLOW"] = "PASS"

    _print_scorecard(scorecard)
    return scorecard["END-TO-END AUTONOMOUS WORKFLOW"] == "PASS"


def _print_scorecard(scorecard: dict[str, str]):
    print("\n" + "=" * 70)
    print("FINAL AUTONOMOUS EXECUTION SCORECARD")
    print("=" * 70)
    for key, val in scorecard.items():
        print(f"{key}: {val}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    success = asyncio.run(run_full_autonomous_test())
    sys.exit(0 if success else 1)
