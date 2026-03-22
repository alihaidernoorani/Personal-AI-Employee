# Contract: Ralph Wiggum Stop Hook

**File**: `.claude/hooks/stop_hook.py` | **Hook type**: Stop (PostToolUse)
**Registered in**: `.claude/settings.json`

## Purpose
Prevents Claude Code from exiting until a task is demonstrably complete. Provides prior-iteration output context on each re-injection.

## Trigger
Fires every time Claude Code is about to exit (after completing its current response).

## State File Contract

Location: `{VAULT_PATH}/In_Progress/local_agent/TASK_{id}.state.json`

```json
{
  "prompt": "string — original task prompt",
  "iteration": 0,
  "max_iterations": 10,
  "task_file": "string — absolute path to source task file",
  "prior_output": null
}
```

## Decision Logic

```
On hook invocation:
  1. Read state file from In_Progress/local_agent/TASK_*.state.json
  2. If no state file found → allow exit (no loop active)
  3. Check: does task_file exist in Done/ ?
     YES → delete state file → exit code 0 (allow exit)
  4. Check: did Claude stdout contain <promise>TASK_COMPLETE</promise> ?
     YES → move task_file to Done/ → delete state file → exit code 0
  5. Check: iteration >= max_iterations ?
     YES → write Needs_Action/ERROR_LOOP_MAX_{id}_{timestamp}.md
           → delete state file → exit code 0
  6. Otherwise:
     → Save current Claude output as prior_output in state file
     → Increment iteration
     → Write re-injection prompt to stdout (blocks exit)
     → exit code 1 (loop continues)
```

## Re-injection Prompt Format

```
[LOOP ITERATION {N} of {MAX}]
Your previous attempt did not complete the task. Prior output:
---
{prior_output}
---
Continue the task. Do not repeat work already done above.
Task:
{original_prompt}
```

## Exit Codes
| Code | Meaning |
|---|---|
| 0 | Allow exit (task complete, max iterations, or no active loop) |
| 1 | Block exit, re-inject prompt |

## Failure Modes
- Hook script crash → Claude exits normally (fail-safe); orchestrator watchdog writes `ERROR_HOOK_CRASH.md`
- State file unreadable → allow exit, write `ERROR_HOOK_STATE.md`
- `Done/` folder inaccessible → treat as "not done"; increment and re-inject (safe default)
