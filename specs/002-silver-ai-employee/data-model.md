# Data Model: Silver Tier Functional Assistant

**Feature**: 002-silver-ai-employee | **Date**: 2026-03-13

---

## Entity Map

```
GmailMessage ──creates──► TaskFile ──creates──► PlanFile ──creates──► ApprovalRequest
WaMessage ────creates──►  (Needs_Action/)       (Plans/)               (Pending_Approval/)
FileDropEvent ──────────►                                                    │
                                                                     human moves to
                                                                    Approved/ or Rejected/
                                                                             │
                                                                      ActionTrigger
                                                                    (Needs_Action/)
                                                                             │
                                                                       MCP call
                                                                             │
                                                                        LogEntry
                                                                       (Logs/)
```

---

## Entities

### 1. TaskFile

Files in `Needs_Action/`. Subtypes: `email`, `whatsapp`, `file_drop`, `action_trigger`, `error`.

**Filename patterns**:
- `EMAIL_<YYYYMMDDTHHMMSSz>_<subject-slug>.md`
- `WA_<YYYYMMDDTHHMMSSz>_<sender-slug>.md`
- `FILE_<YYYYMMDDTHHMMSSz>_<name-slug>.md`
- `ACTION_<YYYYMMDDTHHMMSSz>_<slug>.md`
- `ERROR_<YYYYMMDDTHHMMSSz>_<slug>.md`

**Common frontmatter fields**:
| Field | Type | Values |
|-------|------|--------|
| `type` | string | `email \| whatsapp \| file_drop \| action_trigger \| error` |
| `source` | string | `gmail \| whatsapp \| filesystem \| system` |
| `received` | ISO-8601 UTC | `2026-03-13T09:00:00Z` |
| `priority` | string | `urgent \| high \| normal \| low` |
| `status` | string | `pending \| processing \| done` |

**Email-specific**:
| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | `alice@example.com` |
| `subject` | string | Email subject line |
| `body_snippet` | string | First 300 chars of body |
| `imap_uid` | string | IMAP UID for reply threading |

**WhatsApp-specific**:
| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | Contact name or phone number |
| `message_text` | string | Full message text |
| `message_hash` | string | SHA256 for idempotency |

**Action trigger-specific**:
| Field | Type | Description |
|-------|------|-------------|
| `action_type` | string | `send_email \| linkedin_post` |
| `approval_file` | string | Filename of the originating APPROVAL_*.md |
| `action_params` | object | Serialised action parameters (JSON) |

---

### 2. PlanFile

Files in `Plans/`. One plan per processed task.

**Filename**: `PLAN_<YYYYMMDDTHHMMSSz>_<source-slug>.md`

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `plan` |
| `source_task` | string | Filename of the originating task |
| `created_at` | ISO-8601 UTC | Plan creation time |
| `requires_approval` | boolean | `true` if any outbound action needed |
| `status` | string | `draft \| awaiting_approval \| approved \| executed \| rejected` |

**Body sections**: Summary, Analysis, Actions (`[ ]` safe / marked for approval), Notes

---

### 3. ApprovalRequest

Files in `Pending_Approval/`. Created by skills for sensitive actions.

**Filename**: `APPROVAL_<YYYYMMDDTHHMMSSz>_<action-type>_<slug>.md`

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `approval_request` |
| `action` | string | `send_email \| linkedin_post` |
| `plan_file` | string | Filename of the originating plan |
| `reason` | string | Why this action is needed |
| `parameters` | object | `{to, subject, body}` or `{post_content}` |
| `timestamp` | ISO-8601 UTC | When created |
| `status` | string | `pending \| approved \| rejected` |

**Transitions**:
- Created in `Pending_Approval/` with `status: pending`
- Human moves to `Approved/` → `status: approved`
- Human moves to `Rejected/` → `status: rejected` (logged, no action taken)

---

### 4. ProcessedRegistry

JSON files in `scripts/`. Prevent duplicate processing on watcher restart.

| File | Key | Value |
|------|-----|-------|
| `processed_inbox.json` | filename | `{"processed": ["file.txt", ...]}` |
| `processed_gmail.json` | IMAP UID | `{"processed": {"uid": "timestamp"}}` |
| `processed_whatsapp.json` | message hash | `{"processed": {"hash": "timestamp"}}` |
| `processed_approvals.json` | filename | `{"processed": ["APPROVAL_*.md", ...]}` |

---

### 5. LogEntry

NDJSON lines appended to `Logs/YYYY-MM-DD.json`. One line per action.

```json
{
  "timestamp": "2026-03-13T09:05:00Z",
  "action_type": "send_email | linkedin_post | process_needs_action | file_drop_detected",
  "actor": "claude_code | scheduler | gmail_watcher | whatsapp_watcher",
  "target": "<filename or email address or linkedin>",
  "parameters": {},
  "approval_status": "approved | auto | dry_run | pending",
  "approved_by": "human | system",
  "result": "success | failure | deferred | dry_run"
}
```

---

## Vault Folder State Machine

```
Inbox/
  └──(FilesystemWatcher)──► Needs_Action/
                                 │
Gmail INBOX                      │  (GmailWatcher)
  └──(GmailWatcher)──────────────┤
                                 │
WhatsApp Web                     │  (WhatsAppWatcher)
  └──(WhatsAppWatcher)───────────┘
                                 │
                         (Reasoning skills)
                                 │
                                 ▼
                            Plans/
                                 │
                         (if approval needed)
                                 │
                                 ▼
                       Pending_Approval/
                          │          │
                    (human)        (human)
                          │          │
                       Approved/   Rejected/
                          │
                   (ApprovalWatcher)
                          │
                   Needs_Action/ACTION_*.md
                          │
                   (execute-plan skill → MCP)
                          │
                          ▼
                        Done/
                          +
                        Logs/
```

**Invariants**:
- Files move forward only (no backward moves except explicit human override)
- `Done/` and `Rejected/` are never emptied (audit trail)
- Every action produces a `Logs/` entry
