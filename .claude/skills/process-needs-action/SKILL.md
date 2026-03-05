---
name: process-needs-action
description: |
  Processes all pending items in the AI_Employee_Vault/Needs_Action/ folder.
  Reads each .md file, determines the required action, executes safe actions
  directly, flags sensitive actions for human approval, updates Dashboard.md,
  and moves completed files to /Done/. Use this skill whenever new items
  appear in Needs_Action or on a scheduled basis.
---

# Process Needs Action

Read the vault's pending items and take appropriate action on each one.

## Step 1 — Read the Rules

Before doing anything, read `AI_Employee_Vault/Company_Handbook.md` to load
the current rules of engagement.

## Step 2 — Inventory Needs_Action

List all `.md` files in `AI_Employee_Vault/Needs_Action/`. Skip files that
start with `_` (already claimed). Sort by priority (urgent → high → normal → low),
then by `received` timestamp ascending (oldest first).

## Step 3 — Process Each Item

For each `.md` file found:

1. **Read** the file and parse the YAML frontmatter (`type`, `priority`, `status`).
2. **Decide** what action is needed based on `type`:
   - `file_drop` → Review the file, summarise its contents, determine if any
     follow-up is required.
   - `email` → Draft a reply according to Company_Handbook communication rules.
   - `error` → Log and alert; do not auto-resolve.
   - Unknown type → Flag for human review.
3. **Act** based on Company_Handbook approval rules:
   - Safe actions (drafts, summaries, internal notes) → execute directly.
   - Sensitive actions (sends, payments, deletes) → write an approval request
     to `AI_Employee_Vault/Pending_Approval/` instead.
4. **Move** the processed `.md` file to `AI_Employee_Vault/Done/` once handled.
   Rename with a `DONE_` prefix: `DONE_<original_filename>`.

## Step 4 — Update Dashboard.md

After processing all items, rewrite the dynamic sections of
`AI_Employee_Vault/Dashboard.md`:

- Set `<!-- AI_EMPLOYEE:UPDATED -->` to the current UTC timestamp.
- Count files in `/Needs_Action/`, `/Done/` (today), `/Inbox/` and update
  the corresponding `<!-- AI_EMPLOYEE:*_COUNT -->` placeholders.
- Replace `<!-- AI_EMPLOYEE:ACTIVE_ITEMS -->` with a bullet list of any items
  still in Needs_Action (if none, keep the default italic note).
- Replace `<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->` with the last 5 items
  moved to Done (filename + one-line summary).

## Step 5 — Log the Session

Append one JSON line per processed item to
`AI_Employee_Vault/Logs/YYYY-MM-DD.json` using this schema:

```json
{
  "timestamp": "ISO-8601Z",
  "action_type": "process_needs_action",
  "actor": "claude_code",
  "target": "<filename>",
  "parameters": { "type": "<item_type>", "priority": "<priority>" },
  "approval_status": "auto | pending_approval",
  "approved_by": "system | pending_human",
  "result": "success | deferred"
}
```

## Completion Signal

When all items are processed and Dashboard.md is updated, output:

```
<promise>TASK_COMPLETE</promise>
```

## Error Handling

If any step fails for a specific file:
1. Do NOT stop processing other files.
2. Create `AI_Employee_Vault/Needs_Action/ERROR_<timestamp>_<original>.md`
   describing what failed.
3. Log the failure with `"result": "failure"` in the daily log.
4. Continue to the next file.
