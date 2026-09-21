"""Swarm Observer (Control Tower) - Live status tracking, metrics, communication graph, stall detection, repeat failure detection, and alerts."""

from __future__ import annotations

from typing import Any


class ObserverAgent:
    """Control Tower observer agent. Passively monitors pipeline state, performance, and communication graph."""

    name = "Swarm Observer"
    STALL_THRESHOLD_MS = 5000.0  # Execution SLA threshold for stall detection

    def inspect(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        stages = pipeline.get("stages", [])
        events = pipeline.get("events", [])
        logs = pipeline.get("logs", [])

        failed_agents = [stage["agent"] for stage in stages if stage.get("status") in ("failed", "error")]
        completed_agents = [stage["agent"] for stage in stages if stage.get("status") == "completed"]
        healed_agents = [stage["agent"] for stage in stages if stage.get("status") == "healed"]

        # Performance Metrics
        agent_durations = {stage["agent"]: round(stage.get("duration_ms", 0.0), 2) for stage in stages}
        total_duration_ms = round(sum(agent_durations.values()), 2)
        avg_duration_ms = round(total_duration_ms / len(stages), 2) if stages else 0.0

        # Stall Detection
        stalled_agents = [
            agent for agent, duration in agent_durations.items()
            if duration > self.STALL_THRESHOLD_MS
        ]

        # Repeated Failure & Retry Tracking
        retry_events = [e for e in events if "RETRY" in e.get("event", "") or "ROLLBACK" in e.get("event", "")]
        retry_count = len(retry_events)

        failure_counts: dict[str, int] = {}
        for event in events:
            if "FAIL" in event.get("event", "") or "REVISE" in event.get("event", ""):
                agent = event.get("agent", "Unknown")
                failure_counts[agent] = failure_counts.get(agent, 0) + 1
        
        repeated_failures = [agent for agent, count in failure_counts.items() if count > 1]

        # Agent Communication & Tracing
        communication_graph: list[dict[str, Any]] = []
        for i in range(len(events) - 1):
            src = events[i].get("agent")
            dst = events[i + 1].get("agent")
            if src and dst and src != dst:
                communication_graph.append({
                    "from_agent": src,
                    "to_agent": dst,
                    "trigger_event": events[i].get("event"),
                    "timestamp": events[i].get("timestamp"),
                })

        # Alerting Generator
        alerts: list[dict[str, Any]] = []
        if failed_agents:
            alerts.append({
                "severity": "CRITICAL",
                "type": "AGENT_FAILURE",
                "message": f"Agents failed: {', '.join(failed_agents)}",
                "agents": failed_agents,
            })
        if stalled_agents:
            alerts.append({
                "severity": "MEDIUM",
                "type": "STALLED_AGENT",
                "message": f"Agents exceeded latency SLA ({self.STALL_THRESHOLD_MS}ms): {', '.join(stalled_agents)}",
                "agents": stalled_agents,
            })
        if repeated_failures:
            alerts.append({
                "severity": "HIGH",
                "type": "REPEATED_FAILURE",
                "message": f"Repeated failures detected for agents: {', '.join(repeated_failures)}",
                "agents": repeated_failures,
            })

        # Overall Status Calculation
        if failed_agents:
            overall_status = "attention_required"
        elif stalled_agents or repeated_failures:
            overall_status = "warning"
        else:
            overall_status = "watching"

        return {
            "status": overall_status,
            "role": "Control Tower",
            "agents_monitored": len(stages),
            "agents_completed": len(completed_agents),
            "agents_healed": len(healed_agents),
            "failures_detected": len(failed_agents),
            "failed_agents": failed_agents,
            "retries": retry_count,
            "performance_metrics": {
                "total_duration_ms": total_duration_ms,
                "avg_duration_ms": avg_duration_ms,
                "agent_durations_ms": agent_durations,
                "log_entries_count": len(logs),
                "total_events_count": len(events),
            },
            "stall_analysis": {
                "stalled_agents": stalled_agents,
                "threshold_ms": self.STALL_THRESHOLD_MS,
            },
            "failure_analysis": {
                "repeated_failures": repeated_failures,
                "failure_counts": failure_counts,
            },
            "communication_graph": communication_graph[:15],  # Top inter-agent communications
            "alerts": alerts,
            "latest_event": events[-1] if events else None,
            "message": (
                f"Control Tower active: {len(alerts)} alert(s) generated."
                if alerts else "Control Tower is actively monitoring swarm health."
            ),
        }

