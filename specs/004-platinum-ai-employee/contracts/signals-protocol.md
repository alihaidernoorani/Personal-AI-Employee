# Contract: Signals Protocol

**Feature**: `004-platinum-ai-employee`
**Version**: 1.0.0
**Date**: 2026-06-27

---

## Purpose

The Signals protocol defines a bidirectional alert channel between the cloud and local agents. Either agent may write to `Signals/`; both agents monitor it via `signals_watcher.py`. Signals are permanent records — never deleted.

---

## Signal File Format

**Location**: `AI_Employee_Vault/Signals/SIGNAL_<type>_<ISO-8601Z>.md`

```yaml
---
signal_id: SIGNAL_cloud_down_2026-06-27T14:30:00Z
signal_type: cloud_down
originating_agent: local
created: 2026-06-27T14:30:00Z
severity: critical
requires_human_action: true
linked_ref: null
---

## Signal Message
Cloud agent heartbeat has not been received for 10 minutes. Last heartbeat: 2026-06-27T14:20:00Z.

## Recommended Action
Check cloud VM health. SSH to cloud VM and verify cloud_orchestrator.py is running.
If VM is down, reprovision using scripts/provision-cloud.sh.
```

---

## Signal Types

| Signal Type | Written By | Severity | Human Required | Description |
|---|---|---|---|---|
| `cloud_down` | local | critical | yes | Cloud agent heartbeat absent >10 min |
| `task_recovered` | either | info | no | Stale task returned to Needs_Action/ |
| `sync_conflict` | either (audit script) | warning | yes | `.sync-conflict-*` file detected in vault |
| `sync_stalled` | cloud | warning | no | sync.log has no entry for >10 min |
| `stale_draft` | cloud | info | no | Approval file in Pending_Approval/ age >48 hr |
| `disk_alert` | cloud | warning | yes | Cloud VM disk >80% full |
| `clock_skew` | either | warning | no | Clock skew >1s between machines detected |
| `vault_missing_file` | cloud | warning | no | Expected file (Company_Handbook.md) absent from cloud vault |
| `single_writer_violation` | cloud | critical | yes | Cloud agent attempted write to prohibited path |
| `shutdown_request` | local | info | no | Local agent requests graceful cloud shutdown |
| `plan_ready` | cloud | info | no | Cloud triage complete; plan waiting for local agent |
| `compliance_fail` | local | warning | yes | constitution-check found FAIL principle |

---

## Signal Routing

`signals_watcher.py` on each machine polls `Signals/` every 60 seconds. For each new signal file:

1. **Mark as processed** in `scripts/processed_signals.json`
2. **Route by type**:

| Signal Type | Cloud VM Response | Local Machine Response |
|---|---|---|
| `cloud_down` | — (cloud is down) | Create `Needs_Action/ERROR_*.md` + update Dashboard.md |
| `task_recovered` | Log only | Log only |
| `sync_conflict` | Log only | Create `Needs_Action/SYNC_CONFLICT_*.md` for human review |
| `sync_stalled` | Investigate sync daemon | Log + update Dashboard.md sync status |
| `stale_draft` | Log only | Highlight in Dashboard.md Pending_Approval section |
| `disk_alert` | Clean up old files | Create `Needs_Action/ERROR_DISK_*.md` |
| `clock_skew` | Trigger NTP sync | Log warning |
| `vault_missing_file` | Pause dependent tasks | Log + alert |
| `single_writer_violation` | Log + do NOT retry the write | Create `Needs_Action/ERROR_SINGLE_WRITER_*.md` |
| `shutdown_request` | Graceful shutdown sequence | — |
| `plan_ready` | — | Trigger process-needs-action skill for the linked task |
| `compliance_fail` | Log only | Create `Needs_Action/COMPLIANCE_FAIL_*.md` |

---

## Graceful Shutdown Sequence

Triggered by `Signals/SIGNAL_shutdown_request_<ts>.md` (written by local agent):

1. Cloud orchestrator detects `shutdown_request` via signals_watcher
2. Stops accepting new tasks from `Needs_Action/` (stops claiming)
3. Waits for current in-progress tasks to complete (or times out after 5 minutes)
4. Moves any remaining `In_Progress/cloud/` tasks back to `Needs_Action/`
5. Writes final heartbeat with `watcher_status: shutting_down`
6. Terminates all cloud watcher processes
7. Exits `cloud_orchestrator.py`

---

## Idempotency

`signals_watcher.py` tracks processed signal IDs in `scripts/processed_signals.json`. On restart, it re-reads the signal files but skips already-processed IDs. A signal is only actioned once per machine.

---

## Signal Retention

Signals are permanent records in `Signals/`. They are never deleted by any agent or process. The `Sync/sync.log` cron audit script counts signals per day for the CEO briefing summary.

Signals older than 90 days are eligible for archival (same retention policy as `Logs/`) but this is a manual operation only.
