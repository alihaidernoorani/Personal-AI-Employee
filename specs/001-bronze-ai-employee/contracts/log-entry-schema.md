# Contract: Audit Log Entry Schema

**Version**: 1.0 | **Date**: 2026-03-06

Every action taken by the system MUST produce one NDJSON log line in
`AI_Employee_Vault/Logs/YYYY-MM-DD.json`.

---

## File Naming

```
Logs/YYYY-MM-DD.json    # One file per UTC calendar day
```

Files older than 90 days may be archived but MUST NOT be deleted.

---

## Entry Schema

```json
{
  "timestamp":       "<ISO-8601Z>",
  "action_type":     "<one of the values below>",
  "actor":           "<FilesystemWatcher | claude_code>",
  "target":          "<filename, email address, or empty string>",
  "parameters":      { "<key>": "<value>" },
  "approval_status": "<auto | pending_approval | approved>",
  "approved_by":     "<system | human | pending_human>",
  "result":          "<success | failure | deferred>"
}
```

---

## `action_type` Values (Bronze tier)

| Value | Actor | Description |
|-------|-------|-------------|
| `file_drop_detected` | FilesystemWatcher | New file found in Inbox/ |
| `action_file_created` | FilesystemWatcher | Task .md created in Needs_Action/ |
| `watch_loop_error` | FilesystemWatcher | Exception in watcher loop |
| `process_needs_action` | claude_code | Skill processed one task file |
| `plan_created` | claude_code | Plan.md written to Plans/ |
| `task_completed` | claude_code | Task file moved to Done/ |
| `dashboard_updated` | claude_code | Dashboard.md rewritten |

---

## Example Entries

```json
{"timestamp":"2026-03-06T12:00:44Z","action_type":"file_drop_detected","actor":"FilesystemWatcher","target":"invoice.txt","parameters":{"dest":"FILE_20260306T120044Z_invoice.txt.md"},"approval_status":"auto","approved_by":"system","result":"success"}
{"timestamp":"2026-03-06T12:01:00Z","action_type":"process_needs_action","actor":"claude_code","target":"FILE_20260306T120044Z_invoice.txt.md","parameters":{"type":"file_drop","priority":"normal"},"approval_status":"auto","approved_by":"system","result":"success"}
```
