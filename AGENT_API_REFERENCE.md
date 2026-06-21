---
title: Security Agent API Reference
author: tsumrad
date: 2026-06-21
toc: true
numbersections: true
---

# Security Agent API Reference

## Executive Summary

This reference defines how the Security & Vulnerability Management Agent skills are invoked, which data they exchange, how GitHub integration is performed, and how failures are handled.

---

## 1. Skill Invocation Syntax

### 1.1 Generic Invocation

```yaml
skill: <skill_name>
input:
  repository: owner/repo
  options: {}
```

### 1.2 Supported Skill Names

```yaml
- vulnerability_scanner
- dependabot_analyzer
- risk_scorer
- pr_orchestrator
- report_generator
```

### 1.3 Composite Invocation Example

```yaml
workflow:
  - skill: vulnerability_scanner
  - skill: dependabot_analyzer
  - skill: risk_scorer
  - skill: pr_orchestrator
  - skill: report_generator
```

---

## 2. Core Data Models and Types

### 2.1 Finding

```ts
type Finding = {
  id: string;
  source: "code_scanning" | "dependabot_alert";
  severity: "critical" | "high" | "medium" | "low";
  state: "open" | "dismissed" | "fixed";
  package?: string;
  ecosystem?: string;
  ruleId?: string;
  location?: string;
  cvss?: number;
};
```

### 2.2 Dependabot Pull Request

```ts
type DependabotPullRequest = {
  number: number;
  dependency: string;
  ecosystem: string;
  fromVersion: string;
  toVersion: string;
  updateType: "patch" | "minor" | "major";
  linkedAlerts: number;
  mergeable?: boolean;
};
```

### 2.3 Risk Assessment

```ts
type RiskAssessment = {
  score: number;
  priority: "critical" | "high" | "medium" | "low";
  slaHours: number;
  reasons: string[];
};
```

---

## 3. Input and Output Specifications

### 3.1 Vulnerability Scanner

**Input**

```yaml
skill: vulnerability_scanner
input:
  repository: owner/repo
  state: open
```

**Output**

```yaml
findings:
  - id: code-scanning:42
    source: code_scanning
    severity: high
```

### 3.2 Dependabot Analyzer

**Input**

```yaml
skill: dependabot_analyzer
input:
  repository: owner/repo
  state: open
```

**Output**

```yaml
pull_requests:
  - number: 87
    dependency: axios
    update_type: patch
```

### 3.3 PR Orchestrator

**Input**

```yaml
skill: pr_orchestrator
input:
  pull_request: 87
  decision:
    auto_merge: false
    labels:
      - security-review
```

**Output**

```yaml
result:
  status: updated
  actions_applied:
    - labeled
    - reviewers_requested
```

---

## 4. GitHub API Integration Points

### 4.1 Alert Retrieval

| API | Purpose |
|-----|---------|
| `GET /repos/{owner}/{repo}/code-scanning/alerts` | Retrieve code scanning findings |
| `GET /repos/{owner}/{repo}/dependabot/alerts` | Retrieve dependency alerts |

### 4.2 Pull Request Retrieval

| API | Purpose |
|-----|---------|
| `GET /repos/{owner}/{repo}/pulls` | List open pull requests |
| `GET /repos/{owner}/{repo}/pulls/{pull_number}` | Read PR metadata |
| `GET /repos/{owner}/{repo}/pulls/{pull_number}/files` | Inspect changed files |

### 4.3 Orchestration Actions

| API | Purpose |
|-----|---------|
| `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` | Publish guidance |
| `POST /repos/{owner}/{repo}/issues/{issue_number}/labels` | Apply routing labels |
| `POST /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers` | Request approvals |
| `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` | Merge approved low-risk PRs |

---

## 5. Error Handling and Recovery

### 5.1 Error Classes

| Error | Meaning | Recovery |
|-------|---------|----------|
| `rate_limit` | GitHub API quota exhausted | Retry after reset window |
| `auth_failed` | Token missing or insufficient | Stop and request corrected credentials |
| `partial_inventory` | Pagination or source fetch incomplete | Keep partial results, flag review |
| `policy_denied` | Action blocked by config | Route to manual approval |

### 5.2 Recovery Strategy

```yaml
recovery:
  retries:
    max_attempts: 3
    backoff: exponential
  on_partial_data: needs_review
  on_merge_uncertainty: hold
```

### 5.3 Idempotency Guidance

- Use stable finding and PR identifiers
- Avoid duplicate comments by tagging agent-generated output
- Recompute labels and reviewers from desired state on each run

---

## 6. Example Skill Payloads

### 6.1 Risk Scoring Request

```json
{
  "skill": "risk_scorer",
  "input": {
    "finding": {
      "severity": "critical",
      "cvss": 9.8,
      "package": "openssl"
    }
  }
}
```

### 6.2 Report Generation Response

```json
{
  "status": "ok",
  "report": {
    "critical_findings": 1,
    "high_findings": 4,
    "stale_dependabot_prs": 2
  }
}
```

---

## 7. Compatibility Notes

- Designed for GitHub-hosted repositories using code scanning and Dependabot
- Works best when branch protection and review rules are already defined
- Policy behavior should be versioned alongside repository workflow changes
