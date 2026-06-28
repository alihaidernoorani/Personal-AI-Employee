"""cloud_boundary.py — Security boundary guard for cloud agent vault writes.

Cloud agents are restricted from writing to authoritative local folders.
All vault writes from cloud-side code MUST go through safe_vault_write().
Any attempt to write to a prohibited path is blocked and logged as a signal.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths the cloud agent must never write to (relative to VAULT_PATH).
# Operational folders now live under _System/ (vault redesign 2026-06-28).
# Violations produce a SINGLE_WRITER_VIOLATION signal and raise PermissionError.
PROHIBITED_CLOUD_WRITE_PATHS: list[str] = [
    "Dashboard.md",
    "_System/Done",
    "_System/Approved",
    "_System/Rejected",
]


def _is_prohibited(path: Path, vault_path: Path) -> bool:
    """Return True if path falls under any prohibited vault location."""
    try:
        rel = path.resolve().relative_to(vault_path.resolve())
    except ValueError:
        return False
    rel_posix = rel.as_posix()
    for prohibited in PROHIBITED_CLOUD_WRITE_PATHS:
        if rel_posix == prohibited or rel_posix.startswith(prohibited + "/"):
            return True
    return False


def _write_violation_signal(vault_path: Path, attempted_path: str) -> None:
    """Write a SINGLE_WRITER_VIOLATION signal to Signals/ directory."""
    signals_dir = vault_path / "_System" / "Signals"
    signals_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    signal_file = signals_dir / f"SINGLE_WRITER_VIOLATION_{ts}.md"
    content = (
        f"---\n"
        f"signal_type: single_writer_violation\n"
        f"severity: critical\n"
        f"created: {datetime.now(timezone.utc).isoformat()}Z\n"
        f"agent_id: cloud_agent\n"
        f"requires_human_action: true\n"
        f"---\n\n"
        f"# Single Writer Violation\n\n"
        f"Cloud agent attempted to write to a prohibited vault path:\n\n"
        f"**Path**: `{attempted_path}`\n\n"
        f"The write was blocked. Investigate cloud-side code immediately.\n"
    )
    try:
        signal_file.write_text(content, encoding="utf-8")
        logger.error(f"Single writer violation signal written: {signal_file.name}")
    except OSError as e:
        logger.critical(f"Could not write violation signal: {e}")


def safe_vault_write(path: str | Path, content: str, vault_path: str | Path | None = None) -> None:
    """Write content to path after verifying it is not in a prohibited location.

    Args:
        path: Absolute or vault-relative path to write.
        content: File content to write.
        vault_path: Override vault root. Falls back to VAULT_PATH env var.

    Raises:
        PermissionError: If path is in PROHIBITED_CLOUD_WRITE_PATHS.
    """
    if vault_path is None:
        vault_path = os.environ.get("VAULT_PATH", str(Path(__file__).parent.parent / "AI_Employee_Vault"))
    vault_root = Path(vault_path)
    target = Path(path)

    if _is_prohibited(target, vault_root):
        _write_violation_signal(vault_root, str(target))
        raise PermissionError(
            f"Cloud agent write blocked: '{target}' is in PROHIBITED_CLOUD_WRITE_PATHS. "
            "Only the local agent may write to this location."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    logger.debug(f"safe_vault_write: wrote {target}")


def check_sync_health(vault_path: str | Path, max_lag_seconds: int = 600) -> bool:
    """Check Sync/sync.log recency; write SYNC_STALLED signal if lagging.

    Args:
        vault_path: Root of the Obsidian vault.
        max_lag_seconds: Maximum acceptable lag before raising a stall signal.

    Returns:
        True if sync is healthy; False if stalled.
    """
    vault_root = Path(vault_path)
    sync_log = vault_root / "_System" / "Sync" / "sync.log"

    if not sync_log.exists():
        logger.warning("sync.log not found — cannot assess sync health")
        return False

    lines = sync_log.read_text(encoding="utf-8").splitlines()
    data_lines = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    if not data_lines:
        logger.warning("sync.log has no data entries")
        return False

    last_line = data_lines[-1]
    try:
        # Format: timestamp|direction|file_path|size_bytes|machine_id|sync_lag_seconds
        parts = last_line.split("|")
        if len(parts) < 1:
            raise ValueError("Unexpected sync.log format")
        last_ts_str = parts[0].strip()
        last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
    except (ValueError, IndexError) as e:
        logger.error(f"Could not parse sync.log last entry: {e}")
        return False

    now = datetime.now(timezone.utc)
    lag = (now - last_ts).total_seconds()

    if lag > max_lag_seconds:
        signals_dir = vault_root / "_System" / "Signals"
        signals_dir.mkdir(parents=True, exist_ok=True)
        ts = now.strftime("%Y%m%dT%H%M%SZ")
        signal_file = signals_dir / f"SYNC_STALLED_{ts}.md"
        content = (
            f"---\n"
            f"signal_type: sync_stalled\n"
            f"severity: warning\n"
            f"created: {now.isoformat()}Z\n"
            f"agent_id: cloud_agent\n"
            f"requires_human_action: false\n"
            f"lag_seconds: {int(lag)}\n"
            f"---\n\n"
            f"# Vault Sync Stalled\n\n"
            f"No sync activity detected for **{int(lag)} seconds** (threshold: {max_lag_seconds}s).\n\n"
            f"Last sync.log entry: `{last_ts_str}`\n\n"
            f"Check Syncthing daemon status on both machines.\n"
        )
        signal_file.write_text(content, encoding="utf-8")
        logger.warning(f"Sync stalled signal written (lag={int(lag)}s): {signal_file.name}")
        return False

    logger.debug(f"Sync health OK (lag={int(lag)}s)")
    return True
