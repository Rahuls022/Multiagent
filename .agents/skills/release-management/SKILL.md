---
name: release-management
description: Use when validating release readiness, packaging release artifacts, verifying quality gates, and managing operator approvals
---

# Release Management

## Overview
Coordinate release validation, version tagging, bundle packaging, and operator approval gates. Ensure that every artifact deployed to staging or production is cryptographically checksummed, versioned, and documented with comprehensive release notes.

**Announce at start:** "I'm using the release-management skill to verify release gates, prepare release bundles, and package metadata."

## Core Principles
1. **Prerequisite Verification**: Confirm that Build Agent, Testing Agent, and Security Agent have all completed with zero critical defects.
2. **Deterministic Versioning**: Generate semantic release tags (`v1.0.x`) and commit hashes tied directly to workspace Git history.
3. **Artifact Bundling**: Package deployable assets with SHA-256 integrity checksums.
4. **Approval Gate Protocol**: For protected environments, halt before deployment and require signed operator approval.
5. **Release Notes Generation**: Document all included files, modules, test coverage figures, and security attestations.

