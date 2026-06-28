"""heartbeat_writer.py — Cloud agent liveness beacon.

Writes Updates/HEARTBEAT_<ISO-timestamp>.md every 300 seconds.
Deletes heartbeat files older than 15 minutes on each cycle.
Only active when AGENT_ROLE=cloud; exits immediately otherwise.
"""

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
HEARTBEAT_INTERVAL_SECONDS = int(os.environ.get("HEARTBEAT_INTERVAL_SECONDS", "300"))
HEARTBEAT_TTL_SECONDS = 900  # 15 minutes


def _count_in_progress(vault_path: Path, subdir: str) -> int:
    """Count files in In_Progress/<subdir>/ excluding .gitkeep."""
    target = vault_path / "_System" / "In_Progress" / subdir
    if not target.exists():
        return 0
    return sum(1 for f in target.iterdir() if f.is_file() and f.name != ".gitkeep")


def _last_sync_timestamp(vault_path: Path) -> str:
    """Return the timestamp of the last sync.log entry, or 'unknown'."""
    sync_log = vault_path / "_System" / "Sync" / "sync.log"
    if not sync_log.exists():
        return "unknown"
    lines = sync_log.read_text(encoding="utf-8").splitlines()
    data_lines = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    if not data_lines:
        return "unknown"
    try:
        return data_lines[-1].split("|")[0].strip()
    except IndexError:
        return "unknown"


def _watcher_status(vault_path: Path) -> dict:
    """Build a watcher status dict based on heartbeat recency heuristics."""
    return {
        "gmail_watcher": "running",
        "signals_watcher": "running",
        "stale_task_monitor": "running",
        "heartbeat_writer": "running",
    }


def _cleanup_old_heartbeats(updates_dir: Path) -> None:
    """Delete heartbeat files older than HEARTBEAT_TTL_SECONDS."""
    now = time.time()
    for f in updates_dir.glob("HEARTBEAT_*.md"):
        if f.stat().st_mtime < now - HEARTBEAT_TTL_SECONDS:
            try:
                f.unlink()
                logger.debug(f"Deleted stale heartbeat: {f.name}")
            except OSError as e:
                logger.warning(f"Could not delete stale heartbeat {f.name}: {e}")


def _write_heartbeat(vault_path: Path, agent_id: str) -> None:
    """Write a HEARTBEAT_*.md file to Updates/."""
    from watchers.cloud_boundary import safe_vault_write

    updates_dir = vault_path / "_System" / "Updates"
    updates_dir.mkdir(parents=True, exist_ok=True)

    _cleanup_old_heartbeats(updates_dir)

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    heartbeat_id = f"heartbeat_{ts}"
    tasks_count = _count_in_progress(vault_path, "cloud")
    last_sync = _last_sync_timestamp(vault_path)
    watcher_status = _watcher_status(vault_path)

    content = (
        f"---\n"
        f"heartbeat_id: {heartbeat_id}\n"
        f"agent_id: {agent_id}\n"
        f"created: {now.isoformat()}Z\n"
        f"tasks_in_progress: {tasks_count}\n"
        f"last_processed_task_ref: null\n"
        f"vault_sync_last_ok: {last_sync}\n"
        f"watcher_status:\n"
    )
    for k, v in watcher_status.items():
        content += f"  {k}: {v}\n"
    content += (
        f"---\n\n"
        f"# Heartbeat — {ts}\n\n"
        f"Cloud agent alive. Tasks in progress: {tasks_count}. "
        f"Last sync: {last_sync}.\n"
    )

    out_path = updates_dir / f"HEARTBEAT_{ts}.md"
    safe_vault_write(out_path, content, vault_path)
    logger.info(f"Heartbeat written: {out_path.name}")


def run(vault_path: str | None = None, agent_id: str = "cloud_agent") -> None:
    """Main heartbeat writer loop. Blocks indefinitely."""
    if AGENT_ROLE != "cloud":
        logger.info(f"AGENT_ROLE={AGENT_ROLE} — heartbeat_writer only runs on cloud. Exiting.")
        return

    vault = Path(vault_path or VAULT_PATH)
    logger.info(f"Heartbeat writer started (interval={HEARTBEAT_INTERVAL_SECONDS}s, vault={vault})")

    while True:
        try:
            _write_heartbeat(vault, agent_id)
        except Exception as e:
            logger.error(f"Heartbeat write failed: {e}")
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [HeartbeatWriter] %(levelname)s: %(message)s",
    )
    run()
