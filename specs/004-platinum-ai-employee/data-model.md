# Data Model: Platinum Tier Personal AI Employee

**Feature**: `004-platinum-ai-employee`
**Date**: 2026-06-27
**Baseline**: Extends Gold-tier entities. All Gold entities unchanged unless noted.

---

## New Platinum Entities

### 1. Cloud Signal (`Signals/SIGNAL_<type>_<timestamp>.md`)

Written by either agent to alert the other of an abnormal condition. Both agents poll `Signals/` via `signals_watcher.py`.

**Fields**:

| Field | Type | Values | Notes |
|-------|------|---------|-------|
| `signal_id` | string | `SIGNAL_<ISO-timestamp>` | Unique identifier |
| `signal_type` | enum | `task_recovered`, `cloud_down`, `sync_conflict`, `stale_draft`, `disk_alert`, `clock_skew`, `vault_missing_file`, `single_writer_violation`, `shutdown_request`, `plan_ready`, `sync_stalled` | Extensible |
| `originating_agent` | enum | `cloud`, `local` | Who wrote it |
| `created` | ISO-8601Z | — | Write timestamp |
| `severity` | enum | `info`, `warning`, `critical` | `critical` requires human action |
| `requires_human_action` | boolean | `true`/`false` | If true, creates `Needs_Action/` entry |
| `linked_ref` | string or null | File path | Related task/plan/approval |
| `message` | string | Plain language | Description of condition |
| `recommended_action` | string | Plain language | What receiver should do |

**Lifecycle**: Written → signals_watcher reads → response action taken → signal remains as permanent record (never deleted, like `Rejected/`).

**State machine**:
```
(either agent detects condition)
    ↓
Signals/SIGNAL_<type>_<ts>.md created
    ↓
signals_watcher polls (60s interval)
    ↓
[if requires_human_action = true] → Needs_Action/ERROR_SIGNAL_<ts>.md created
[if signal_type = cloud_down]    → Dashboard.md updated to OFFLINE
[if signal_type = single_writer_violation] → log + alert, do NOT write to prohibited path
```

---

### 2. Agent Heartbeat (`Updates/HEARTBEAT_<timestamp>.md`)

Written by the cloud agent every 5 minutes. Monitored by the local agent. Self-expiring.

**Fields**:

| Field | Type | Notes |
|-------|------|-------|
| `heartbeat_id` | string | `HEARTBEAT_<ISO-timestamp>` |
| `agent_id` | string | `cloud_agent` |
| `created` | ISO-8601Z | Write time |
| `tasks_in_progress` | integer | Count in `In_Progress/cloud/` |
| `last_processed_task_ref` | string or null | Path to last completed task |
| `vault_sync_last_ok` | ISO-8601Z or null | Last confirmed sync cycle |
| `watcher_status` | object | `{ gmail: running|stopped|error, signals: running|stopped|error }` |

**Retention**: Cloud agent deletes heartbeats older than 15 minutes during each write cycle. At steady state, 2–3 heartbeat files exist at any time.

**Monitoring rule** (local `orchestrator.py`):
```
Every 10 minutes:
  Find most-recent HEARTBEAT_*.md in Updates/
  If not found OR file age > 10 minutes:
    Write Needs_Action/ERROR_CLOUD_AGENT_DOWN_<ts>.md
    Write Signals/CLOUD_AGENT_DOWN_<ts>.md (severity: critical)
    Update Dashboard.md: Cloud Agent Status = OFFLINE
```

---

### 3. Agent Update (`Updates/<TYPE>_<timestamp>.md`)

Written by the cloud agent for non-alert status communications. Four sub-types:

| Sub-type | Filename Pattern | Purpose |
|----------|-----------------|---------|
| Heartbeat | `HEARTBEAT_<ts>.md` | Liveness signal (see above) |
| Vault Health | `VAULT_HEALTH_<ts>.md` | Output of `vault-health` skill |
| Briefing Data | `BRIEFING_DATA_<YYYY-MM-DD>.md` | Pre-assembled CEO briefing input |
| Plan Ready | `PLAN_READY_<task_id>_<ts>.md` | Cloud triage complete; local should proceed |

**Vault Health** (`VAULT_HEALTH_<ts>.md`) fields:
- `check_date` (ISO-8601Z)
- `vault_folder_integrity` (`ok` | `missing_folders: [...]`)
- `stale_tasks_detected` (integer)
- `sync_log_last_entry` (ISO-8601Z or null)
- `sync_lag_seconds` (integer — seconds since last sync entry)
- `health_status` (`healthy` | `degraded` | `critical`)
- Body: plain-language summary of findings

**Briefing Data** (`BRIEFING_DATA_<YYYY-MM-DD>.md`) fields:
- `period_start`, `period_end` (YYYY-MM-DD)
- `generated_at` (ISO-8601Z)
- `generated_by`: `cloud_agent`
- `cloud_agent_uptime_pct` (float, 0–100)
- `cloud_agent_downtime_events` (list of timestamp ranges)
- `signal_summary` (list: type, severity, resolved)
- `social_activity` (table: platform, posts, engagement)
- `vault_health_snapshot` (reference to latest VAULT_HEALTH_*.md)

---

### 4. Sync Log Entry (`Sync/sync.log`)

Append-only plain-text file. Written by `audit-sync-log.sh` cron (polls Syncthing REST API every 60 s).

**Line format** (pipe-delimited):
```
<ISO-8601Z> | direction=<local→cloud|cloud→local|both> | files_changed=<N> | bytes=<N> | conflicts=<N> | duration_ms=<N> | status=<ok|conflict|error>
```

**Retention**: No automated deletion. Grows at ~1.5 KB/day (1 line/minute). 90-day retention = ~135 KB. Negligible.

**Monitoring**: The `vault-health` skill reads the last line to determine sync recency. If the last entry is older than 10 minutes, it reports `sync_lag` as degraded.

---

### 5. Compliance Report (`Briefings/COMPLIANCE_REPORT_<YYYY-MM-DD>.md`)

Output of the `constitution-check` skill.

**Fields**:

| Field | Type | Notes |
|-------|------|-------|
| `report_id` | string | `COMPLIANCE_<YYYY-MM-DD>` |
| `check_date` | YYYY-MM-DD | — |
| `generated_by` | string | `constitution-check skill` |
| `overall_status` | enum | `PASS`, `FAIL`, `PARTIAL` |
| `principles_pass` | integer | 0–15 |
| `principles_fail` | integer | 0–15 |
| `principles_manual_review` | integer | 0–15 |

**Body structure**:
```markdown
## Principle Results
| # | Principle | Status | Automated | Finding |
|---|-----------|--------|-----------|---------|
| I | Production First | NEEDS_MANUAL_REVIEW | NO | [checklist item for human] |
| II | Local First | PASS | YES | No secrets found on cloud VM |
...

## Remediation Items
[FAIL items with file path, violation, and fix instruction]

## Manual Review Items
[NEEDS_MANUAL_REVIEW items with human verification checklist]
```

**Lifecycle**:
```
constitution-check skill runs
    ↓
Briefings/COMPLIANCE_REPORT_<date>.md written
    ↓
[if any FAIL] → Needs_Action/COMPLIANCE_FAIL_<date>.md created
[all PASS/MR]  → Dashboard.md compliance section updated
               → Next CEO briefing includes compliance summary
```

---

### 6. Stale Task Recovery Record

Not a new file type — uses existing Cloud Signal schema with `signal_type = task_recovered`.

**Additional context fields in body**:
- `recovered_task_path`: original path in `In_Progress/<agent>/`
- `returned_to_path`: `Needs_Action/<filename>`
- `stale_age_seconds`: how long the task was stranded
- `recovering_agent`: which agent detected and moved it

---

## Extended Audit Log Entry (Platinum additions)

Gold-tier schema extended with two new fields:

```json
{
  "timestamp": "ISO-8601Z",
  "action_type": "email_send | social_post | payment | odoo_sync | file_move | vault_sync | heartbeat | signal | ...",
  "actor": "cloud_agent | local_agent | watcher_gmail_cloud | watcher_signals | ...",
  "target": "<recipient, URL, or resource identifier>",
  "parameters": {},
  "approval_status": "approved | auto | pending | dry_run",
  "approved_by": "human | system",
  "result": "success | failure",
  "error_message": "<string or null>",
  "originating_agent": "cloud | local",
  "executing_agent": "local"
}
```

**Rule**: `executing_agent` is always `"local"` for any MCP action. `originating_agent` is `"cloud"` when the task file was first created by the cloud agent, `"local"` otherwise. This field pair enables attribution queries: "how many tasks originated from cloud but were executed locally?"

---

## State Machine Extensions

### Gold-tier state machine (unchanged)
```
Needs_Action/ → In_Progress/local/ → Plans/ → Pending_Approval/ → Approved/ → Done/
                                                                 → Rejected/
```

### Platinum additions

```
NEW: Needs_Action/ → In_Progress/cloud/ → Plans/ → In_Progress/local/
                                                  → (stale recovery) → Needs_Action/

NEW: In_Progress/cloud/ --[stale timeout]--> Needs_Action/
     ↳ Signals/RECOVERED_TASK_*.md created

NEW: Updates/ → (no state transition; read-only for local agent)

NEW: Signals/ → (no state transition; permanent record)
     ↳ [if requires_human_action=true] → Needs_Action/ERROR_SIGNAL_*.md

EXTENDED: In_Progress/<agent>/ now has two subdirectories
  In_Progress/local/  (was: In_Progress/local_agent/)
  In_Progress/cloud/  (new)
```

### Complete Platinum Vault State Machine

```
     ┌──────────────────────────────────────────────────┐
     │                 NEEDS_ACTION/                     │
     │  (created by: watchers, recovery, signal errors)  │
     └────────────┬──────────────────────────────────────┘
                  │ claim (first-mover wins)
        ┌─────────┴─────────┐
        ▼                   ▼
 IN_PROGRESS/cloud/   IN_PROGRESS/local/
 (cloud agent)        (local agent)
        │                   │
        │ [cloud triage      │ [local planning
        │  complete]         │  complete]
        ▼                   │
 IN_PROGRESS/local/  ←──────┘
 (local proceeds)
        │
        ▼ write
   PLANS/PLAN_*.md ──────────────────────┐
        │                                │
        │ [requires approval]            │ [auto-approved]
        ▼                                ▼
 PENDING_APPROVAL/              execute-plan skill
 APPROVAL_*.md                         │
        │                              ▼
  human moves file              MCP action executed
        ├──→ APPROVED/ ──→ execute-plan skill ──→ MCP
        │
        └──→ REJECTED/ (permanent archive)
                            │
                            ▼
                          DONE/
                  (permanent archive)
                            │
                   Dashboard.md updated
                   Audit log written
                            │
          [stale timeout in IN_PROGRESS/]
                            │
                            ▼
                      NEEDS_ACTION/ ← recovery
                 Signals/RECOVERED_TASK_*.md created
```

---

## Vault Folder Authority Matrix (Platinum)

| Folder | Writer(s) | Reader(s) | Syncthing Mode (local) | Syncthing Mode (cloud) |
|--------|-----------|-----------|----------------------|----------------------|
| `Needs_Action/` | All watchers (both) | All agents (both) | Send and Receive | Send and Receive |
| `In_Progress/local/` | Local agent | Local + cloud monitors | Send and Receive | Send and Receive |
| `In_Progress/cloud/` | Cloud agent | Cloud + local monitors | Send and Receive | Send and Receive |
| `Plans/` | Cloud agent (primary), Local skill | Local agent | Send and Receive | Send and Receive |
| `Updates/` | Cloud agent only | Local agent | Receive Only | Send Only |
| `Signals/` | Either agent | Either agent | Send and Receive | Send and Receive |
| `Pending_Approval/` | Local skills only | Local approval watcher | Send and Receive | Send and Receive |
| `Approved/` | Human (move) | Approval watcher | **Send Only** | **Receive Only** |
| `Rejected/` | Human (move) | Read-only after write | **Send Only** | **Receive Only** |
| `Done/` | Local skills only | CEO briefing, human | **Send Only** | **Receive Only** |
| `Dashboard.md` | Local agent only | All agents (read) | **Send Only** | **Receive Only** |
| `Logs/` | Local MCP calls only | CEO briefing, human | **Send Only** | **Receive Only** |
| `Briefings/` | Local skills only | Human | **Send Only** | **Receive Only** |
| `Bank_Transactions.md` | Finance watcher (local) | CEO briefing | **Send Only** | **Receive Only** |
| `Sync/sync.log` | Audit cron (both) | vault-health skill | Send and Receive | Send and Receive |

> **Bold** = enforced by Syncthing Send-Only / Receive-Only mode. Non-bold = enforced by agent code convention + constitution-check skill audit.
