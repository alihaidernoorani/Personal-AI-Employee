---
name: execute-plan
description: |
  Executes approved actions by processing type: action_trigger files in
  AI_Employee_Vault/Needs_Action/. For each trigger, reads the referenced
  approval file, identifies the action type, and calls the appropriate
  MCP tool. On success, moves files to Done/ and logs the result.
  On failure (3 retries, 5s backoff), creates ERROR_*.md and restores
  the approval file to Pending_Approval/.
  Supported actions: send_email (via email-mcp), linkedin_post (via browsing-with-playwright).
  Use this skill after ApprovalWatcher creates ACTION_*.md trigger files.
---

# Execute Plan

Execute all pending approved actions by processing `type: action_trigger` files.

---

## Step 1 — Inventory Action Triggers

List all `.md` files in `AI_Employee_Vault/Needs_Action/` where the YAML
frontmatter `type` is `action_trigger`.

Sort by `received` timestamp ascending (oldest first).

If no `action_trigger` files exist, output:
```
No pending action triggers found.
<promise>TASK_COMPLETE</promise>
```

---

## Step 2 — Process Each Action Trigger

For each `ACTION_*.md` file, perform the following steps.

### 2a. Read and Parse the Trigger File

Extract from YAML frontmatter:
- `action_type` — the action to perform (`send_email`, `linkedin_post`, etc.)
- `approval_file` — filename of the APPROVAL_*.md that was approved
- `action_params` — JSON string of parameters for the action

Parse `action_params` as JSON to get the parameter dictionary.

### 2b. Locate the Referenced Approval File

Check `AI_Employee_Vault/Approved/<approval_file>` exists.

If the approval file is missing, write an ERROR_*.md and skip this trigger.

### 2c. Execute the Action (with retry)

Attempt the action up to **3 times** with **5-second backoff** between attempts.

#### Action: send_email

Call the `email-mcp` `send_email` tool with parameters:
- `to` — from `action_params.to`
- `subject` — from `action_params.subject`
- `body` — from `action_params.body`
- `reply_to_message_id` — from `action_params.reply_to_uid` (optional)

If `DRY_RUN=true` (default), the tool will log the action without sending.
If `DRY_RUN=false`, the tool will send the real email.

#### Action: linkedin_post

If `DRY_RUN=true`:
- Log the action to `AI_Employee_Vault/Logs/YYYY-MM-DD.json` with `action_type: linkedin_post, approval_status: dry_run`
- Do NOT call any external tool

If `DRY_RUN=false`:

Use the `playwright` MCP tools directly (they are available as `browser_navigate`,
`browser_snapshot`, `browser_click`, `browser_type`, `browser_wait_for`, etc.).

Execute the following steps **in order**. If any step fails, treat it as a
retryable error and follow the retry logic in Step 2c.

**LinkedIn Posting Workflow:**

1. **Navigate to LinkedIn feed**
   Call `browser_navigate` with `url: "https://www.linkedin.com/feed/"`.

2. **Wait for page load**
   Call `browser_wait_for` with `time: 3000` (3 seconds).

3. **Verify login state**
   Call `browser_snapshot`. Inspect the result:
   - If you see a "Sign in" or "Join now" button → LinkedIn session has expired.
     Write `ERROR_<ts>_linkedin-session-expired.md` to `Needs_Action/` with
     instructions to re-open the browser and log in manually.
     Move the approval file back to `Pending_Approval/`. Stop this action.
   - If you see a feed or profile nav → proceed.

4. **Open the post composer**
   Call `browser_click` targeting the "Start a post" button.
   Use `element: "Start a post"` — Playwright will match by accessible name.
   If not found via click, call `browser_snapshot` to get the current `ref`,
   then retry with the `ref` from the snapshot.

5. **Wait for composer to open**
   Call `browser_wait_for` with `time: 2000`.

6. **Type the post content**
   Call `browser_type` with:
   - `element: "text editor"` (LinkedIn's composer uses a contenteditable div)
   - `text: <post_content from action_params.post_content>`
   - Do NOT set `submit: true`

7. **Verify content was entered**
   Call `browser_snapshot`. Confirm the text appears in the composer.

8. **Click Post**
   Call `browser_click` with `element: "Post"`.
   If multiple "Post" elements exist, use the primary/submit button
   (typically has `ref` visible in the snapshot near the composer modal).

9. **Wait for confirmation**
   Call `browser_wait_for` with `time: 3000`.
   Then call `browser_snapshot` and confirm the feed is visible
   (modal closed = post submitted successfully).

10. **Take a screenshot for the audit trail**
    Call `browser_take_screenshot` with `type: "png"`.
    Save the screenshot description/result in the log entry parameters.

**Session setup (one-time, manual):**
The `playwright` MCP uses a persistent browser profile at `playwright-profile/`.
On first use, open any browser page via the MCP, navigate to `https://www.linkedin.com`,
and log in manually. The session cookie is saved and reused on subsequent runs.

#### Action: unknown

Write `Needs_Action/ERROR_<ts>_unknown-action.md` and continue.

### 2d. On Success

1. Move `Needs_Action/ACTION_<ts>_<slug>.md` → `Done/DONE_ACTION_<ts>_<slug>.md`
2. Move `Approved/<approval_file>` → `Done/DONE_<approval_file>`
3. Find the linked Plan file (read `plan_file` from approval frontmatter) in `Plans/`
   and update its frontmatter `status` from `awaiting_approval` to `executed`
4. Append a NDJSON log entry (see Step 3 schema)

### 2e. On Failure (all 3 retries exhausted)

1. Write `AI_Employee_Vault/Needs_Action/ERROR_<timestamp>_<slug>.md` with failure details
2. Move `Approved/<approval_file>` back to `AI_Employee_Vault/Pending_Approval/<approval_file>`
3. Find the linked Plan file and update frontmatter `status` to `awaiting_approval`
4. Append a NDJSON log entry with `"result": "failure"`
5. Continue processing remaining triggers — do not stop

---

## Step 3 — Log Each Action

Append one NDJSON line per executed action to
`AI_Employee_Vault/Logs/YYYY-MM-DD.json` (use today's UTC date).

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "<action_type from trigger>",
  "actor": "claude_code",
  "target": "<to email or 'LinkedIn' or other target>",
  "parameters": {
    "trigger_file": "<ACTION_*.md filename>",
    "approval_file": "<APPROVAL_*.md filename>",
    "dry_run": true
  },
  "approval_status": "approved | dry_run",
  "approved_by": "human",
  "result": "success | failure | dry_run"
}
```

---

## Step 4 — Update Dashboard.md

After processing all triggers, update `AI_Employee_Vault/Dashboard.md`:

- `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` — count of files in `Pending_Approval/`
- `<!-- AI_EMPLOYEE:PENDING_APPROVAL_LIST -->` — bullet list of filenames in `Pending_Approval/`
- `<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->` — last 5 `DONE_*` files sorted newest-first
- `<!-- AI_EMPLOYEE:UPDATED -->` — current UTC timestamp

---

## Completion Signal

When all triggers are processed and Dashboard.md is updated, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
