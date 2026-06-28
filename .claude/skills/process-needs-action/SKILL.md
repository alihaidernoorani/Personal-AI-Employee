---
name: process-needs-action
description: |
  Processes all pending items in the AI_Employee_Vault/_System/Needs_Action/ folder.
  Reads Reference/Company_Handbook.md first, then for each pending task creates a
  _System/Plans/PLAN_*.md file, and for sensitive actions writes a
  _System/Pending_Approval/APPROVAL_*.md file. Moves the source task to _System/Done/,
  updates Dashboard.md, and appends NDJSON audit logs.
  Handles types: file_drop, email, whatsapp, action_trigger, error.
  Use this skill whenever new items appear in _System/Needs_Action or on a scheduled basis.
---

# Process Needs Action

Process every pending item in the vault through a six-step workflow.

---

## Step 1 — Read the Rules

Before doing anything else, read `AI_Employee_Vault/Reference/Company_Handbook.md` to
load the current rules of engagement. All decisions in Steps 3–5 must respect
these rules.

Also read `AI_Employee_Vault/Reference/Business_Goals.md` for context on services and
communication priorities.

---

## Step 2 — Check for Cloud-Prepared Tasks (Platinum)

Before scanning _System/Needs_Action/, check `AI_Employee_Vault/_System/In_Progress/local/` for
tasks moved there by the cloud agent (tasks with a linked cloud-prepared plan).

For each file in `_System/In_Progress/local/` (excluding `.gitkeep`):

1. Read the task file's YAML frontmatter
2. Look for a `plan_ref` field pointing to `Plans/PLAN_*.md`
3. If `plan_ref` exists AND that plan file exists:
   - Read the plan file
   - Extract `action_type` and `mcp_tool` fields
   - **Validate** that the referenced MCP tool is available locally:
     - `email-mcp/send_email` → check `email-mcp` is in MCP config
     - `social-mcp/post_*` → check `social-mcp` is in MCP config
     - `odoo-mcp/post_invoice` → check `odoo-mcp` is in MCP config
   - If tool is available AND `requires_approval: true` in plan:
     → Write `_System/Pending_Approval/APPROVAL_*.md` using the plan's MCP action spec
     → Move task from `_System/In_Progress/local/` to `_System/Done/DONE_<task>.md`
   - If tool is available AND `requires_approval: false`:
     → Pass to execute-plan skill directly (write an `action_trigger` to `_System/Needs_Action/`)
     → Move task to `_System/Done/`
   - If tool is NOT available:
     → Write `_System/Needs_Action/ERROR_<ts>_mcp-unavailable.md` with plan reference
     → Leave task in `_System/In_Progress/local/`
   - **Log** with `originating_agent: cloud_agent, executing_agent: local`

4. If `plan_ref` does NOT exist in the task file: leave it in `_System/In_Progress/local/`
   for normal processing (will be picked up as orphaned by vault-health skill)

After processing all `_System/In_Progress/local/` cloud-prepared tasks, proceed to Step 3.

---

## Step 3 — Inventory Needs_Action

List all `.md` files in `AI_Employee_Vault/_System/Needs_Action/`. Skip any file whose
name starts with `_` (draft/claimed) or `ERROR_` (already failed).

Sort the remaining files by:
1. `priority` field in YAML frontmatter: `urgent` → `high` → `normal` → `low`
2. `received` timestamp ascending (oldest first) as tiebreaker.

---

## Step 4 — Process Each Item

For each `.md` file in the sorted list, do the following. If any sub-step
fails, follow the **Error Path** at the bottom of this section instead.

### 3a. Read and Parse

Read the file and extract the YAML frontmatter (`type`, `priority`, `status`,
`sender`, `subject`, `imap_uid`, `message_text`, `received`).

### 3b. Determine Action by Type

| `type`          | Action |
|-----------------|--------|
| `file_drop`     | Read the copied file in `_System/Needs_Action/`. Summarise its contents and determine if any follow-up is required per Reference/Company_Handbook rules. |
| `email`         | Draft a reply following Company_Handbook Communication Standards. Create a Plan file AND an Approval file (see Step 3c-email). |
| `whatsapp`      | Summarise message context and log for reference. Silver tier is receive-only — no outbound WhatsApp action. Create Plan with status: complete. |
| `action_trigger`| Log the trigger. This type is handled by the execute-plan skill, not this skill. Flag for execute-plan. |
| `error`         | Log and alert; do not auto-resolve. Flag for human review. |
| _(unknown)_     | Flag for human review with a note explaining the unknown type. |

### 3c. Write Plan File

Create `AI_Employee_Vault/_System/Plans/PLAN_<timestamp>_<original-stem>.md` where
`<timestamp>` is the current UTC time as `YYYYMMDDTHHMMSSZ` and
`<original-stem>` is the stem of the source task file (without the `.md`
extension).

**For type: email** — Plan structure (saved to `_System/Plans/`):

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
`AI_Employee_Vault/_System/Pending_Approval/APPROVAL_<timestamp>_email_<slug>.md`

Where `<slug>` is derived from the sender's email address (alphanumeric, hyphenated).

Use this exact structure (fast-path header required):

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
created: "<ISO-8601 UTC>"
status: pending
---

> [!caution] ⏳ Pending Approval — SEND EMAIL
> **To**: <sender email> · **Subject**: Re: <original subject>
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook
Human-in-the-Loop Rules, all outbound email requires explicit human approval.

## Action Summary

**To**: <sender email>
**Subject**: Re: <original subject>
**Action**: Click ✅ Approve or ❌ Reject below, or move this file to `_System/Approved/` / `_System/Rejected/`.
```

Then append these two in-file Meta Bind buttons (they set this file's own
`status`; the approval watcher picks it up and moves the file). Use a real
triple-backtick fence for each block — they are shown here inside a `~~~` fence
only to display the nested fences:

~~~
```meta-bind-button
id: "approve-<original-stem>"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "reject-<original-stem>"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click ✅ Approve or ❌ Reject above — the approval watcher moves this file and runs (or archives) the action automatically.
~~~

The same button pair applies to finance and social approval files; only the
`reason`/`parameters` differ. Valid `style` values: `default`, `primary`,
`destructive`, `plain` (never `secondary`).

**Fast-path header requirements** (all future APPROVAL_*.md files must include):
- YAML frontmatter with `type`, `action`, `created` (ISO-8601 UTC), `status` fields
- `> [!caution] ⏳ Pending Approval — <ACTION TYPE>` callout as first content after YAML
- Callout must include: action/payee/amount or recipient/subject, and approve/reject instructions
- Purpose: human can understand and act within 10 lines of reading

### Error Path (if processing a file fails)

1. Create `AI_Employee_Vault/_System/Needs_Action/ERROR_<timestamp>_<original-stem>.md`
   with a description of what failed and why.
2. Append a log entry with `"result": "failure"` (see Step 5 schema).
3. Continue processing the remaining files — do not stop.

---

## Step 5 — Move Task to Done

After successfully writing the Plan file (and Approval file if applicable) for a task:

Move the source `.md` file from `AI_Employee_Vault/_System/Needs_Action/<filename>`
to `AI_Employee_Vault/_System/Done/DONE_<filename>` (prepend `DONE_` and preserve the
rest of the original filename exactly).

---

## Step 5.5 — Sync Pipeline.md

After moving the task file and (optionally) creating an approval file, update
`AI_Employee_Vault/Pipeline.md` to reflect the new state. This is an additive
step — existing cards are preserved.

### (a) File moved to Done

When a file moves from `_System/Needs_Action/` to `_System/Done/DONE_<filename>`:
1. Read `Pipeline.md`
2. Find any `- [ ] [[_System/Needs_Action/<filename>|...]]` card in `## 📥 Needs Action`
3. Move that card to `## ✅ Done (Recent)` as `- [x] [[_System/Done/DONE_<filename>|<display-name>]]`
4. If the Done column has more than 10 `- [x]` cards, remove the oldest one

### (b) File moved to In_Progress

When a file moves from `_System/Needs_Action/<file>` to `_System/In_Progress/<agent>/<file>`:
1. Read `Pipeline.md`
2. Find the `- [ ] [[_System/Needs_Action/<file>|...]]` card in `## 📥 Needs Action`
3. Move that card to `## 🔄 In Progress` as `- [ ] [[_System/In_Progress/<agent>/<file>|<display-name>]]`

### (c) Approval file created

When `_System/Pending_Approval/APPROVAL_*.md` is created:
1. Read `Pipeline.md`
2. Add a new card to `## ✋ Pending Approval`:
   `- [ ] [[_System/Pending_Approval/<approval-filename>|<action-type>: <brief-description>]] #<domain-tag>`
3. Domain tags: email approvals → `#email`, finance → `#finance`, social → `#social`

**Implementation note**: Only update Pipeline.md if the file exists and is readable.
Never fail the overall processing loop if Pipeline.md sync fails — log the error
to `_System/Needs_Action/ERROR_<ts>_pipeline-sync-fail.md` and continue.

---

## Step 6 — Update Dashboard.md

After all tasks are processed, rewrite `AI_Employee_Vault/Dashboard.md`
dynamic tokens. If `Dashboard.md` is missing, create it from scratch with
the full token structure below.

Replace each token with live data:

| Token | Replacement |
|-------|-------------|
| `<!-- AI_EMPLOYEE:UPDATED -->` | Current UTC timestamp in ISO-8601 format |
| `<!-- AI_EMPLOYEE:NEEDS_ACTION_COUNT -->` | Count of `.md` files currently in `_System/Needs_Action/` |
| `<!-- AI_EMPLOYEE:DONE_TODAY_COUNT -->` | Count of `DONE_*` files in `_System/Done/` modified today (UTC date) |
| `<!-- AI_EMPLOYEE:INBOX_COUNT -->` | Count of files currently in `_System/Inbox/` |
| `<!-- AI_EMPLOYEE:ACTIVE_ITEMS -->` | Bullet list of remaining `_System/Needs_Action/` filenames; if empty write `_No pending items._` |
| `<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->` | Last 5 `DONE_*` files sorted newest-first, each with filename + one-line summary |
| `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` | Count of files in `_System/Pending_Approval/` |
| `<!-- AI_EMPLOYEE:PENDING_APPROVAL_LIST -->` | Categorized draft list — see format note below. If empty write `_No pending approvals._` |
| `<!-- AI_EMPLOYEE:RECENT_REJECTIONS -->` | Last 3 filenames in `_System/Rejected/` sorted newest-first; if empty write `_No recent rejections._` |

### PENDING_APPROVAL_LIST format

Group the current `_System/Pending_Approval/APPROVAL_*.md` files into three
sub-sections by filename token, in this order. Omit a sub-section if it has no items.

- `### 📧 Draft Email Approvals` — files containing `_email_`
- `### 📣 Draft Social Media Post Approvals` — files containing `linkedin`, `facebook`, `instagram`, or `twitter`
- `### 💰 Finance Approvals` — files containing `_finance_`

For each file, write one row with a wikilink and a pair of inline Meta Bind
buttons (Approve/Reject) referenced by id:

```
- [[_System/Pending_Approval/<stem>|<friendly label>]] — `BUTTON[ap-<id>]` `BUTTON[rj-<id>]`
```

Then, still inside the marker, emit one hidden button definition per id. Each
sets the target file's `status` via a cross-file bind target (path is
vault-relative, no `.md` extension):

~~~
```meta-bind-button
id: "ap-<id>"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/<stem>#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-<id>"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/<stem>#status"
    evaluate: false
    value: "rejected"
```
~~~

`<id>` must be unique and stable per file (derive it from the filename). Valid
`style` values are only `default`, `primary`, `destructive`, `plain` — never
`secondary`. Clicking a button sets `status`; the approval watcher then moves
the file to `_System/Approved/` or `_System/Rejected/` and fires the workflow.

---

## Step 7 — Log the Session

Append one NDJSON line per processed task to
`AI_Employee_Vault/_System/Logs/YYYY-MM-DD.json` (use today's UTC date for the
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
