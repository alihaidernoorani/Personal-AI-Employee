"""
Ralph Wiggum Reasoning Loop
============================
Runs a task_prompt through Claude Code in a persistence loop.
Claude cannot exit until it outputs <promise>TASK_COMPLETE</promise>
or the max iteration limit is reached.

Usage:
  python scripts/ralph_loop.py "Process all emails in Needs_Action"
  python scripts/ralph_loop.py "Weekly briefing" --max-iterations 15
  python scripts/ralph_loop.py "Post to LinkedIn" --completion-promise "DONE"

The loop:
  1. Launches claude with the task prompt (non-interactive, -p flag)
  2. Streams stdout and watches for the completion promise token
  3. If token found → exits with code 0
  4. If not found and iterations remain → re-runs with continuation prompt
  5. If max iterations hit → writes ERROR file to Needs_Action/ and exits 1
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Config ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
VAULT = BASE_DIR / "AI_Employee_Vault"

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_PROMISE = "TASK_COMPLETE"
# claude CLI — use .cmd wrapper on Windows for npm-installed binaries
CLAUDE_CMD = (
    r"C:\Users\DELL\AppData\Roaming\npm\claude.cmd"
    if sys.platform == "win32"
    else "claude"
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def today_log() -> Path:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_dir = VAULT / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{date}.json"

def append_log(entry: dict):
    with open(today_log(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def write_state_file(stamp: str, task_prompt: str, iteration: int, status: str, log_lines: list[str]) -> Path:
    in_progress = VAULT / "In_Progress" / "claude_code"
    in_progress.mkdir(parents=True, exist_ok=True)
    path = in_progress / f"LOOP_{stamp}_state.md"
    content = f"""---
type: loop_state
task_prompt: {json.dumps(task_prompt)}
started_at: "{now_iso()}"
iteration: {iteration}
max_iterations: {DEFAULT_MAX_ITERATIONS}
status: {status}
---

## Task

{task_prompt}

## Iteration Log

{"".join(f"- {line}\\n" for line in log_lines)}
"""
    path.write_text(content, encoding="utf-8")
    return path

def write_error_file(stamp: str, task_prompt: str, iterations: int, reason: str):
    needs_action = VAULT / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)
    path = needs_action / f"ERROR_{stamp}_loop-max-iterations.md"
    path.write_text(f"""---
type: error
error_type: loop_max_iterations
task_prompt: {json.dumps(task_prompt)}
iterations_completed: {iterations}
timestamp: "{now_iso()}"
---

## Error: {reason}

The reasoning loop did not complete within the iteration limit.

## Task

{task_prompt}

## Recommended Action

Review the task prompt and restart with a clearer description, or increase
max iterations:

    python scripts/ralph_loop.py "{task_prompt}" --max-iterations 20
""", encoding="utf-8")
    print(f"[ralph_loop] ERROR file written: {path.name}", flush=True)

def run_claude(prompt: str, verbose: bool) -> tuple[str, int]:
    """Run claude -p <prompt> and return (full_output, exit_code)."""
    cmd = [CLAUDE_CMD, "-p", prompt, "--permission-mode", "bypassPermissions"]
    print(f"\n[ralph_loop] Running: {' '.join(cmd[:2])} \"<prompt>\"", flush=True)
    output_lines = []
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            output_lines.append(line)
            if verbose:
                print(line, end="", flush=True)
            else:
                # Always print lines containing the promise token
                if "promise>" in line or "[ralph_loop]" in line:
                    print(line, end="", flush=True)
        proc.wait()
        return "".join(output_lines), proc.returncode
    except FileNotFoundError:
        print(f"[ralph_loop] ERROR: '{CLAUDE_CMD}' not found on PATH.", flush=True)
        sys.exit(1)

# ── Main loop ──────────────────────────────────────────────────────────────────

def ralph_loop(task_prompt: str, max_iterations: int, completion_promise: str, verbose: bool):
    stamp = now_stamp()
    log_lines = []
    found = False
    previous_output = ""

    print(f"[ralph_loop] Starting - task: {task_prompt[:80]}", flush=True)
    print(f"[ralph_loop] Max iterations: {max_iterations}  |  Promise: <promise>{completion_promise}</promise>", flush=True)

    for iteration in range(1, max_iterations + 1):
        print(f"\n[ralph_loop] -- Iteration {iteration}/{max_iterations} --", flush=True)

        # First iteration uses the raw task prompt.
        # Subsequent iterations re-inject the prompt AND include previous output
        # so Claude can see what it did and pick up where it left off.
        if iteration == 1:
            prompt = task_prompt
        else:
            prev_snippet = previous_output.strip()[-2000:] if previous_output.strip() else "(no output)"
            prompt = (
                f"{task_prompt}\n\n"
                f"[LOOP CONTINUATION - iteration {iteration}/{max_iterations}]\n"
                f"Your previous attempt did not output <promise>{completion_promise}</promise>.\n"
                f"Previous output (last 2000 chars):\n---\n{prev_snippet}\n---\n\n"
                f"Continue working on the task. Output <promise>{completion_promise}</promise> "
                f"only when the task is fully complete."
            )

        output, rc = run_claude(prompt, verbose)
        previous_output = output

        token = f"<promise>{completion_promise}</promise>"
        if token in output:
            log_lines.append(f"Iteration {iteration} completed at {now_iso()}: PROMISE FOUND — task complete")
            found = True
            print(f"\n[ralph_loop] Promise token detected. Task complete after {iteration} iteration(s).", flush=True)
            break

        summary = output.strip().splitlines()[-1][:120] if output.strip() else "(no output)"
        log_lines.append(f"Iteration {iteration} completed at {now_iso()}: {summary}")
        print(f"[ralph_loop] Promise not found in iteration {iteration}. Continuing...", flush=True)

    # ── Write state file ────────────────────────────────────────────────────────
    status = "completed" if found else "max_iterations_reached"
    state_path = write_state_file(stamp, task_prompt, iteration, status, log_lines)

    if found:
        # Move state file to Done/
        done_dir = VAULT / "Done"
        done_dir.mkdir(parents=True, exist_ok=True)
        done_path = done_dir / f"DONE_LOOP_{stamp}_state.md"
        state_path.rename(done_path)

        append_log({
            "timestamp": now_iso(),
            "action_type": "reasoning_loop_complete",
            "actor": "ralph_loop.py",
            "target": "loop",
            "parameters": {
                "task_prompt": task_prompt,
                "iterations": iteration,
                "state_file": done_path.name,
            },
            "approval_status": "auto",
            "approved_by": "system",
            "result": "success",
        })
        print(f"[ralph_loop] State saved to: {done_path.name}", flush=True)
        sys.exit(0)

    else:
        write_error_file(stamp, task_prompt, iteration, f"Max iterations ({max_iterations}) reached")
        append_log({
            "timestamp": now_iso(),
            "action_type": "reasoning_loop_failed",
            "actor": "ralph_loop.py",
            "target": "loop",
            "parameters": {
                "task_prompt": task_prompt,
                "iterations": iteration,
            },
            "approval_status": "auto",
            "approved_by": "system",
            "result": "failure",
        })
        sys.exit(1)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum reasoning loop — runs a task until Claude promises completion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ralph_loop.py "Process all emails in Needs_Action"
  python scripts/ralph_loop.py "Generate weekly briefing" --max-iterations 15
  python scripts/ralph_loop.py "Post to LinkedIn" --completion-promise "DONE" --verbose
""",
    )
    parser.add_argument("task_prompt", help="Task description for Claude to execute")
    parser.add_argument(
        "--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS,
        metavar="N", help=f"Max loop iterations before giving up (default: {DEFAULT_MAX_ITERATIONS})"
    )
    parser.add_argument(
        "--completion-promise", default=DEFAULT_PROMISE,
        metavar="TOKEN", help=f"Promise token to detect in output (default: {DEFAULT_PROMISE})"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Stream all Claude output to stdout (default: only promise lines)"
    )

    args = parser.parse_args()

    if not args.task_prompt.strip():
        parser.error("task_prompt cannot be empty")

    ralph_loop(
        task_prompt=args.task_prompt,
        max_iterations=args.max_iterations,
        completion_promise=args.completion_promise,
        verbose=args.verbose,
    )
