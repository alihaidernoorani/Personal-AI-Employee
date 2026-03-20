"""process_supervisor.py — Process manager for the AI Employee orchestrator.

Monitors orchestrator.py and restarts it automatically if it crashes.
Works on Windows (no fork/systemd required).

Usage:
    python process_supervisor.py                  # default: restart orchestrator with default watchers
    python process_supervisor.py --watcher all    # pass --watcher all to orchestrator
    python process_supervisor.py --watcher gmail_api  # restart Gmail API watcher only
    python process_supervisor.py --check-interval 30  # check every 30 seconds (default: 60)

Environment variables (loaded from .env):
    VAULT_PATH  — passed through to orchestrator
    DRY_RUN     — passed through to orchestrator
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Watchdog] %(levelname)s: %(message)s",
)
logger = logging.getLogger("Watchdog")

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    str(Path(__file__).parent / "AI_Employee_Vault"),
)
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

ORCHESTRATOR = Path(__file__).parent / "orchestrator.py"
MAX_RESTARTS = 10          # stop trying after this many consecutive crashes
RESTART_WINDOW = 300       # seconds — resets the restart counter if stable this long


def _log_event(action_type: str, result: str, extra: dict | None = None) -> None:
    """Append a NDJSON audit entry to Logs/YYYY-MM-DD.json."""
    try:
        log_dir = Path(VAULT_PATH) / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type,
            "actor": "watchdog",
            "target": "orchestrator",
            "parameters": extra or {},
            "approval_status": "auto",
            "approved_by": "system",
            "result": result,
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.error(f"Failed to write log entry: {exc}")


def _write_error_file(message: str) -> None:
    """Write an ERROR_*.md to Needs_Action/ so Claude can surface it."""
    try:
        needs_action = Path(VAULT_PATH) / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = needs_action / f"ERROR_{ts}_watchdog-max-restarts.md"
        path.write_text(
            f"---\ntype: error\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n"
            f"priority: high\nstatus: pending\n---\n\n"
            f"## Watchdog: Max Restarts Reached\n\n{message}\n\n"
            f"Manual intervention required. Check orchestrator logs and restart manually.\n",
            encoding="utf-8",
        )
        logger.error(f"Error file written: {path.name}")
    except Exception as exc:
        logger.error(f"Failed to write error file: {exc}")


def _build_command(watcher_arg: str | None) -> list[str]:
    """Build the subprocess command for orchestrator.py."""
    python = sys.executable
    cmd = [python, str(ORCHESTRATOR)]
    if watcher_arg:
        cmd += ["--watcher", watcher_arg]
    return cmd


def run(watcher_arg: str | None, check_interval: int) -> None:
    """Main watchdog loop."""
    cmd = _build_command(watcher_arg)
    env = os.environ.copy()
    env["VAULT_PATH"] = VAULT_PATH

    logger.info(f"Watchdog starting. Command: {' '.join(cmd)}")
    logger.info(f"Check interval: {check_interval}s | Max restarts: {MAX_RESTARTS}")

    restarts = 0
    last_stable_time = time.monotonic()
    process: subprocess.Popen | None = None

    def _shutdown(signum, frame):
        logger.info("Watchdog shutting down (signal received)")
        if process and process.poll() is None:
            process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        # Start orchestrator if not running
        if process is None or process.poll() is not None:
            exit_code = process.poll() if process else None

            # Reset restart counter if the process was stable long enough
            elapsed = time.monotonic() - last_stable_time
            if elapsed >= RESTART_WINDOW:
                if restarts > 0:
                    logger.info(
                        f"Process was stable for {elapsed:.0f}s — resetting restart counter"
                    )
                restarts = 0

            if exit_code is not None:
                logger.warning(
                    f"Orchestrator exited with code {exit_code}. "
                    f"Restart #{restarts + 1}/{MAX_RESTARTS}"
                )
                _log_event(
                    "orchestrator_restart",
                    "restarting",
                    {"exit_code": exit_code, "restart_count": restarts + 1},
                )
                restarts += 1

            if restarts > MAX_RESTARTS:
                msg = (
                    f"Orchestrator crashed {restarts} times in {RESTART_WINDOW}s. "
                    f"Giving up to avoid a crash loop."
                )
                logger.error(msg)
                _log_event("watchdog_abort", "failure", {"reason": msg})
                _write_error_file(msg)
                sys.exit(1)

            logger.info(f"Starting orchestrator: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, env=env)
            last_stable_time = time.monotonic()
            _log_event("orchestrator_start", "started", {"pid": process.pid})

        time.sleep(check_interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Employee Watchdog")
    parser.add_argument(
        "--watcher",
        choices=["filesystem", "gmail", "gmail_api", "whatsapp", "approval", "all"],
        default=None,
        help="--watcher flag passed through to orchestrator.py (default: orchestrator default)",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=60,
        help="Seconds between process health checks (default: 60)",
    )
    args = parser.parse_args()

    if not Path(VAULT_PATH).exists():
        logger.error(f"Vault not found: {VAULT_PATH}")
        sys.exit(1)

    run(args.watcher, args.check_interval)


if __name__ == "__main__":
    main()
