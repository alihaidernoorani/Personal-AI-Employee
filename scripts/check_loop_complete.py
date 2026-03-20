"""
Ralph Wiggum Stop Hook
======================
Claude Code Stop hook: blocks Claude from exiting until the promise token
is present in the last assistant message.

Configure in .claude/settings.json:
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

Exit codes:
  0  — allow exit (task complete or no loop active)
  2  — block exit (task not yet complete, loop continues)

The hook reads JSON from stdin with the session transcript.
It checks if the last assistant message contains <promise>TASK_COMPLETE</promise>.
If not found, it blocks exit and prints a re-injection message.
"""

import json
import sys
from pathlib import Path

PROMISE_TOKEN = "<promise>TASK_COMPLETE</promise>"
VAULT = Path(__file__).parent.parent / "AI_Employee_Vault"


def last_assistant_text(transcript: list) -> str:
    """Return the text content of the most recent assistant message."""
    for msg in reversed(transcript):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
    return ""


def loop_is_active() -> bool:
    """Return True if a LOOP_* state file exists in In_Progress/claude_code/."""
    in_progress = VAULT / "In_Progress" / "claude_code"
    if not in_progress.exists():
        return False
    return any(in_progress.glob("LOOP_*_state.md"))


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # If we can't read stdin, allow exit (don't block)
        sys.exit(0)

    transcript = data.get("transcript", [])

    # If no active loop state file, allow exit normally
    if not loop_is_active():
        sys.exit(0)

    last_text = last_assistant_text(transcript)

    if PROMISE_TOKEN in last_text:
        # Task complete — allow Claude to exit
        sys.exit(0)

    # Task not complete — block exit and instruct Claude to continue
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"Ralph Wiggum loop active. Task not yet complete — "
            f"{PROMISE_TOKEN} not found in output. "
            f"Continue working on the task and output {PROMISE_TOKEN} when done."
        )
    }))
    sys.exit(2)


if __name__ == "__main__":
    main()
