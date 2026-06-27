# Contract: Cloud Agent Interface

**Feature**: `004-platinum-ai-employee`
**Version**: 1.0.0
**Date**: 2026-06-27

---

## Purpose

This contract defines the complete boundary between the cloud agent and the vault. It specifies exactly what the cloud agent may write, what it may never write, and how local-agent code validates that boundary.

---

## What the Cloud Agent MAY Write

| Path Pattern | Action | Condition |
|---|---|---|
| `Needs_Action/EMAIL_<id>.md` | Create | New email detected by cloud Gmail watcher |
| `Needs_Action/SIGNAL_ERROR_<ts>.md` | Create | Cloud agent encounters a processing error |
| `In_Progress/cloud/<filename>` | Create (move from Needs_Action/) | Claiming a task |
| `In_Progress/local/<filename>` | Create (move from In_Progress/cloud/) | Handing off completed triage to local agent |
| `Plans/PLAN_<ts>.md` | Create | Cloud triage drafting a response plan |
| `Updates/HEARTBEAT_<ts>.md` | Create | Liveness signal every 5 minutes |
| `Updates/VAULT_HEALTH_<ts>.md` | Create | Output of vault-health skill |
| `Updates/BRIEFING_DATA_<date>.md` | Create | Output of cloud-briefing-prep skill |
| `Signals/SIGNAL_<type>_<ts>.md` | Create | Alert conditions detected by cloud agent |
| `Sync/sync.log` | Append | Audit-sync-log.sh on cloud VM |

---

## What the Cloud Agent MUST NEVER Write

| Path | Reason | Enforcement |
|---|---|---|
| `Dashboard.md` | Single Writer Rule (Principle VII) | Syncthing Send-Only on local; code guard in cloud agent |
| `Done/` | Local authority — task completion is local-only | Syncthing Receive-Only on cloud |
| `Approved/` | Human-move only | Syncthing Receive-Only on cloud |
| `Rejected/` | Human-move only; permanent archive | Syncthing Receive-Only on cloud |
| `Logs/` | All MCP audit records are local-only | Syncthing Receive-Only on cloud |
| `Briefings/` | CEO briefing assembled locally | Syncthing Receive-Only on cloud |
| `Bank_Transactions.md` | Finance watcher is local-only | Syncthing Receive-Only on cloud |
| `Company_Handbook.md` | Owner maintains locally | Syncthing Receive-Only on cloud (read access for cloud agent) |
| `Business_Goals.md` | Owner maintains locally | Syncthing Receive-Only on cloud (read access for cloud agent) |
| Any MCP tool call | Cloud has no MCP servers | No `.mcp.json` on cloud VM |

---

## Cloud Agent Code Guard

Every cloud agent skill and watcher MUST include this guard before any vault write:

```python
PROHIBITED_CLOUD_WRITE_PATHS = [
    "Dashboard.md",
    "Done/",
    "Approved/",
    "Rejected/",
    "Logs/",
    "Briefings/",
    "Bank_Transactions.md",
]

def safe_vault_write(path: Path, content: str) -> None:
    for prohibited in PROHIBITED_CLOUD_WRITE_PATHS:
        if str(path).endswith(prohibited) or prohibited in str(path):
            signal_path = VAULT_PATH / "Signals" / f"SINGLE_WRITER_VIOLATION_{datetime.utcnow().isoformat()}Z.md"
            signal_path.write_text(f"---\nsignal_type: single_writer_violation\n...\nAttempted write to {path}")
            raise PermissionError(f"Cloud agent prohibited from writing to {path}")
    path.write_text(content)
```

The `constitution-check` skill verifies this guard is present in all cloud-side code (Principle VII check).

---

## Cloud Agent Activation

The cloud agent is activated by the environment variable:
```
AGENT_ROLE=cloud
```

When `AGENT_ROLE=cloud`:
- `cloud_orchestrator.py` starts (not `orchestrator.py`)
- `.mcp.json` is absent — no MCP tool calls possible
- `PROHIBITED_CLOUD_WRITE_PATHS` guard is enforced

When `AGENT_ROLE=local` (default):
- `orchestrator.py` starts
- All MCP servers available
- Cloud write guard inactive (local agent has full write access)

---

## Validation (constitution-check Principle III check)

Automated checks the `constitution-check` skill runs against the cloud VM:

1. **No `.mcp.json` present on cloud VM**: `test -f <vault_root>/../.mcp.json` → FAIL if exists
2. **No MCP server processes running**: `pgrep -f mcp-servers` → FAIL if any match
3. **`AGENT_ROLE=cloud` set**: inspect `.env.cloud` (cloud-only env file) → FAIL if `AGENT_ROLE` not set to `cloud`
4. **Code guard present**: `grep -r "PROHIBITED_CLOUD_WRITE_PATHS" watchers/ .claude/skills/` → FAIL if not found
5. **No execution credentials**: scan cloud VM home directory for `.env`, `*.token`, `*.json` credential patterns → FAIL if any found
