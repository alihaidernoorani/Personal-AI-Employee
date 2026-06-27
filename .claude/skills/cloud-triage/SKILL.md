---
name: cloud-triage
description: |
  Cloud agent task classification and plan drafting skill.
  Reads unclaimed Needs_Action/ task files, classifies by type (email, whatsapp,
  finance, signal, social_post_trigger, odoo_draft), drafts a response plan using
  Company_Handbook.md and Business_Goals.md, writes Plans/PLAN_<task_id>_<ts>.md
  with full MCP action specification, writes Signals/SIGNAL_plan_ready_<ts>.md,
  and moves the task from In_Progress/cloud/ to In_Progress/local/ for local execution.
  BOUNDARY: All vault writes use safe_vault_write(). MUST NOT call any MCP tool
  except odoo-mcp (create_invoice, update_expense) in ODOO_DRAFT_ONLY mode.
  Triggered by: cloud agent processing unclaimed tasks, "run cloud-triage skill".
write_boundary:
  allowed_paths:
    - Plans/
    - Signals/
    - In_Progress/cloud/
    - In_Progress/local/
    - Needs_Action/
    - Updates/
  prohibited_paths:
    - Dashboard.md
    - Done/
    - Approved/
    - Rejected/
  mcp_tools_allowed:
    - odoo-mcp/create_invoice (draft only, when ODOO_DRAFT_ONLY=true)
    - odoo-mcp/update_expense (draft only, when ODOO_DRAFT_ONLY=true)
  mcp_tools_prohibited:
    - email-mcp (all tools)
    - social-mcp (all tools)
    - browser-mcp (all tools)
    - odoo-mcp/post_invoice
---

# Cloud Triage

Classify and draft response plans for unclaimed vault tasks. This skill runs on the
cloud VM only. It MUST NOT send emails, post to social media, or execute any final
irreversible action. All output is draft plans for local agent review.

---

## Step 1 — Validate Cloud Boundary

Before doing anything:

1. Verify `AGENT_ROLE=cloud` environment variable is set.
   - If not cloud: output "ERROR: cloud-triage only runs on AGENT_ROLE=cloud" and stop.
2. Import `safe_vault_write` from `watchers/cloud_boundary.py`.
   - All file writes in this skill MUST use `safe_vault_write()`.
   - Direct `Path.write_text()` calls are PROHIBITED.

---

## Step 2 — Read Context

Read the following files in order:

1. `AI_Employee_Vault/Company_Handbook.md` — rules of engagement, tone, priorities
2. `AI_Employee_Vault/Business_Goals.md` — OKRs, services, contact types

---

## Step 3 — Scan for Unclaimed Tasks

List all `.md` files in `AI_Employee_Vault/Needs_Action/` that are NOT already
in `In_Progress/cloud/` or `In_Progress/local/`.

Skip files:
- Starting with `ERROR_` (already failed)
- Starting with `_` (draft)
- Already appearing in `In_Progress/cloud/` or `In_Progress/local/`

Sort by `priority` (urgent → high → normal → low) then `received` ascending.

---

## Step 4 — Claim Task (Claim-by-Move)

For the first unclaimed task:

1. Move the file from `AI_Employee_Vault/Needs_Action/<task>.md`
   → `AI_Employee_Vault/In_Progress/cloud/<task>.md`
   - Use `os.rename()` for atomicity (prevents double-claim)
   - If rename fails (file already moved by another agent): skip this task and try next

2. Read the task file and extract:
   - `type` from YAML frontmatter
   - `priority`, `received`, `sender`, `subject`, `message_text` (where applicable)

---

## Step 5 — Classify and Draft Plan

Based on `type`, draft the appropriate plan:

### Type: email

1. Classify intent: support request, invoice query, partnership, spam, other
2. Draft reply using Company_Handbook.md tone guidelines
3. Identify required MCP action: `email-mcp/send_email` (LOCAL ONLY — do not call here)
4. Write `AI_Employee_Vault/Plans/PLAN_<task_id>_<ts>.md`:

```markdown
---
type: plan
task_ref: <task_filename>
originating_agent: cloud_agent
created: <ISO-8601Z>
action_type: email_reply
mcp_tool: email-mcp/send_email
executing_agent: local
requires_approval: true
---

# Plan: Email Reply — <subject>

## Classification
<intent classification>

## Draft Reply
<full email reply text>

## MCP Action Spec
Tool: email-mcp/send_email
Parameters:
  to: <sender email>
  subject: Re: <subject>
  body: <draft reply text>
```

### Type: whatsapp

Same structure as email. MCP tool: `browser-mcp` (local execution only).

### Type: finance

Draft an Odoo entry. MCP tool: `odoo-mcp/create_invoice` (draft, local execution for post_invoice).

### Type: social_post_trigger

Draft post content using Business_Goals.md OKRs and Company_Handbook.md tone:

1. Choose platform from task file (`platform` field)
2. Draft 100–300 word post
3. Identify optimal posting time
4. Write `Plans/PLAN_<id>_social.md`
5. Write `Pending_Approval/APPROVAL_<id>_social.md` via safe_vault_write

Check stale drafts: if any `Pending_Approval/APPROVAL_*_social.md` is older than 48 hours:
- Write `Signals/SIGNAL_stale_draft_<ts>.md` with `requires_human_action: false`
- Do NOT auto-publish

### Type: odoo_draft

1. Check ODOO_AVAILABLE: read `Signals/` — if last SIGNAL_odoo_down is more recent than
   last SIGNAL_odoo_recovered, set ODOO_AVAILABLE=False.
2. If ODOO_AVAILABLE=False: leave task in `In_Progress/cloud/` with a warning comment. Stop.
3. If ODOO_AVAILABLE=True: call `odoo-mcp/create_invoice` or `odoo-mcp/update_expense` (draft).
4. Write `Plans/PLAN_<id>_odoo.md` with the draft record ID and amount.
5. Write `Pending_Approval/APPROVAL_<id>_odoo.md`.

### Type: signal

Route via signals_watcher pattern. Write a log entry only (no plan needed).

### Type: unknown / unrecognised

Write `Plans/PLAN_<id>_unknown.md` with full task content and note "requires human classification".

---

## Step 6 — Write Plan Ready Signal

After writing the plan, write `AI_Employee_Vault/Signals/SIGNAL_plan_ready_<ts>.md`:

```markdown
---
signal_type: plan_ready
severity: info
created: <ISO-8601Z>
agent_id: cloud_agent
requires_human_action: false
task_ref: <task_filename>
plan_ref: Plans/PLAN_<id>.md
---

# Plan Ready

Cloud triage complete for `<task_filename>`.
Plan written to `Plans/PLAN_<id>.md`.
Local agent should proceed with review and approval.
```

---

## Step 7 — Move Task to Local

Move `AI_Employee_Vault/In_Progress/cloud/<task>.md`
→ `AI_Employee_Vault/In_Progress/local/<task>.md`

This signals the local agent that the plan is ready and local execution should proceed.

---

## Step 8 — Repeat or Stop

If `Needs_Action/` still has unclaimed tasks and the processing budget has not exceeded
10 tasks per invocation: return to Step 3.

Otherwise: output a summary of tasks processed.

---

## Completion Signal

```
<promise>TASK_COMPLETE</promise>
```
