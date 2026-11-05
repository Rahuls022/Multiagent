---
name: security-audit
description: Use when scanning generated source code for exposed secrets, API keys, path traversal, dangerous commands, and CVE vulnerabilities
---

# Security Audit

## Overview
Perform automated zero-trust security audits on all generated application artifacts before deployment. Inspect files for hardcoded secrets, database credentials, insecure deserialization, command injection, and OWASP Top 10 vulnerabilities.

**Announce at start:** "I'm using the security-audit skill to perform zero-trust code scanning and secret leak detection."

## Core Principles
1. **Zero-Trust Verification**: Never assume client code is benign. Every input, query parameter, and filesystem path must be checked.
2. **Secret Detection**: Scan for pattern signatures of private keys, bearer tokens, JWT secrets, database connection strings, and cloud vendor API keys.
3. **Command & Script Sanitization**: Verify that no subprocess shell calls execute unescaped user inputs (`eval`, `exec`, arbitrary SQL concatenations).
4. **Boundary Checks**: Check for path traversal vulnerabilities (`../`, `/etc/`, absolute overrides) in file operations.
5. **Quality Gate Verdict**: If high-severity vulnerabilities or credential leaks are detected, stop the pipeline immediately.
