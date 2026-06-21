---
title: Security Agent Workflow Guide
author: tsumrad
date: 2026-06-21
toc: true
numbersections: true
---

# Security Agent Workflow Guide

## Executive Summary

This document describes the core workflows executed by the Security & Vulnerability Management Agent, from detection through remediation and reporting.

---

## 1. End-to-End Vulnerability Remediation Workflow

### 1.1 Overview

```text
┌──────────────┐   ┌──────────────┐   ┌────────────┐   ┌──────────────┐
│ Discover     │→→│ Analyze      │→→│ Prioritize │→→│ Orchestrate   │
└──────────────┘   └──────────────┘   └────────────┘   └──────┬───────┘
                                                               │
                                                               ▼
                                                     ┌──────────────────┐
                                                     │ Report + Metrics │
                                                     └──────────────────┘
```

### 1.2 Workflow Steps

1. Collect open code scanning alerts and dependency findings
2. Normalize records and enrich with advisory metadata
3. Score each finding using configured thresholds
4. Match findings to open Dependabot PRs where possible
5. Route remediation actions by severity and environment
6. Emit a report and backlog summary

---

## 2. Dependabot PR Management Workflow

### 2.1 Decision Path

```text
Open Dependabot PR
        │
        ▼
Analyze package, scope, and linked alerts
        │
        ├─ Patch/minor + green checks + allowed policy ──► Auto-merge path
        │
        └─ Major / risky / production-sensitive ─────────► Manual approval path
```

### 2.2 Workflow Rules

- Auto-merge only patch or explicitly allowed minor upgrades
- Request human approval for major updates
- Hold changes touching critical services until required reviewers approve
- Re-check stale PRs and remind owners when SLA thresholds are exceeded

---

## 3. Escalation and Approval Workflow

### 3.1 Escalation Triggers

- Critical severity finding
- Overdue remediation window
- Production dependency with failing checks
- Major upgrade lacking ownership confirmation

### 3.2 Approval Sequence

1. Label item as `security-review`
2. Request security and service-owner reviewers
3. Post context comment with risk summary and recommendation
4. Block merge until checks and approvals satisfy policy

### 3.3 Example Approval Payload

```yaml
approval:
  required: true
  reviewers:
    - security-team
    - service-owner
  reason: "Critical runtime dependency update"
```

---

## 4. Batch Processing Workflow

### 4.1 Use Cases

- Scheduled hourly or daily backlog refresh
- Weekly repository security posture review
- Organization-wide dependency hygiene sweep

### 4.2 Batch Flow

1. Enumerate repositories or targets
2. Run vulnerability scanning inventory
3. Aggregate Dependabot PR state
4. Compute scores and queue actions
5. Publish one report per repository or portfolio

### 4.3 Safeguards

- Use pagination checkpoints for large repositories
- Persist partial progress when API rate limits are encountered
- Separate report generation from merge execution when running at scale

---

## 5. Reporting and Metrics Workflow

### 5.1 Standard Metrics

| Metric | Description |
|--------|-------------|
| Open critical findings | Count of unresolved critical items |
| Mean time to triage | Time from detection to first decision |
| Mean time to remediate | Time from detection to closure |
| Stale Dependabot PRs | Open PRs beyond configured threshold |
| Auto-merge success rate | Fraction of approved PRs merged automatically |

### 5.2 Report Cycle

1. Gather current findings and PR state
2. Compare against previous reporting window
3. Highlight newly introduced and closed items
4. Publish markdown summary and optional machine-readable output

---

## 6. Example End-to-End Scenario

1. A new critical dependency alert is opened in GitHub
2. The agent detects a matching Dependabot PR
3. The PR is scored as critical because it affects a production runtime dependency
4. The orchestrator labels the PR, requests reviewers, and posts remediation guidance
5. After checks and approvals pass, the PR is merged according to policy
6. The report generator updates the backlog and remediation metrics

---

## 7. Failure Recovery

- Retry transient GitHub API failures
- Continue report generation even when one source is temporarily unavailable
- Fall back to manual-review state when scoring data is incomplete
- Mark blocked items explicitly so they are re-evaluated on the next run
