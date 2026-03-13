---
name: process-needs-action
description: |
  Processes all pending items in the AI_Employee_Vault/Needs_Action/ folder.
  Reads Company_Handbook.md first, then for each pending task creates a
  Plans/PLAN_*.md file, moves the source task to Done/, updates Dashboard.md,
  and appends NDJSON audit logs. Use this skill whenever new items appear in
  Needs_Action or on a scheduled basis.
---

# Process Needs Action

Process every pending item in the vault through a six-step workflow.

---

## Step 1 — Read the Rules

Before doing anything else, read `AI_Employee_Vault/Company_Handbook.md` to
load the current rules of engagement. All decisions in Steps 3–5 must respect
these rules.

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
`original_name`, `received`).

### 3b. Determine Action by Type

| `type`      | Action |
|-------------|--------|
| `file_drop` | Read the copied file in `Needs_Action/`. Summarise its contents and determine if any follow-up is required per Company_Handbook rules. |
| `email`     | Draft a reply following Company_Handbook Communication Standards. |
| `error`     | Log and alert; do not auto-resolve. Flag for human review. |
| _(unknown)_ | Flag for human review with a note explaining the unknown type. |

### 3c. Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_<original-stem>.md` where
`<timestamp>` is the current UTC time as `YYYYMMDDTHHMMSSz` and
`<original-stem>` is the stem of the source task file (without the `.md`
extension).

The plan file MUST follow this structure:

```markdown
---
type: plan
source_task: <source task filename>
created_at: <ISO-8601 UTC timestamp>
requires_approval: false
status: draft
---

## Summary

<One paragraph describing what this task is and what was decided.>

## Analysis

<Key findings from reading the task file and applying Handbook rules.>

## Actions

<For each safe action, write a standard checkbox:>
- [ ] <Action description>

<For each sensitive action (external comms, financial, deletions), write an approval checkbox:>
- [ ] APPROVE: <Action description>

## Notes

<Any caveats, edge cases, or information the human reviewer should know.>
```

Use `- [ ] APPROVE:` only for actions that require explicit human sign-off per
the Company_Handbook Human-in-the-Loop Rules. If no sensitive actions are
needed, omit `APPROVE` lines entirely.

### Error Path (if processing a file fails)

1. Create `AI_Employee_Vault/Needs_Action/ERROR_<timestamp>_<original-stem>.md`
   with a description of what failed and why.
2. Append a log entry with `"result": "failure"` (see Step 5 schema).
3. Continue processing the remaining files — do not stop.

---

## Step 4 — Move Task to Done

After successfully writing the Plan file for a task:

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
| `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` | Count of plan files in `Plans/` containing `- [ ] APPROVE:` lines |

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
    "plan_file": "<PLAN_*.md filename>"
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "success | deferred | failure"
}
```

Use `"result": "deferred"` when a plan was created but contains `APPROVE`
lines awaiting human sign-off. Use `"result": "failure"` when the error path
was taken.

---

## Completion Signal

When Dashboard.md and all log entries are written, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
