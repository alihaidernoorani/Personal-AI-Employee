---
name: whatsapp-reply
description: |
  Processes WHATSAPP_*.md task files from AI_Employee_Vault/Needs_Action/ where
  a reply is warranted. Drafts a reply per Company_Handbook.md communication
  rules and writes an Approval file to Pending_Approval/ — ALL WhatsApp outbound
  messages require human approval (FR-017, Gold tier). Does NOT send any message.
  The execute-plan skill handles sending after approval.
  Use this skill when a WhatsApp message requires a response, after the WhatsApp
  watcher has created a WHATSAPP_*.md in Needs_Action/.
  Triggered by: "run whatsapp-reply skill", "draft whatsapp reply", "respond to whatsapp".
---

# WhatsApp Reply

Draft a WhatsApp reply and route through the approval pipeline.
Every outbound WhatsApp message requires human approval — no auto-send.

---

## Step 1 — Read Rules

Read `AI_Employee_Vault/Company_Handbook.md` for:
- WhatsApp communication standards (tone, response time expectations)
- Known contacts list (affects priority and response style)
- Topics that must be escalated vs. handled autonomously

---

## Step 2 — Inventory WhatsApp Tasks

List all files in `AI_Employee_Vault/Needs_Action/` matching `WHATSAPP_*.md`.
Sort by `created` timestamp ascending (oldest first).

For each file, check if it requires a reply:
- If the message is informational only (no question, no action requested) →
  log it and mark as complete without drafting a reply (see Step 5, info-only path)
- If the message requires a response → proceed to Step 3

---

## Step 3 — Draft the Reply

Read the task file and extract:
- `sender` — phone number or contact name
- `message_text` — the raw WhatsApp message content
- `keyword_matched` — the keyword that triggered the watcher (if any)
- `created` — message timestamp

Draft a reply following `Company_Handbook.md` communication standards:

**Reply guidelines:**
- Keep WhatsApp replies concise (WhatsApp is a chat medium, not email)
- Match the tone of the original message (casual → casual, formal → formal)
- Address the specific question or request directly
- If the request requires action beyond a reply (e.g. sending a document, scheduling
  a call), note those follow-up actions in the Plan file
- Do NOT include pricing, credentials, or confidential information
- If the message is ambiguous, draft a clarifying question rather than an assumption

---

## Step 4 — Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_whatsapp_<sender_slug>.md`
where `<timestamp>` is current UTC as `YYYYMMDDTHHMMSSZ` and `<sender_slug>`
is the sender identifier (alphanumeric, hyphenated).

```markdown
---
type: plan
source_task: <WHATSAPP_*.md filename>
created_at: <ISO-8601 UTC timestamp>
requires_approval: true
status: awaiting_approval
sender: "<sender>"
reply_type: <reply|clarification|information>
---

## Summary

WhatsApp reply to <sender> regarding: <one-line summary of message>

## Original Message

<message_text from task file>

## Analysis

<Key context: is sender a known contact? What is the intent of their message?
What does the handbook say about this type of request?>

## Drafted Reply

<Full reply text — this is what will be sent via WhatsApp>

## Follow-up Actions (if any)

- [ ] <Any non-reply actions: send document, schedule call, etc.>

## Notes

<Any caveats for the human reviewer>
```

---

## Step 5 — Write Approval File (all reply cases)

Create `AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_whatsapp_<sender_slug>.md`:

```markdown
---
type: approval_request
action: whatsapp_reply
plan_file: "PLAN_<timestamp>_whatsapp_<sender_slug>.md"
reason: "WhatsApp outbound reply — all WhatsApp messages require human approval"
parameters:
  to: "<sender phone or contact name>"
  message: |
    <Full reply text — identical to Plan file drafted reply>
  source_task: "<WHATSAPP_*.md filename>"
risk_class: low
timestamp: "<ISO-8601 UTC>"
status: pending
---

## Why Approval is Required

All outbound WhatsApp messages require explicit human approval per
Company_Handbook.md Human-in-the-Loop Rules and Gold tier FR-017.
WhatsApp communication represents the business externally.

## Original Message

**From**: <sender>
**Received**: <message timestamp>
**Content**: <message_text>

## Drafted Reply

<Full reply text>

## Action

Move this file to `Approved/` to send the reply, or `Rejected/` to discard.
```

### Info-only path (no reply needed):

If the message is informational and requires no reply:
- Write a minimal Plan file with `requires_approval: false`, `status: complete`
- Do NOT write an Approval file
- Move the task to `Done/` directly

---

## Step 6 — Move Task to Done

After writing the Plan file (and Approval file if required):

Move `AI_Employee_Vault/Needs_Action/WHATSAPP_<id>.md`
→ `AI_Employee_Vault/Done/DONE_WHATSAPP_<id>.md`

---

## Step 7 — Log the Action

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "whatsapp_reply_drafted",
  "actor": "claude_code",
  "target": "<sender>",
  "parameters": {
    "plan_file": "<PLAN_*.md filename>",
    "approval_file": "<APPROVAL_*.md filename or null>",
    "reply_type": "<reply|clarification|info_only>"
  },
  "approval_status": "deferred | auto",
  "approved_by": "pending | system",
  "result": "deferred | success"
}
```

---

## Completion Signal

When all WhatsApp tasks are processed, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
