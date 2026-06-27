---
name: vault-health
description: |
  Checks the integrity and operational health of the AI_Employee_Vault.
  Verifies: all required folders exist (Folder Authority Matrix), no tasks orphaned
  in In_Progress/ (>2h), stale_tasks_detected count for In_Progress/cloud/ and
  In_Progress/local/, sync_lag_seconds from Sync/sync.log last entry,
  health_status classification (healthy: lag<120s, degraded: lag<600s,
  critical: lag>=600s or missing folders), Pending_Approval files stale (>48h),
  Dashboard.md freshness, watcher state files.
  Writes a health report to AI_Employee_Vault/Updates/VAULT_HEALTH_<ts>.md
  (AGENT_ROLE-aware: cloud writes to Updates/ via safe_vault_write(),
  local writes to Updates/ directly). Also writes ERROR_*.md for critical issues.
  Triggered by: "run vault-health skill", "check vault health", "vault status",
  "is the vault healthy", "check system health", cloud orchestrator daily 06:00 UTC.
---

# Vault Health

Audit vault integrity and surface operational issues before they cause failures.

---

## Step 1 — Check Required Folder Structure

Verify all required folders exist in `AI_Employee_Vault/`:

```
Required folders:
  ✓/✗ Inbox/
  ✓/✗ Needs_Action/
  ✓/✗ In_Progress/
  ✓/✗ In_Progress/local/
  ✓/✗ In_Progress/cloud/
  ✓/✗ Plans/
  ✓/✗ Pending_Approval/
  ✓/✗ Approved/
  ✓/✗ Rejected/
  ✓/✗ Done/
  ✓/✗ Briefings/
  ✓/✗ Accounting/
  ✓/✗ Logs/
  ✓/✗ Updates/
  ✓/✗ Signals/
  ✓/✗ Sync/
```

For any missing folder: record as `CRITICAL` issue and note it must be created
before watchers can write output.

---

## Step 2 — Check Required Vault Files

Verify these files exist and are non-empty:

| File | Status if missing |
|------|------------------|
| `Dashboard.md` | WARNING — agent won't update counts |
| `Company_Handbook.md` | CRITICAL — all skills depend on this |
| `Business_Goals.md` | WARNING — CEO briefing and social posts will lack context |
| `Bank_Transactions.md` | WARNING — finance watcher output may fail |

---

## Step 3 — Check for Orphaned In_Progress Tasks

List all files in `AI_Employee_Vault/In_Progress/` (all subfolders).

For each file:
- Read the `created_at` or file modification time
- If age > 2 hours: classify as `ORPHANED`

Orphaned tasks indicate a Claude session crashed mid-task. They should be
moved back to `Needs_Action/` for reprocessing.

For each orphaned task, note its filename and age.

---

## Step 4 — Check for Stale Pending Approvals

List all files in `AI_Employee_Vault/Pending_Approval/`.

For each file:
- Read the `timestamp` from YAML frontmatter
- If age > 48 hours: classify as `STALE`

Stale approvals indicate the owner has not reviewed them. These are informational
warnings — the system should never auto-expire approval files.

---

## Step 5 — Check Dashboard.md Freshness

Read `AI_Employee_Vault/Dashboard.md` and extract the `<!-- AI_EMPLOYEE:UPDATED -->`
timestamp (or check file modification time).

- If last updated < 30 minutes ago: `OK`
- If last updated 30 min – 4 hours ago: `WARNING` — may be behind
- If last updated > 4 hours ago: `STALE` — agent may not be running

---

## Step 6 — Check Watcher State Files

Verify the following state files exist in `scripts/`:

| File | Watcher |
|------|---------|
| `processed_gmail.json` | Gmail watcher |
| `processed_finance.json` | Finance watcher |
| `email_outbox_queue.json` | Email MCP queue |

For each present state file, verify it is valid JSON (parse it).
For any missing or invalid file: record as `WARNING`.

---

## Step 7 — Check Recent Log Activity

List files in `AI_Employee_Vault/Logs/` matching `YYYY-MM-DD.json`.

- If today's log file exists and has ≥ 1 entry: `OK`
- If today's log file is missing: `WARNING` — no activity logged today
- If the newest log file is > 24 hours old: `WARNING` — system may be inactive

---

## Step 7b — Check Sync Health (Platinum)

Read the last non-comment line of `AI_Employee_Vault/Sync/sync.log`.

Parse the timestamp (first pipe-delimited field). Compute `sync_lag_seconds`.

Classify:
- `healthy`: sync_lag_seconds < 120
- `degraded`: 120 ≤ sync_lag_seconds < 600
- `critical`: sync_lag_seconds ≥ 600

Count files in `In_Progress/cloud/` and `In_Progress/local/` (excluding `.gitkeep`).
Record as `stale_tasks_cloud` and `stale_tasks_local`.

If `Sync/sync.log` does not exist: set `sync_lag_seconds: null`, `health_status: critical`.

---

## Step 8 — Write Health Report

Write `AI_Employee_Vault/Updates/VAULT_HEALTH_<ISO-ts>.md`.
If `AGENT_ROLE=cloud`: use `safe_vault_write()` from `watchers/cloud_boundary.py`.
If `AGENT_ROLE=local` (or unset): write directly.

Schema:

```markdown
---
type: vault_health_report
generated_at: <ISO-8601Z>
health_status: <healthy|degraded|critical>
sync_lag_seconds: <int|null>
stale_tasks_cloud: <int>
stale_tasks_local: <int>
overall_status: <OK|WARNING|CRITICAL>
agent_id: <cloud_agent|local_agent>
---

# Vault Health Report — <YYYY-MM-DD T HH:MM>Z

*Generated: <timestamp>*

## Overall Status: <OK 🟢 | WARNING 🟡 | CRITICAL 🔴>

---

## Folder Structure

| Folder | Status |
|--------|--------|
| Inbox/ | ✓ OK |
| Needs_Action/ | ✓ OK |
| ... | ... |

---

## Required Files

| File | Status |
|------|--------|
| Company_Handbook.md | ✓ OK |
| ... | ... |

---

## In_Progress Tasks

<N> orphaned tasks (age > 2h):
- <filename> — <age>
<If none: "No orphaned tasks. ✓">

---

## Pending Approvals

<N> stale approval files (age > 48h):
- <filename> — <age>
<If none: "No stale approvals. ✓">

---

## Dashboard Freshness

Last updated: <timestamp> (<age>)
Status: <OK|WARNING|STALE>

---

## Watcher State Files

| File | Status |
|------|--------|
| processed_gmail.json | ✓ Valid JSON |
| ... | ... |

---

## Log Activity

Newest log file: <filename> (<age>)
Today's log entries: <count>
Status: <OK|WARNING>

---

## Action Items

<Bulleted list of any CRITICAL or WARNING items that need attention>
<If all OK: "No action required. Vault is healthy. ✓">
```

---

## Step 9 — Write ERROR Files for Critical Issues

For each `CRITICAL` issue found (missing required folder, missing
Company_Handbook.md, invalid state files):

Write `AI_Employee_Vault/Needs_Action/ERROR_<ts>_vault-health-<issue-slug>.md`:

```markdown
---
type: error
error_type: vault_health_critical
issue: "<brief issue description>"
timestamp: <ISO-8601Z>
---

## Vault Health Critical Issue

<Full description of the issue and its impact>

## Recommended Fix

<Specific steps to resolve>
```

---

## Step 10 — Log the Health Check

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "vault_health_check",
  "actor": "claude_code",
  "target": "AI_Employee_Vault/",
  "parameters": {
    "overall_status": "<OK|WARNING|CRITICAL>",
    "critical_count": 0,
    "warning_count": 0,
    "orphaned_tasks": 0,
    "stale_approvals": 0,
    "report_file": "Briefings/VAULT_HEALTH_<date>.md"
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "success"
}
```

---

## Completion Signal

After writing the report and log entry:

```
<promise>TASK_COMPLETE</promise>
```
