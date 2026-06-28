---
type: error
error_type: loop_max_iterations
task_prompt: "First say STEP_1_DONE. On the next invocation, output <promise>TASK_COMPLETE</promise>."
iterations_completed: 3
timestamp: "2026-06-27T10:18:23Z"
---

## Error: Max iterations (3) reached

The reasoning loop did not complete within the iteration limit.

## Task

First say STEP_1_DONE. On the next invocation, output <promise>TASK_COMPLETE</promise>.

## Recommended Action

Review the task prompt and restart with a clearer description, or increase
max iterations:

    python scripts/ralph_loop.py "First say STEP_1_DONE. On the next invocation, output <promise>TASK_COMPLETE</promise>." --max-iterations 20
