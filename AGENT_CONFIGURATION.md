---
title: Security Agent Configuration Guide
author: tsumrad
date: 2026-06-21
toc: true
numbersections: true
---

# Security Agent Configuration Guide

## Executive Summary

The Security & Vulnerability Management Agent is controlled through YAML configuration. The configuration file defines scan targets, threshold policy, routing rules, environment overrides, and authentication expectations.

---

## 1. Configuration Structure

### 1.1 Top-Level Layout

```yaml
version: 1

github:
  owner: your-org
  repo: your-repo
  api_url: https://api.github.com

targets:
  code_scanning: true
  dependabot_alerts: true
  dependabot_prs: true

thresholds:
  cvss:
    critical: 9.0
    high: 7.0
    medium: 4.0
  auto_merge:
    allow_patch: true
    allow_minor: true
    allow_major: false

routing:
  labels:
    critical: security-critical
    high: security-high
  reviewers:
    critical:
      - security-team
    production:
      - platform-team

environments:
  production:
    approval_required: true
  development:
    approval_required: false
```

---

## 2. YAML Sections

### 2.1 `github`

| Field | Type | Description |
|-------|------|-------------|
| `owner` | string | Repository owner |
| `repo` | string | Repository name |
| `api_url` | string | GitHub API base URL |
| `graphql_url` | string | Optional GraphQL endpoint |

### 2.2 `targets`

Use `targets` to enable or disable data sources.

```yaml
targets:
  code_scanning: true
  dependabot_alerts: true
  dependabot_prs: true
```

### 2.3 `thresholds`

Use `thresholds` to define severity boundaries and lifecycle policy.

```yaml
thresholds:
  cvss:
    critical: 9.0
    high: 7.0
    medium: 4.0
  stale_pr_days: 7
  overdue_findings_days:
    critical: 1
    high: 7
    medium: 30
```

---

## 3. Threshold Settings

### 3.1 CVSS Mapping

| Score | Priority | Default Handling |
|-------|----------|------------------|
| `>= 9.0` | Critical | Escalate immediately |
| `>= 7.0` | High | Review within normal SLA |
| `>= 4.0` | Medium | Queue for planned remediation |
| `< 4.0` | Low | Batch or defer by policy |

### 3.2 Severity Overrides

```yaml
thresholds:
  severity_overrides:
    package:
      openssl: critical
    rule:
      js/sql-injection: critical
```

### 3.3 Auto-Merge Controls

```yaml
thresholds:
  auto_merge:
    allow_patch: true
    allow_minor: true
    allow_major: false
    require_green_checks: true
```

---

## 4. Alert Routing Rules

### 4.1 Label Routing

```yaml
routing:
  labels:
    critical: security-critical
    high: security-high
    auto_merge: dependencies-auto-merge
```

### 4.2 Reviewer Routing

```yaml
routing:
  reviewers:
    critical:
      - security-team
    ecosystems:
      npm:
        - web-platform-team
      pip:
        - data-platform-team
```

### 4.3 Escalation Rules

```yaml
routing:
  escalation:
    critical_hours: 4
    stale_pr_days: 7
    notify:
      - security-oncall
      - engineering-manager
```

---

## 5. Environment-Specific Settings

### 5.1 Example Overrides

```yaml
environments:
  production:
    approval_required: true
    auto_merge: false
  staging:
    approval_required: true
    auto_merge: false
  development:
    approval_required: false
    auto_merge: true
```

### 5.2 Branch and Service Scoping

```yaml
environments:
  production:
    branches:
      - main
      - release/*
    services:
      - api
      - auth
```

---

## 6. API Credentials and Security Setup

### 6.1 Minimum Permissions

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
  security-events: read
```

### 6.2 Secret Management

- Store credentials in GitHub Actions secrets or a supported secret manager
- Do not commit personal access tokens into configuration files
- Prefer GitHub App or workflow token authentication where possible

### 6.3 Example Secret Wiring

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  SECURITY_AGENT_CONFIG: .github/security-agent/config.yml
```

---

## 7. Hardened Configuration Example

```yaml
version: 1

github:
  owner: your-org
  repo: your-repo

targets:
  code_scanning: true
  dependabot_alerts: true
  dependabot_prs: true

thresholds:
  cvss:
    critical: 9.0
    high: 7.0
    medium: 4.0
  auto_merge:
    allow_patch: true
    allow_minor: false
    allow_major: false
    require_green_checks: true

routing:
  labels:
    critical: security-critical
    high: security-high
    review_required: security-review
  reviewers:
    critical:
      - security-team
    production:
      - platform-team
  escalation:
    critical_hours: 2
    notify:
      - security-oncall

environments:
  production:
    approval_required: true
    auto_merge: false
```

---

## 8. Validation Guidance

- Validate YAML syntax before rollout
- Start with report-only mode in a non-production repository
- Review routing outcomes before enabling auto-merge
- Revisit thresholds periodically as package mix and risk posture change
