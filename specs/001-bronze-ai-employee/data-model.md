# Data Model: Bronze Tier Personal AI Employee

**Branch**: `001-bronze-ai-employee` | **Date**: 2026-03-06

All state is stored as Markdown files in `AI_Employee_Vault/`. There is no database.

---

## Entity: Task File

**Location**: `AI_Employee_Vault/Needs_Action/FILE_<timestamp>_<stem>.md`
**Created by**: `FilesystemWatcher`
**Consumed by**: `process-needs-action` skill

### YAML Frontmatter (required fields)

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `type` | string | `file_drop`, `email`, `error`, `unknown` | Source event type |
| `original_name` | string | filename | Original filename as dropped in Inbox |
| `copied_to` | string | filename | Name of the copied file in Needs_Action |
| `size_bytes` | integer | ≥ 0 | File size in bytes |
| `received` | string | ISO 8601Z | UTC timestamp when detected |
| `priority` | string | `urgent`, `high`, `normal`, `low` | Processing priority |
| `status` | string | `pending`, `in_progress`, `done`, `error` | Lifecycle state |

### State Transitions

```
pending → in_progress (when Claude starts processing)
        → done        (after Claude moves file to Done/)
        → error       (on processing failure)
```

### Body Sections (required)

```markdown
## File Dropped for Processing
<summary table: original_name, size, received, copied_to>

## Suggested Actions
- [ ] Review file contents
- [ ] Determine if action is required
- [ ] Move to /Done/ when complete
```

---

## Entity: Plan

**Location**: `AI_Employee_Vault/Plans/PLAN_<timestamp>_<stem>.md`
**Created by**: `process-needs-action` skill
**Consumed by**: Human (via Obsidian) or orchestrator (for HITL)

### YAML Frontmatter

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `type` | string | `plan` | Always `plan` |
| `source_task` | string | filename | The task file this plan was created for |
| `created_at` | string | ISO 8601Z | UTC timestamp |
| `requires_approval` | boolean | `true`, `false` | Whether a human must act before execution |
| `status` | string | `draft`, `approved`, `rejected`, `executed` | Lifecycle state |

### Body Sections

```markdown
## Summary
<1-3 sentence description of what the task is>

## Analysis
<Claude's interpretation of the task type and content>

## Actions
- [ ] <safe action — executed automatically>
- [ ] APPROVE: <sensitive action — blocked until human checks this>

## Notes
<any relevant observations or follow-up reminders>
```

---

## Entity: Dashboard

**Location**: `AI_Employee_Vault/Dashboard.md`
**Single writer**: `process-needs-action` skill (after every run)
**Read by**: Human via Obsidian

### Dynamic Tokens (replaced by skill on each update)

| Token | Content |
|-------|---------|
| `<!-- AI_EMPLOYEE:UPDATED -->` | UTC timestamp of last update |
| `<!-- AI_EMPLOYEE:NEEDS_ACTION_COUNT -->` | Count of `.md` files in Needs_Action |
| `<!-- AI_EMPLOYEE:DONE_TODAY_COUNT -->` | Count of files moved to Done today |
| `<!-- AI_EMPLOYEE:INBOX_COUNT -->` | Count of files in Inbox |
| `<!-- AI_EMPLOYEE:ACTIVE_ITEMS -->` | Bullet list of pending task filenames |
| `<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->` | Last 5 completed items with one-line summary |
| `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` | Items in Pending_Approval/ |

---

## Entity: Log Entry

**Location**: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
**Written by**: `BaseWatcher` and `process-needs-action` skill
**Format**: One JSON object per line (NDJSON / JSON Lines)

### Schema

```json
{
  "timestamp":       "ISO-8601Z",
  "action_type":     "file_drop_detected | process_needs_action | action_file_created | watch_loop_error",
  "actor":           "FilesystemWatcher | claude_code",
  "target":          "<filename or empty string>",
  "parameters":      { "<key>": "<value>" },
  "approval_status": "auto | pending_approval | approved",
  "approved_by":     "system | human | pending_human",
  "result":          "success | failure | deferred"
}
```

**Retention**: 90 days minimum (files older than 90 days may be archived).

---

## Entity: Processed Inbox Registry

**Location**: `scripts/processed_inbox.json`
**Written by**: `FilesystemWatcher` on each new file detection
**Purpose**: Idempotency — prevents duplicate task creation on watcher restart

### Schema

```json
{
  "processed": [
    "test_invoice.txt",
    "contract_v2.pdf"
  ]
}
```

---

## Folder State Machine

```
AI_Employee_Vault/
│
├── Inbox/            ← Human drops files here (entry point)
│       │
│       ▼  (FilesystemWatcher detects, copies, records in processed_inbox.json)
│
├── Needs_Action/     ← Task .md files awaiting Claude (status: pending)
│       │
│       ▼  (process-needs-action skill reads, creates Plan, updates status)
│
├── Plans/            ← Plan .md files created by Claude
│       │
│       │  (for safe actions: Claude acts directly)
│       │  (for sensitive actions: requires human to check [ ] APPROVE)
│       ▼
│
├── Done/             ← Completed task files (prefixed DONE_, immutable)
│
└── Logs/             ← Audit trail (NDJSON, one file per day)
```
