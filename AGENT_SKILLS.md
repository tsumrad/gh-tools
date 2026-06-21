---
title: Security Agent Skills Reference
author: tsumrad
date: 2026-06-21
toc: true
numbersections: true
---

# Security Agent Skills Reference

## Executive Summary

The Security & Vulnerability Management Agent is composed of five reusable skills. Each skill performs one focused part of the workflow while sharing the same policy, identity, and reporting model.

---

## 1. Skill Inventory

| Skill | Primary Role | Key Outputs |
|-------|--------------|-------------|
| Vulnerability Scanner | Collect and normalize findings | Structured alert inventory |
| Dependabot Analyzer | Review open dependency PRs | Change impact summary |
| Risk Scorer | Rank urgency and exposure | Priority score and SLA tier |
| PR Orchestrator | Move PRs through lifecycle | Labels, comments, approvals, merge actions |
| Report Generator | Summarize posture and trends | Markdown/JSON reports |

---

## 2. Vulnerability Scanner Skill

### 2.1 Responsibilities

- Fetch code scanning findings and advisory-linked dependency alerts
- Normalize alert fields into one schema
- Correlate duplicated findings by package, rule, location, or advisory
- Capture source, severity, status, component, and remediation metadata

### 2.2 Inputs

```yaml
skill: vulnerability_scanner
input:
  repositories:
    - owner/repo
  include:
    code_scanning: true
    dependabot_alerts: true
  state: open
```

### 2.3 Outputs

```json
{
  "findings": [
    {
      "id": "code-scanning:42",
      "source": "code_scanning",
      "severity": "high",
      "rule_id": "js/sql-injection",
      "state": "open",
      "component": "api/orders"
    }
  ]
}
```

### 2.4 Notes

- Best for scheduled scans and backlog refreshes
- Should page through GitHub results until inventory is complete
- Can be configured to ignore dismissed or fixed findings

---

## 3. Dependabot Analyzer Skill

### 3.1 Responsibilities

- List open Dependabot pull requests
- Inspect package ecosystem, version delta, lockfile churn, and changed files
- Link PRs back to alerts or advisories when possible
- Detect potentially risky upgrades such as majors or broad transitive changes

### 3.2 Inputs

```yaml
skill: dependabot_analyzer
input:
  selectors:
    author: app/dependabot
    state: open
  inspect_files: true
```

### 3.3 Outputs

```json
{
  "pull_requests": [
    {
      "number": 87,
      "ecosystem": "npm",
      "dependency": "axios",
      "from_version": "1.7.2",
      "to_version": "1.7.9",
      "update_type": "patch",
      "linked_alerts": 1
    }
  ]
}
```

### 3.4 Notes

- Use with branch protection context before auto-merge decisions
- Treat major updates as manual-review candidates by default

---

## 4. Risk Scorer Skill

### 4.1 Responsibilities

- Map GitHub severity and advisory data into a unified score
- Apply CVSS-based thresholds and repository policy overrides
- Elevate risk for production systems, privileged code paths, or internet-facing services
- Assign SLA targets and escalation bands

### 4.2 Scoring Factors

| Factor | Example | Effect |
|--------|---------|--------|
| Base severity | Critical advisory | Strong increase |
| CVSS | 9.8 | Strong increase |
| Exposure | Public API or auth path | Increase |
| Update type | Major version bump | Increase |
| Environment | Production dependency | Increase |
| Package scope | Dev-only tooling | Potential decrease |

### 4.3 Example Output

```json
{
  "score": 92,
  "priority": "critical",
  "sla_hours": 24,
  "reasons": [
    "CVSS >= 9.0",
    "runtime dependency",
    "internet-facing service"
  ]
}
```

---

## 5. PR Orchestrator Skill

### 5.1 Responsibilities

- Apply labels such as `security`, `dependabot`, `critical`, or `auto-merge`
- Request reviewers based on ownership and severity
- Comment with remediation guidance and rollout notes
- Merge low-risk updates when policy and checks allow
- Hold or escalate high-risk changes

### 5.2 Example Actions

```yaml
skill: pr_orchestrator
input:
  pull_request: 87
  actions:
    label:
      - security
      - auto-merge
    request_reviewers:
      - platform-team
    comment: true
```

### 5.3 Decision Rules

- Auto-merge only when checks are green and policy allows
- Request approval for major upgrades or critical production dependencies
- Re-open stalled items through reminder comments or routing rules

---

## 6. Report Generator Skill

### 6.1 Responsibilities

- Produce repository posture summaries
- Group findings by severity, owner, service, or ecosystem
- Track stale PRs, overdue findings, and remediation throughput
- Emit operator reports and executive summaries

### 6.2 Example Outputs

```yaml
skill: report_generator
input:
  format: markdown
  include:
    - severity_breakdown
    - stale_prs
    - overdue_findings
```

```markdown
## Security Summary

- Critical findings: 1
- High findings: 4
- Open Dependabot PRs: 7
- Overdue items: 2
```

---

## 7. Skill Composition Patterns

### 7.1 Full Triage Run

1. `vulnerability_scanner`
2. `dependabot_analyzer`
3. `risk_scorer`
4. `pr_orchestrator`
5. `report_generator`

### 7.2 Report-Only Run

1. `vulnerability_scanner`
2. `dependabot_analyzer`
3. `report_generator`

### 7.3 Merge-Readiness Run

1. `dependabot_analyzer`
2. `risk_scorer`
3. `pr_orchestrator`

---

## 8. Failure Handling Guidelines

- Retry GitHub API reads with backoff
- Preserve partial inventories when pagination fails
- Mark uncertain classifications as `needs_review`
- Never auto-merge when the risk score or policy result is incomplete
