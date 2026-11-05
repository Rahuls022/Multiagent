---
name: observability
description: Use when monitoring runtime service availability, latency profiling, error log analysis, and automated self-healing triggers
---

# Observability & Runtime Monitoring

## Overview
Continuous monitoring of post-deployment services. Collect telemetry metrics (HTTP status codes, latency, CPU/memory estimates), analyze server logs for runtime errors, and trigger self-healing workflows if incidents are detected.

**Announce at start:** "I'm using the observability skill to verify live telemetry, probe endpoint latency, and monitor service health."

## Core Principles
1. **Live Health Verification**: Probe deployed endpoints using HTTP requests; distinguish between healthy 200 OK responses and 4xx/5xx failure states.
2. **Latency Profiling**: Measure millisecond response times and evaluate against SLA thresholds (<500ms).
3. **Telemetry Attribution**: Record CPU, memory, uptime, and active subsystem indicators in mission logs.
4. **Autonomous Incident Detection**: Flag any unreachable endpoint, uncaught exception, or socket timeout as an actionable incident.
5. **Self-Healing Bridge**: If an incident occurs, synthesize root-cause diagnostics and trigger automated remediation.
