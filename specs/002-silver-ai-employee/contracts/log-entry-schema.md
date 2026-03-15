# Contract: Log Entry Schema (Silver Tier)

Extends Bronze Tier log-entry-schema with new action types.

**File**: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
**Format**: NDJSON — one JSON object per line, newline-delimited

---

## Schema

```json
{
  "timestamp": "2026-03-13T09:05:00Z",
  "action_type": "send_email | linkedin_post | draft_reply | search_inbox | process_needs_action | file_drop_detected | gmail_detected | whatsapp_detected | approval_detected",
  "actor": "claude_code | scheduler | gmail_watcher | whatsapp_watcher | approval_watcher | filesystem_watcher",
  "target": "<filename | email address | 'linkedin' | 'system'>",
  "parameters": {},
  "approval_status": "approved | auto | dry_run | pending | rejected",
  "approved_by": "human | system",
  "result": "success | failure | deferred | dry_run"
}
```

---

## Examples

**Email detected by watcher**:
```json
{"timestamp":"2026-03-13T09:00:00Z","action_type":"gmail_detected","actor":"gmail_watcher","target":"EMAIL_20260313T090000Z_invoice.md","parameters":{"uid":"12345","sender":"alice@example.com"},"approval_status":"auto","approved_by":"system","result":"success"}
```

**Email reply sent via MCP**:
```json
{"timestamp":"2026-03-13T09:15:00Z","action_type":"send_email","actor":"claude_code","target":"alice@example.com","parameters":{"subject":"Re: Invoice #1001","reply_to_uid":"12345"},"approval_status":"approved","approved_by":"human","result":"success"}
```

**LinkedIn post (dry run)**:
```json
{"timestamp":"2026-03-13T08:05:00Z","action_type":"linkedin_post","actor":"claude_code","target":"linkedin","parameters":{"content_length":247},"approval_status":"dry_run","approved_by":"system","result":"dry_run"}
```

**Scheduler trigger**:
```json
{"timestamp":"2026-03-13T09:00:00Z","action_type":"process_needs_action","actor":"scheduler","target":"Needs_Action/","parameters":{"tasks_found":3},"approval_status":"auto","approved_by":"system","result":"success"}
```
