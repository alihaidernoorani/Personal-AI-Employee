# Contract: Vault Sync Protocol

**Feature**: `004-platinum-ai-employee`
**Version**: 1.0.0
**Date**: 2026-06-27

---

## Overview

Syncthing is the vault sync mechanism. It runs as a headless daemon on both the local machine and the cloud VM, synchronising the Obsidian vault directory bidirectionally. Folder-level Send-Only / Receive-Only mode assignments eliminate conflict disputes on authoritative folders by architectural policy.

---

## Latency SLA

| Condition | Maximum propagation time |
|-----------|------------------------|
| Normal operation (LAN / low-latency WAN) | ≤ 10 seconds |
| High-latency WAN (>100ms RTT) | ≤ 30 seconds |
| Worst-case (high load, large batch) | ≤ 60 seconds |
| During network partition | Changes buffered; applied on reconnect; no data lost |

---

## Folder Authority Configuration

| Vault Folder | Local Syncthing Mode | Cloud Syncthing Mode |
|---|---|---|
| `Dashboard.md` (root file) | **Send Only** | **Receive Only** |
| `Done/` | **Send Only** | **Receive Only** |
| `Approved/` | **Send Only** | **Receive Only** |
| `Rejected/` | **Receive Only** — human moves only; cloud cannot create | **Receive Only** |
| `Logs/` | **Send Only** | **Receive Only** |
| `Briefings/` | **Send Only** | **Receive Only** |
| `Bank_Transactions.md` | **Send Only** | **Receive Only** |
| `Updates/` | **Receive Only** | **Send Only** |
| `In_Progress/cloud/` | **Receive Only** (cloud moves; local reads) | **Send Only** |
| `Needs_Action/` | Send and Receive | Send and Receive |
| `In_Progress/local/` | Send and Receive | Send and Receive |
| `Plans/` | Send and Receive | Send and Receive |
| `Signals/` | Send and Receive | Send and Receive |
| `Pending_Approval/` | Send and Receive | Send and Receive |
| `Sync/` | Send and Receive | Send and Receive |
| `Company_Handbook.md` | **Send Only** | **Receive Only** |
| `Business_Goals.md` | **Send Only** | **Receive Only** |

> Syncthing enforces Send-Only / Receive-Only at the folder level. The cloud VM physically cannot modify Receive-Only folders even if a bug in cloud agent code attempts to write there — Syncthing rejects or reverts the change.

---

## Exclusion List (`.stignore`)

The following patterns are excluded from sync. This file lives at the vault root on both machines and is itself synced (Send and Receive) so both machines share the same exclusion rules.

```
// Secrets — never leave local machine
.env
.env.*
.env.local
.env.production

// Session data
*.session
*_session/
cookies/
WHATSAPP_SESSION/
playwright-session/

// Watcher idempotency state (each machine maintains its own)
scripts/processed_*.json
scripts/email_outbox_queue.json

// Build artifacts
**/__pycache__/
**/*.pyc
**/*.pyo
.venv/
node_modules/

// Sync lock (managed by Syncthing itself)
Sync/sync.lock

// Git metadata
.git/
```

---

## Conflict Resolution

### Authoritative-folder conflicts (handled by Syncthing policy)
Syncthing Send-Only mode means the remote machine cannot modify locally-authoritative files. If the cloud VM somehow writes to `Dashboard.md`, Syncthing reverts the change on the next sync cycle and logs it as a conflict. The local copy always wins.

### Shared-folder conflicts
For folders where both agents can write (`Needs_Action/`, `Plans/`, `Signals/`, `Pending_Approval/`), Syncthing conflict files are named:
```
<filename>.sync-conflict-<YYYYMMDD>-<HHMMSS>-<device-id>.<ext>
```
The `audit-sync-log.sh` cron detects `.sync-conflict-*` files and writes `Signals/SYNC_CONFLICT_<ts>.md` for human review.

**Resolution rule for shared-folder conflicts**: Both versions are preserved. The file without the `.sync-conflict-` suffix is the version that was written first. Human must review and decide which version to keep.

---

## Audit Trail

**Mechanism**: `scripts/sync/audit-sync-log.sh` cron runs every 60 seconds on both machines:
1. Poll Syncthing REST API: `GET http://127.0.0.1:8384/rest/events?since=<last_id>&types=LocalChangeDetected,RemoteChangeDetected`
2. For each event, append one line to `AI_Employee_Vault/Sync/sync.log`:
   ```
   <ISO-8601Z> | direction=<local→cloud|cloud→local> | files_changed=<N> | bytes=<N> | conflicts=<N> | duration_ms=<N> | status=<ok|conflict|error>
   ```
3. Update `last_id` in `scripts/sync/last_event_id` to avoid re-processing events

**API authentication**: Syncthing REST API key stored in `SYNCTHING_API_KEY` environment variable (local only; not synced to cloud). Cloud uses its own API key.

---

## Setup Sequence (`scripts/sync/setup-syncthing.sh`)

1. Verify Syncthing is installed and daemonised on both machines
2. Get local device ID: `curl http://127.0.0.1:8384/rest/system/status | jq .myID`
3. Get cloud device ID via SSH: `ssh <cloud> 'curl http://127.0.0.1:8384/rest/system/status | jq .myID'`
4. Add cloud device to local Syncthing via REST API
5. Add local device to cloud Syncthing via REST API
6. Configure each vault subfolder with its correct authority mode on each machine
7. Deploy `.stignore` to vault root on both machines
8. Trigger initial full sync (local → cloud direction)
9. Verify sync by writing test file, confirming propagation within SLA, deleting test file

---

## Health Monitoring

| Condition | Detection | Response |
|-----------|-----------|---------|
| `sync.log` has no entry for >10 min | `vault-health` skill checks last line timestamp | Write `Signals/SYNC_STALLED_<ts>.md` |
| `.sync-conflict-*` files detected | `audit-sync-log.sh` scans vault | Write `Signals/SYNC_CONFLICT_<ts>.md` |
| Syncthing daemon not responding | REST API health check times out | Write `Needs_Action/ERROR_SYNC_DOWN_<ts>.md` |
| Cloud VM disk >80% | Cloud orchestrator checks `df` | Write `Signals/DISK_ALERT_<ts>.md` |
