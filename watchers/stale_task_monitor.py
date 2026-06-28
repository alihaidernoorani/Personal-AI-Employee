"""stale_task_monitor.py — Stale task recovery for Platinum multi-agent coordination.

Monitors In_Progress/<monitored_agent>/ for files that have not moved within
STALE_TASK_TIMEOUT_SECONDS. Moves stale files back to Needs_Action/ and writes
a SIGNAL_task_recovered signal.

Run on each machine monitoring the OTHER agent's In_Progress/ subdirectory:
  - Cloud instance monitors In_Progress/local/
  - Local instance monitors In_Progress/cloud/
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    str(Path(__file__).parent.parent / "AI_Employee_Vault"),
)
AGENT_ROLE = os.environ.get("AGENT_ROLE", "local")
STALE_TASK_TIMEOUT_SECONDS = int(os.environ.get("STALE_TASK_TIMEOUT_SECONDS", "600"))
CHECK_INTERVAL_SECONDS = 120

# Local monitors cloud; cloud monitors local
MONITORED_AGENT = "cloud" if AGENT_ROLE == "local" else "local"
PROCESSED_FILE = Path(__file__).parent.parent / "scripts" / "processed_recovered.json"


def _load_recovered_ids() -> set:
    if PROCESSED_FILE.exists():
        try:
            return set(json.loads(PROCESSED_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def _save_recovered_ids(ids: set) -> None:
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_FILE.write_text(json.dumps(sorted(ids)), encoding="utf-8")


def _write_recovery_signal(vault_path: Path, task_filename: str) -> None:
    """Write SIGNAL_task_recovered_<ts>.md to Signals/ directory."""
    from watchers.cloud_boundary import safe_vault_write

    signals_dir = vault_path / "_System" / "Signals"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    signal_file = signals_dir / f"SIGNAL_task_recovered_{ts}.md"
    content = (
        f"---\n"
        f"signal_type: task_recovered\n"
        f"severity: warning\n"
        f"created: {datetime.now(timezone.utc).isoformat()}Z\n"
        f"agent_id: stale_task_monitor\n"
        f"requires_human_action: false\n"
        f"recovered_task: {task_filename}\n"
        f"monitored_agent: {MONITORED_AGENT}\n"
        f"---\n\n"
        f"# Stale Task Recovered\n\n"
        f"Task `{task_filename}` was stale in `In_Progress/{MONITORED_AGENT}/` "
        f"and has been returned to `Needs_Action/`.\n\n"
        f"The `{MONITORED_AGENT}` agent may have crashed mid-task.\n"
    )
    safe_vault_write(signal_file, content, vault_path)
    logger.info(f"Recovery signal written: {signal_file.name}")


def _check_stale_tasks(vault_path: Path) -> int:
    """Scan monitored In_Progress/ subdirectory and recover stale tasks.

    Returns number of tasks recovered.
    """
    monitored_dir = vault_path / "_System" / "In_Progress" / MONITORED_AGENT
    needs_action_dir = vault_path / "_System" / "Needs_Action"

    if not monitored_dir.exists():
        return 0

    recovered_ids = _load_recovered_ids()
    now = time.time()
    recovered_count = 0

    for task_file in monitored_dir.iterdir():
        if not task_file.is_file() or task_file.name == ".gitkeep":
            continue

        file_id = task_file.name
        if file_id in recovered_ids:
            continue

        age_seconds = now - task_file.stat().st_mtime
        if age_seconds <= STALE_TASK_TIMEOUT_SECONDS:
            continue

        logger.warning(
            f"Stale task detected: {task_file.name} "
            f"(age={int(age_seconds)}s, threshold={STALE_TASK_TIMEOUT_SECONDS}s)"
        )

        try:
            dest = needs_action_dir / task_file.name
            needs_action_dir.mkdir(parents=True, exist_ok=True)
            task_file.rename(dest)
            _write_recovery_signal(vault_path, task_file.name)
            recovered_ids.add(file_id)
            _save_recovered_ids(recovered_ids)
            recovered_count += 1
            logger.info(f"Recovered stale task: {task_file.name} → Needs_Action/")
        except OSError as e:
            logger.error(f"Could not recover task {task_file.name}: {e}")

    return recovered_count


def run(vault_path: str | None = None) -> None:
    """Main stale task monitor loop. Blocks indefinitely."""
    vault = Path(vault_path or VAULT_PATH)
    logger.info(
        f"Stale task monitor started (monitoring In_Progress/{MONITORED_AGENT}/, "
        f"interval={CHECK_INTERVAL_SECONDS}s, timeout={STALE_TASK_TIMEOUT_SECONDS}s)"
    )

    while True:
        try:
            count = _check_stale_tasks(vault)
            if count:
                logger.info(f"Recovered {count} stale task(s)")
        except Exception as e:
            logger.error(f"Stale task check failed: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [StaleTaskMonitor] %(levelname)s: %(message)s",
    )
    run()
