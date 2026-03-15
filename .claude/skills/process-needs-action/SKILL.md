---
name: process-needs-action
description: |
  Processes all pending items in the AI_Employee_Vault/Needs_Action/ folder.
  Reads Company_Handbook.md first, then for each pending task creates a
  Plans/PLAN_*.md file, and for sensitive actions writes a
  Pending_Approval/APPROVAL_*.md file. Moves the source task to Done/,
  updates Dashboard.md, and appends NDJSON audit logs.
  Handles types: file_drop, email, whatsapp, action_trigger, error.
  Use this skill whenever new items appear in Needs_Action or on a scheduled basis.
---

# Process Needs Action

Process every pending item in the vault through a six-step workflow.

---

## Step 1 — Read the Rules

Before doing anything else, read `AI_Employee_Vault/Company_Handbook.md` to
load the current rules of engagement. All decisions in Steps 3–5 must respect
these rules.

Also read `AI_Employee_Vault/Business_Goals.md` for context on services and
communication priorities.

---

## Step 2 — Inventory Needs_Action

List all `.md` files in `AI_Employee_Vault/Needs_Action/`. Skip any file whose
name starts with `_` (draft/claimed) or `ERROR_` (already failed).

Sort the remaining files by:
1. `priority` field in YAML frontmatter: `urgent` → `high` → `normal` → `low`
2. `received` timestamp ascending (oldest first) as tiebreaker.

---

## Step 3 — Process Each Item

For each `.md` file in the sorted list, do the following. If any sub-step
fails, follow the **Error Path** at the bottom of this section instead.

### 3a. Read and Parse

Read the file and extract the YAML frontmatter (`type`, `priority`, `status`,
`sender`, `subject`, `imap_uid`, `message_text`, `received`).

### 3b. Determine Action by Type

| `type`          | Action |
|-----------------|--------|
| `file_drop`     | Read the copied file in `Needs_Action/`. Summarise its contents and determine if any follow-up is required per Company_Handbook rules. |
| `email`         | Draft a reply following Company_Handbook Communication Standards. Create a Plan file AND an Approval file (see Step 3c-email). |
| `whatsapp`      | Summarise message context and log for reference. Silver tier is receive-only — no outbound WhatsApp action. Create Plan with status: complete. |
| `action_trigger`| Log the trigger. This type is handled by the execute-plan skill, not this skill. Flag for execute-plan. |
| `error`         | Log and alert; do not auto-resolve. Flag for human review. |
| _(unknown)_     | Flag for human review with a note explaining the unknown type. |

### 3c. Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_<original-stem>.md` where
`<timestamp>` is the current UTC time as `YYYYMMDDTHHMMSSZ` and
`<original-stem>` is the stem of the source task file (without the `.md`
extension).

**For type: email** — Plan structure:

```markdown
---
type: plan
source_task: <source task filename>
created_at: <ISO-8601 UTC timestamp>
requires_approval: true
status: awaiting_approval
---

## Summary

Reply to email from <sender> regarding: <subject>

## Analysis

<Key findings from reading the email headers and applying Handbook comms rules.>

## Actions

- [ ] APPROVE: Send reply email to <sender>

## Drafted Reply

<Full drafted reply body per Company_Handbook Communication Standards>

## Notes

<Any caveats or context the human reviewer should know.>
```

**For type: whatsapp** — Plan structure:

```markdown
---
type: plan
source_task: <source task filename>
created_at: <ISO-8601 UTC timestamp>
requires_approval: false
status: complete
---

## Summary

WhatsApp message received from <sender>.

## Analysis

<Summary of message content and context.>

## Actions

- [x] Message logged and filed (Silver tier: receive-only)

## Notes

WhatsApp outbound messaging is not implemented in Silver tier.
Review the message and respond manually if needed.
```

**For type: file_drop** — Use existing Bronze plan structure (requires_approval: false unless
Handbook rules indicate sensitive content).

**For type: error** — Plan structure with requires_approval: false, status: needs_human_review.

### 3c-email. Write Approval File (only for type: email)

After writing the Plan file, also write:
`AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_email_<slug>.md`

Where `<slug>` is derived from the sender's email address (alphanumeric, hyphenated).

Use this exact structure:

```markdown
---
type: approval_request
action: send_email
plan_file: "PLAN_<timestamp>_<original-stem>.md"
reason: "Reply to email from <sender> regarding: <subject>"
parameters:
  to: "<sender email>"
  subject: "Re: <original subject>"
  body: |
    <Full drafted reply body>
  reply_to_uid: "<imap_uid>"
timestamp: "<ISO-8601 UTC>"
status: pending
---

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook
Human-in-the-Loop Rules, all outbound email requires explicit human approval.

## Action Summary

**To**: <sender email>
**Subject**: Re: <original subject>
**Action**: Move this file to `Approved/` to send, or `Rejected/` to discard.
```

### Error Path (if processing a file fails)

1. Create `AI_Employee_Vault/Needs_Action/ERROR_<timestamp>_<original-stem>.md`
   with a description of what failed and why.
2. Append a log entry with `"result": "failure"` (see Step 5 schema).
3. Continue processing the remaining files — do not stop.

---

## Step 4 — Move Task to Done

After successfully writing the Plan file (and Approval file if applicable) for a task:

Move the source `.md` file from `AI_Employee_Vault/Needs_Action/<filename>`
to `AI_Employee_Vault/Done/DONE_<filename>` (prepend `DONE_` and preserve the
rest of the original filename exactly).

---

## Step 5 — Update Dashboard.md

After all tasks are processed, rewrite `AI_Employee_Vault/Dashboard.md`
dynamic tokens. If `Dashboard.md` is missing, create it from scratch with
the full token structure below.

Replace each token with live data:

| Token | Replacement |
|-------|-------------|
| `<!-- AI_EMPLOYEE:UPDATED -->` | Current UTC timestamp in ISO-8601 format |
| `<!-- AI_EMPLOYEE:NEEDS_ACTION_COUNT -->` | Count of `.md` files currently in `Needs_Action/` |
| `<!-- AI_EMPLOYEE:DONE_TODAY_COUNT -->` | Count of `DONE_*` files in `Done/` modified today (UTC date) |
| `<!-- AI_EMPLOYEE:INBOX_COUNT -->` | Count of files currently in `Inbox/` |
| `<!-- AI_EMPLOYEE:ACTIVE_ITEMS -->` | Bullet list of remaining `Needs_Action/` filenames; if empty write `_No pending items._` |
| `<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->` | Last 5 `DONE_*` files sorted newest-first, each with filename + one-line summary |
| `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` | Count of files in `Pending_Approval/` |
| `<!-- AI_EMPLOYEE:PENDING_APPROVAL_LIST -->` | Bullet list of filenames in `Pending_Approval/`; if empty write `_No pending approvals._` |
| `<!-- AI_EMPLOYEE:RECENT_REJECTIONS -->` | Last 3 filenames in `Rejected/` sorted newest-first; if empty write `_No recent rejections._` |

---

## Step 6 — Log the Session

Append one NDJSON line per processed task to
`AI_Employee_Vault/Logs/YYYY-MM-DD.json` (use today's UTC date for the
filename). Use this exact schema:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "process_needs_action",
  "actor": "claude_code",
  "target": "<source task filename>",
  "parameters": {
    "type": "<item type>",
    "priority": "<priority>",
    "plan_file": "<PLAN_*.md filename>",
    "approval_file": "<APPROVAL_*.md filename or null>"
  },
  "approval_status": "auto | deferred",
  "approved_by": "system",
  "result": "success | deferred | failure"
}
```

Use `"result": "deferred"` when an approval file was created (email type) and
is awaiting human sign-off. Use `"result": "failure"` when the error path
was taken.

---

## Completion Signal

When Dashboard.md and all log entries are written, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
