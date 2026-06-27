"""signals_watcher.py — Cross-agent signal monitor.

Polls AI_Employee_Vault/Signals/ every 60 seconds for new SIGNAL_*.md files.
Routes each signal by type per signals-protocol.md routing table.
Marks processed signals in scripts/processed_signals.json (permanent, never deleted).
Runs on both local and cloud machines.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    str(Path(__file__).parent.parent / "AI_Employee_Vault"),
)
AGENT_ROLE = os.environ.get("AGENT_ROLE", "local")
CHECK_INTERVAL_SECONDS = 60
PROCESSED_FILE = Path(__file__).parent.parent / "scripts" / "processed_signals.json"


def _load_processed_ids() -> set:
    if PROCESSED_FILE.exists():
        try:
            return set(json.loads(PROCESSED_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def _save_processed_ids(ids: set) -> None:
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_FILE.write_text(json.dumps(sorted(ids)), encoding="utf-8")


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a signal file."""
    if not content.startswith("---"):
        return {}
    try:
        end = content.index("---", 3)
        return yaml.safe_load(content[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}


def _write_needs_action_error(vault_path: Path, slug: str, message: str) -> None:
    from watchers.cloud_boundary import safe_vault_write
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"ERROR_{slug}_{ts}.md"
    target = vault_path / "Needs_Action" / fname
    safe_vault_write(
        target,
        f"---\ntype: error\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n---\n\n"
        f"# Error: {slug}\n\n{message}\n",
        vault_path,
    )
    logger.warning(f"Error file written to Needs_Action: {fname}")


def _write_needs_action_task(vault_path: Path, fname: str, content: str) -> None:
    from watchers.cloud_boundary import safe_vault_write
    target = vault_path / "Needs_Action" / fname
    safe_vault_write(target, content, vault_path)
    logger.info(f"Task written to Needs_Action: {fname}")


def _route_signal(signal_type: str, meta: dict, signal_file: Path, vault_path: Path) -> None:
    """Route a signal to the appropriate local or cloud response."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if signal_type == "cloud_down" and AGENT_ROLE == "local":
        _write_needs_action_error(
            vault_path, "CLOUD_AGENT_DOWN",
            f"Cloud agent heartbeat absent. Last heartbeat from signal: "
            f"{meta.get('created', 'unknown')}.\n\n"
            "SSH to cloud VM and verify cloud_orchestrator.py is running."
        )

    elif signal_type == "sync_conflict" and AGENT_ROLE == "local":
        _write_needs_action_task(
            vault_path,
            f"SYNC_CONFLICT_{ts}.md",
            f"---\ntype: sync_conflict\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n"
            f"signal_ref: {signal_file.name}\n---\n\n"
            f"# Sync Conflict Detected\n\nA sync conflict was flagged in the vault.\n"
            f"Review `.sync-conflict-*` files and resolve manually.\n"
        )

    elif signal_type == "single_writer_violation":
        slug = "SINGLE_WRITER_VIOLATION"
        _write_needs_action_error(
            vault_path, slug,
            f"Cloud agent attempted to write to a prohibited vault path.\n"
            f"Signal file: {signal_file.name}\n\n"
            "Investigate cloud-side code immediately. The write was blocked."
        )

    elif signal_type == "disk_alert" and AGENT_ROLE == "local":
        _write_needs_action_error(
            vault_path, "DISK_ALERT",
            f"Cloud VM disk usage exceeded 80%. Source: {signal_file.name}.\n\n"
            "Log into cloud VM and free disk space."
        )

    elif signal_type == "plan_ready" and AGENT_ROLE == "local":
        linked_ref = meta.get("linked_ref") or meta.get("task_ref", "")
        logger.info(
            f"plan_ready signal received — local agent should process task: {linked_ref}"
        )

    elif signal_type == "compliance_fail" and AGENT_ROLE == "local":
        _write_needs_action_task(
            vault_path,
            f"COMPLIANCE_FAIL_{ts}.md",
            f"---\ntype: compliance_fail\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n"
            f"signal_ref: {signal_file.name}\n---\n\n"
            f"# Compliance Check Failure\n\n"
            f"Constitution check detected a FAIL principle. Review "
            f"`Briefings/COMPLIANCE_REPORT_*.md` for details.\n"
        )

    elif signal_type == "shutdown_request" and AGENT_ROLE == "cloud":
        logger.warning("shutdown_request signal received — cloud orchestrator should initiate graceful shutdown")

    else:
        logger.debug(f"Signal {signal_type} on AGENT_ROLE={AGENT_ROLE}: log only")


def _check_signals(vault_path: Path) -> int:
    """Scan Signals/ for new signal files and route each. Returns count processed."""
    signals_dir = vault_path / "Signals"
    if not signals_dir.exists():
        return 0

    processed_ids = _load_processed_ids()
    count = 0

    for signal_file in sorted(signals_dir.glob("SIGNAL_*.md")):
        signal_id = signal_file.name
        if signal_id in processed_ids:
            continue

        try:
            content = signal_file.read_text(encoding="utf-8")
            meta = _parse_frontmatter(content)
            signal_type = meta.get("signal_type", "unknown")
            logger.info(f"Processing signal: {signal_id} (type={signal_type})")
            _route_signal(signal_type, meta, signal_file, vault_path)
            processed_ids.add(signal_id)
            count += 1
        except Exception as e:
            logger.error(f"Error processing signal {signal_id}: {e}")

    if count:
        _save_processed_ids(processed_ids)

    return count


def run(vault_path: str | None = None) -> None:
    """Main signals watcher loop. Blocks indefinitely."""
    vault = Path(vault_path or VAULT_PATH)
    logger.info(
        f"Signals watcher started (AGENT_ROLE={AGENT_ROLE}, interval={CHECK_INTERVAL_SECONDS}s)"
    )

    while True:
        try:
            count = _check_signals(vault)
            if count:
                logger.info(f"Processed {count} new signal(s)")
        except Exception as e:
            logger.error(f"Signal check failed: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [SignalsWatcher] %(levelname)s: %(message)s",
    )
    run()
