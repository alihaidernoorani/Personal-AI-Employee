# Vault Sync Configuration

**Maintained by**: Owner (manual edits only — do not auto-generate)
**Last updated**: 2026-06-27

---

## Sync Engine

**Tool**: [Syncthing](https://syncthing.net/) — P2P daemon, no central server.
**Interval**: File changes detected within ~30 seconds via inotify (Linux) / polling (Windows NTFS).
**Transport**: Syncthing relay or direct TCP over port 22000 (SSH tunnel for cloud VM).

---

## Excluded Paths

The following paths are excluded on **both** machines via `scripts/sync/.stignore`:

| Pattern | Reason |
|---------|--------|
| `.env`, `.env.*` | All credentials — must never reach cloud VM |
| `*.session`, `*_session/` | Browser/Playwright sessions — local machine only |
| `cookies/` | Cookie jars — local machine only |
| `scripts/processed_*.json` | Watcher idempotency state — machine-local |
| `scripts/email_outbox_queue.json` | Email queue — local machine only |
| `Sync/sync.lock` | Coordination lock — machine-local |
| `__pycache__/`, `*.pyc` | Python artifacts — rebuilt on each machine |
| `.venv/`, `venv/` | Python virtual environments |
| `.git/` | Git repository metadata |
| `.DS_Store`, `Thumbs.db` | OS artifacts |

---

## Conflict Resolution

Syncthing folder authority modes eliminate conflicts by policy:

| Vault Folder | Local Machine | Cloud VM |
|---|---|---|
| `Dashboard.md`, `Done/`, `Approved/`, `Rejected/` | **Send Only** | **Receive Only** |
| `Updates/`, `Signals/`, `In_Progress/cloud/` | **Receive Only** | **Send Only** |
| `Needs_Action/`, `Plans/`, `In_Progress/local/`, all others | **Send and Receive** | **Send and Receive** |

**Send Only**: machine can write; remote cannot modify these files (conflicts prevented by design).
**Receive Only**: machine cannot modify; accepts writes from the authoritative machine.
**Send and Receive**: both machines can write; Syncthing uses vector clocks.

For shared folders: sync conflicts are saved as `.sync-conflict-*` files and flagged
in `Signals/SYNC_CONFLICT_*.md` by the audit script.

---

## Retry Policy

| Scenario | Behaviour |
|---|---|
| Network partition < 10 min | Changes buffered locally; propagate on reconnect |
| Network partition 10–30 min | All changes queued; Syncthing deduplicates on reconnect |
| Network partition > 30 min | All changes queued; verify via `Sync/sync.log` on reconnect |
| Sync conflict on shared folder | `.sync-conflict-*` file preserved; `SYNC_CONFLICT_*.md` written to `Signals/` |
| Sync stall > 10 min | `SYNC_STALLED_*.md` written to `Signals/`; investigate Syncthing daemon |

Syncthing retry: built-in reconnect with exponential backoff (managed by daemon).

---

## Sync Log Format

Each line in `AI_Employee_Vault/Sync/sync.log`:

```
timestamp|direction|file_path|size_bytes|machine_id|sync_lag_seconds
```

| Field | Description |
|-------|-------------|
| `timestamp` | ISO-8601 UTC of sync event |
| `direction` | `local->remote` or `remote->local` |
| `file_path` | Vault-relative file path |
| `size_bytes` | File size at time of sync |
| `machine_id` | Hostname of reporting machine |
| `sync_lag_seconds` | Seconds between write and detection on remote |

Written by `scripts/sync/audit-sync-log.sh` (polls Syncthing REST API every 60s).

---

## Health Monitoring

- Local orchestrator checks `Sync/sync.log` recency every 10 minutes.
- If last entry > 10 minutes old: `Signals/SYNC_STALLED_*.md` written.
- Cloud agent checks sync health via `watchers/cloud_boundary.check_sync_health()`.
- On cloud: `cloud_orchestrator.py` also checks sync stall on each health cycle.
