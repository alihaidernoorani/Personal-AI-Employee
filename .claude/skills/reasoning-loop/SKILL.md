---
name: reasoning-loop
description: |
  Ralph Wiggum persistence loop for multi-step tasks. Prevents Claude from
  exiting until the task is fully complete. Uses promise-based completion:
  Claude must output <promise>TASK_COMPLETE</promise> to exit the loop.
  Re-injects the task_prompt on each iteration if completion is not detected.
  Max iterations enforced to prevent infinite loops.
  Invoke with: /ralph-loop "<task_prompt>"
  Parameters: task_prompt (string) — the full task description to execute.
---

# Reasoning Loop (Ralph Wiggum)

Persist through a multi-step task until the promise token is emitted.
Claude will not exit until `<promise>TASK_COMPLETE</promise>` is output or
the max iteration limit is reached.

---

## What This Skill Does

The Ralph Wiggum loop wraps any task in a persistence harness:

1. Claude receives `task_prompt` and begins execution
2. At the end of each step, Claude checks: is the task done?
3. If YES → output `<promise>TASK_COMPLETE</promise>` (loop exits cleanly)
4. If NO → continue to the next step (loop continues)
5. If max iterations reached → write `ERROR_loop_max_iterations.md` and exit

This prevents Claude from stopping mid-task due to context limits, tool
failures, or ambiguous completion states.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_prompt` | string | yes | Full natural-language description of the task to complete |
| `max_iterations` | int | no | Maximum loop iterations before forced exit (default: 10) |
| `completion_promise` | string | no | Promise token to detect (default: `TASK_COMPLETE`) |

---

## Step 1 — Parse Task Prompt

Read `task_prompt` from the invocation arguments.

If `task_prompt` is empty or missing, output:
```
ERROR: task_prompt is required. Usage: /ralph-loop "<task description>"
```
and stop.

Set internal state:
- `iteration = 1`
- `max_iterations = 10` (or override from args)
- `completion_token = "TASK_COMPLETE"` (or override from args)
- `task_complete = false`

---

## Step 2 — Write State File

Write `AI_Employee_Vault/In_Progress/claude_code/LOOP_<timestamp>_state.md`:

```markdown
---
type: loop_state
task_prompt: "<task_prompt>"
started_at: "<ISO-8601Z>"
iteration: 1
max_iterations: 10
status: in_progress
---

## Task

<task_prompt>

## Iteration Log

- Iteration 1 started at <timestamp>
```

`<timestamp>` format: `YYYYMMDDTHHMMSSZ`

---

## Step 3 — Execute Task Steps

Work through the `task_prompt` step by step. For each step:

### 3a. Read current state
Before every tool call or file write, confirm the state file still shows
`status: in_progress`. If it shows `status: cancelled`, stop immediately.

### 3b. Decompose into sub-tasks
Break the `task_prompt` into the smallest testable units. Complete each
unit before moving to the next. Never skip a unit without logging why.

### 3c. Handle failures gracefully
If a step fails:
1. Log the failure in the state file under `## Iteration Log`
2. Attempt one retry with a different approach
3. If retry also fails, write `AI_Employee_Vault/Needs_Action/ERROR_<ts>_loop-step-failed.md`
   with full context, then continue to the next step if possible

### 3d. Check completion after each step
After completing each sub-task, ask: **Is the overall `task_prompt` now fully satisfied?**

- If YES → proceed to Step 5 (completion)
- If NO → update the state file iteration count and continue

### 3e. Enforce max iterations
At the start of each iteration:
```
if iteration > max_iterations:
    → write ERROR file (Step 4b)
    → stop
iteration += 1
```

---

## Step 4 — Iteration Cycle

### 4a. Update state file each iteration

Append to `## Iteration Log` in the state file:
```
- Iteration <N> completed at <timestamp>: <one-line summary of what was done>
```

Update frontmatter:
```yaml
iteration: <N>
```

### 4b. Max iterations exceeded

If `iteration > max_iterations`, write:
`AI_Employee_Vault/Needs_Action/ERROR_<ts>_loop-max-iterations.md`

```markdown
---
type: error
error_type: loop_max_iterations
task_prompt: "<task_prompt>"
iterations_completed: <N>
timestamp: "<ISO-8601Z>"
---

## Error: Maximum Iterations Reached

The reasoning loop exceeded the maximum of <max_iterations> iterations
without completing the task.

## Task

<task_prompt>

## Last Known State

<summary of last completed step>

## Recommended Action

Review the task prompt for ambiguity and restart with a more specific prompt.
Or increase max_iterations: /ralph-loop "<task>" --max-iterations 20
```

Then output:
```
<promise>TASK_COMPLETE</promise>
```
(exits loop even on failure — human will see the ERROR file)

---

## Step 5 — Completion

When the task is fully done:

### 5a. Update state file to completed

```yaml
status: completed
completed_at: "<ISO-8601Z>"
```

### 5b. Move state file to Done

Move `AI_Employee_Vault/In_Progress/claude_code/LOOP_<timestamp>_state.md`
→ `AI_Employee_Vault/Done/DONE_LOOP_<timestamp>_state.md`

### 5c. Log completion

Append to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "reasoning_loop_complete",
  "actor": "claude_code",
  "target": "loop",
  "parameters": {
    "task_prompt": "<task_prompt>",
    "iterations": <N>,
    "state_file": "DONE_LOOP_<timestamp>_state.md"
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "success"
}
```

### 5d. Emit promise token

Output exactly:

```
<promise>TASK_COMPLETE</promise>
```

---

## CLI Usage

### Basic invocation (PowerShell)

```powershell
# Run a task with the Ralph Wiggum loop
claude -p /ralph-loop "Process all emails in Needs_Action and send approved replies"
```

### With max iterations override

```powershell
claude -p '/ralph-loop "Run the weekly CEO briefing" --max-iterations 15'
```

### With custom completion token

```powershell
claude -p '/ralph-loop "Audit all subscriptions in Bank_Transactions.md" --completion-promise "AUDIT_DONE"'
```

### As a scheduled task (Windows Task Scheduler)

```powershell
# Run every Monday at 08:00
$action = New-ScheduledTaskAction -Execute "claude" `
    -Argument '-p "/ralph-loop \"Generate and queue the weekly LinkedIn post\""' `
    -WorkingDirectory "C:\Users\DELL\Documents\GitHub\Personal_AI_Employee"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 08:00

Register-ScheduledTask -TaskName "AI-Employee-Monday-Post" `
    -Action $action -Trigger $trigger -RunLevel Highest
```

### Via orchestrator (Python)

```python
import subprocess, sys

result = subprocess.run(
    [sys.executable, "-m", "claude", "-p",
     f'/ralph-loop "{task_prompt}" --max-iterations 10'],
    cwd="C:/Users/DELL/Documents/GitHub/Personal_AI_Employee",
    capture_output=True, text=True
)
# Loop exits when <promise>TASK_COMPLETE</promise> is detected in stdout
if "TASK_COMPLETE" in result.stdout:
    print("Task completed successfully")
```

---

## Stop Hook Integration

The Ralph Wiggum loop works with Claude Code Stop hooks. Add to
`.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/check_loop_complete.py"
          }
        ]
      }
    ]
  }
}
```

`scripts/check_loop_complete.py` reads the Claude output, checks for
`<promise>TASK_COMPLETE</promise>`, and returns exit code 0 (allow stop)
or exit code 2 (block stop and re-inject prompt).

```python
#!/usr/bin/env python3
"""
Stop hook for Ralph Wiggum loop.
Reads Claude's last output from stdin (JSON).
Returns 0 to allow exit, 2 to block and re-inject.
"""
import json, sys

data = json.load(sys.stdin)
transcript = data.get("transcript", [])

# Check last assistant message for completion token
for msg in reversed(transcript):
    if msg.get("role") == "assistant":
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") for c in content if isinstance(c, dict)
            )
        if "<promise>TASK_COMPLETE</promise>" in content:
            sys.exit(0)  # allow exit
        break

# Not complete — block exit
print(json.dumps({
    "decision": "block",
    "reason": "Task not yet complete. Continuing loop..."
}))
sys.exit(2)
```

---

## Example Task Prompts

```powershell
# Process all pending Needs_Action items
/ralph-loop "Process every file in AI_Employee_Vault/Needs_Action/ using the process-needs-action skill. Output TASK_COMPLETE when Needs_Action is empty."

# Weekly briefing
/ralph-loop "Generate the Monday CEO briefing from Business_Goals.md and Bank_Transactions.md. Save to Briefings/. Output TASK_COMPLETE when the briefing file is written."

# LinkedIn post pipeline
/ralph-loop "Use the linkedin-post skill to draft this week's post. Wait for the approval file to appear in Approved/, then execute it via scripts/linkedin_post.py. Output TASK_COMPLETE after the post is published."

# Subscription audit
/ralph-loop "Read Bank_Transactions.md. Identify any recurring charges not listed in Business_Goals.md subscriptions. Write a report to Briefings/AUDIT_<date>.md. Output TASK_COMPLETE when the report is saved."
```

---

## Completion Signal

At task completion (or max iterations), always output exactly:

```
<promise>TASK_COMPLETE</promise>
```
