---
name: email-queue-manager
description: |
  Manages the email outbox queue in scripts/email_outbox_queue.json.
  Supports three modes: status (view queue contents), flush (send all queued
  emails via email-mcp flush_queue tool), and discard (remove specific items).
  Used when Email MCP was temporarily unavailable and emails were queued locally,
  or to inspect/clear the queue on demand.
  Respects DRY_RUN=true — flush in dry-run mode logs intended sends without
  connecting to SMTP.
  Use this skill to manage queued emails, check queue status, or recover from
  Email MCP outages.
  Triggered by: "run email-queue-manager skill", "check email queue", "flush email queue",
  "show queued emails", "clear email queue", "send queued emails".
---

# Email Queue Manager

Inspect, flush, or clean the email outbox queue.

---

## Step 1 — Parse the Operation

Determine which operation the user wants:

| User says | Operation |
|-----------|-----------|
| "check", "show", "status", "what's in the queue" | `status` |
| "flush", "send", "deliver" | `flush` |
| "discard", "clear", "remove", "delete" | `discard` |

Default to `status` if no clear signal.

---

## Step 2 — Read the Queue

Read `scripts/email_outbox_queue.json`.

If the file does not exist or is empty (`[]`):
```
Email queue is empty. Nothing to do.
<promise>TASK_COMPLETE</promise>
```

If the file contains entries, parse each entry. Each queue entry has:
- `to` — recipient email address
- `subject` — email subject
- `body` — email body text
- `queued_at` — ISO-8601 timestamp when it was queued
- `reply_to_message_id` — optional IMAP UID for threading

---

## Step 3 — Execute the Operation

### Operation: status

Display the queue contents without taking any action:

```
Email Queue Status
------------------
Total queued: N emails

Queue contents:
  #1  To: <to>
      Subject: <subject>
      Queued: <queued_at> (<age>)

  #2  To: <to>
      Subject: <subject>
      Queued: <queued_at> (<age>)
  ...

No action taken. To send: "flush email queue"
To discard all: "discard email queue"
```

Log a `queue_status_check` audit entry and output completion signal.

### Operation: flush

Send all queued emails in order via the Email MCP.

**Step 3a: Check DRY_RUN**

If `DRY_RUN=true` (default): call `email-mcp flush_queue` which will log
intended sends without connecting to SMTP. Note: `flush_queue` in dry-run mode
returns `{sent: 0, dry_run: true, would_have_sent: N}`.

If `DRY_RUN=false`: call `email-mcp flush_queue` which sends real emails.

**Step 3b: Call flush_queue**

```
mcp__email-mcp__flush_queue
  (no parameters required — flushes the full queue)
```

**Step 3c: Handle the result**

On success response `{sent: N, failed: M}`:
- Log N sent and M failed
- If M > 0: report which emails failed (they remain in the queue with error annotation)

On MCP error (email-mcp unavailable):
- Write `AI_Employee_Vault/Needs_Action/ERROR_<ts>_email-flush-failed.md`
- Do NOT modify the queue — leave emails for the next flush attempt

**Step 3d: Report**

```
Email Queue Flush Complete
--------------------------
Sent:   N emails
Failed: M emails
Mode:   <DRY_RUN / LIVE>

<If M > 0:>
Failed emails (still in queue):
  - To: <to> | Subject: <subject> | Error: <error>
```

### Operation: discard

Remove specific items from the queue without sending them.

**Step 3a: Identify items to discard**

If the user named specific recipients or subjects, match those items.
If the user said "discard all" or "clear queue", mark all items for removal.

**Step 3b: Confirm before discarding**

List the items to be discarded and ask for confirmation:
```
About to discard N queued email(s):
  - To: <to> | Subject: <subject> | Queued: <age>

These emails will NOT be sent. Proceed? (Reply 'yes' to confirm)
```

**Step 3c: Execute discard**

On confirmation, rewrite `scripts/email_outbox_queue.json` with the remaining
items (those NOT marked for discard). If discarding all, write `[]`.

Log each discarded email as a `queue_discard` audit entry.

---

## Step 4 — Log the Operation

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "email_queue_<status|flush|discard>",
  "actor": "claude_code",
  "target": "scripts/email_outbox_queue.json",
  "parameters": {
    "operation": "<status|flush|discard>",
    "queue_size_before": 0,
    "sent": 0,
    "failed": 0,
    "discarded": 0,
    "dry_run": true
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "success | failure"
}
```

---

## Completion Signal

```
<promise>TASK_COMPLETE</promise>
```
