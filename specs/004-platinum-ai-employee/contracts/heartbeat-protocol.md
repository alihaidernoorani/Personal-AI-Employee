# Contract: Heartbeat Protocol

**Feature**: `004-platinum-ai-employee`
**Version**: 1.0.0
**Date**: 2026-06-27

---

## Purpose

The heartbeat protocol provides liveness signalling from the cloud agent to the local agent. The local agent uses heartbeat recency to determine cloud agent health and update `Dashboard.md` accordingly.

---

## Heartbeat Production (Cloud Agent)

**Producer**: `watchers/heartbeat_writer.py` on the cloud VM
**Frequency**: Every 300 seconds (5 minutes)
**Location**: `AI_Employee_Vault/Updates/HEARTBEAT_<ISO-8601Z>.md`

**File content** (YAML frontmatter + plain body):

```yaml
---
heartbeat_id: HEARTBEAT_2026-06-27T14:30:00Z
agent_id: cloud_agent
created: 2026-06-27T14:30:00Z
tasks_in_progress: 2
last_processed_task_ref: In_Progress/local/EMAIL_abc123_2026-06-27T14.md
vault_sync_last_ok: 2026-06-27T14:29:45Z
watcher_status:
  gmail: running
  signals: running
  stale_monitor: running
---

Cloud agent healthy. 2 tasks in progress. Last sync 15 seconds ago.
```

**Self-cleanup**: During each write, `heartbeat_writer.py` deletes heartbeat files older than 15 minutes. Maximum 3 heartbeat files exist at any time.

---

## Heartbeat Consumption (Local Agent)

**Consumer**: `orchestrator.py` heartbeat monitor, runs every 10 minutes
**Detection logic**:

```python
def check_cloud_agent_health(vault_path: Path) -> str:
    heartbeat_files = sorted(
        (vault_path / "Updates").glob("HEARTBEAT_*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    if not heartbeat_files:
        return "OFFLINE"
    newest_mtime = heartbeat_files[0].stat().st_mtime
    age_seconds = time.time() - newest_mtime
    if age_seconds > 600:   # 10 minutes
        return "OFFLINE"
    if age_seconds > 360:   # 6 minutes (1 missed beat + buffer)
        return "DEGRADED"
    return "ONLINE"
```

**Response to status changes**:

| Status | Response |
|--------|---------|
| `ONLINE` | Update `Dashboard.md` Cloud Agent Status = ONLINE |
| `DEGRADED` | Update `Dashboard.md` Cloud Agent Status = DEGRADED; no alert yet |
| `OFFLINE` | Update `Dashboard.md` Cloud Agent Status = OFFLINE; write `Needs_Action/ERROR_CLOUD_AGENT_DOWN_<ts>.md`; write `Signals/CLOUD_AGENT_DOWN_<ts>.md` (severity: critical) |

---

## Dashboard.md Cloud Agent Section

The local agent maintains this section in `Dashboard.md` (single-writer rule):

```markdown
## Cloud Agent Status
- **Status**: ONLINE / DEGRADED / OFFLINE
- **Last Heartbeat**: 2026-06-27T14:30:00Z (2 minutes ago)
- **Tasks in Progress (Cloud)**: 2
- **Vault Sync Last OK**: 2026-06-27T14:29:45Z
- **Watcher Status**: Gmail: running | Signals: running | Stale Monitor: running

### Recent Updates
- 2026-06-27T14:30:00Z — Heartbeat received; 2 tasks in progress
- 2026-06-27T14:25:00Z — Plan drafted for EMAIL_abc123
- 2026-06-27T14:20:00Z — Vault health check passed
```

---

## Failure Scenarios

| Scenario | Heartbeat age | Status | Action taken |
|----------|--------------|--------|-------------|
| Normal operation | < 6 min | ONLINE | None |
| Cloud agent slow/overloaded | 6–10 min | DEGRADED | Dashboard updated; no alert |
| Cloud agent crashed | > 10 min | OFFLINE | ERROR file + Signal created |
| Cloud VM network partition | > 10 min | OFFLINE | Same as crashed; but stale tasks may accumulate |
| Cloud VM powered off | > 10 min | OFFLINE | Same as crashed; local agent continues solo |

**Note**: OFFLINE does not halt the local agent. All local operations continue normally. Cloud triage is temporarily unavailable; local Gmail watcher activates as fallback (it runs continuously, but at lower priority than cloud when both are active).
