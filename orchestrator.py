"""orchestrator.py — Silver-tier launcher for the AI Employee.

Starts watchers as background/foreground processes. Supports selective
watcher launch via --watcher flag and cron-mode logging via --cron flag.

Usage:
    python orchestrator.py                          # default: filesystem + approval + whatsapp
    python orchestrator.py --watcher gmail --cron   # cron-triggered Gmail poll
    python orchestrator.py --watcher whatsapp       # WhatsApp daemon only
    python orchestrator.py --watcher approval       # Approval watcher only
    python orchestrator.py --watcher all            # all watchers

Environment variables (see .env.example):
    VAULT_PATH           — absolute path to AI_Employee_Vault (default: ./AI_Employee_Vault)
    DRY_RUN              — set to 'true' to log actions without executing (default: true)
    GMAIL_EMAIL          — Gmail address for GmailWatcher
    GMAIL_APP_PASSWORD   — Gmail App Password (16-char string from Google Account > Security)
"""

import argparse
import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Orchestrator] %(levelname)s: %(message)s",
)
logger = logging.getLogger("Orchestrator")

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    str(Path(__file__).parent / "AI_Employee_Vault"),
)
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"


def _write_cron_log_entry() -> None:
    """Write actor: scheduler NDJSON entry to Logs/YYYY-MM-DD.json (FR-020)."""
    try:
        log_dir = Path(VAULT_PATH) / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": "watcher_start",
            "actor": "scheduler",
            "target": "orchestrator",
            "parameters": {},
            "approval_status": "auto",
            "approved_by": "system",
            "result": "started",
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info("Cron log entry written (actor: scheduler)")
    except Exception as e:
        logger.error(f"Failed to write cron log entry: {e}")


def _start_watcher_thread(watcher_instance, name: str) -> threading.Thread:
    """Start a watcher in a daemon thread and return the thread."""
    t = threading.Thread(target=watcher_instance.run, name=name, daemon=True)
    t.start()
    logger.info(f"Started watcher thread: {name}")
    return t


def main():
    parser = argparse.ArgumentParser(
        description="AI Employee Orchestrator — Silver Tier"
    )
    parser.add_argument(
        "--watcher",
        choices=["filesystem", "gmail", "whatsapp", "approval", "all"],
        default=None,
        help="Which watcher(s) to start. Default: filesystem + approval + whatsapp.",
    )
    parser.add_argument(
        "--cron",
        action="store_true",
        default=False,
        help="Indicate this run was triggered by cron. Writes actor:scheduler log entry.",
    )
    args = parser.parse_args()

    logger.info("AI Employee Orchestrator starting (Silver tier)")
    logger.info(f"Vault path : {VAULT_PATH}")
    logger.info(f"Dry-run    : {DRY_RUN}")

    if not Path(VAULT_PATH).exists():
        logger.error(f"Vault not found at: {VAULT_PATH}")
        logger.error("Create the vault first or set VAULT_PATH in your .env file.")
        sys.exit(1)

    # Write scheduler log entry when --cron flag is passed
    if args.cron:
        _write_cron_log_entry()

    # Import watchers — defer imports so missing deps surface clearly
    sys.path.insert(0, str(Path(__file__).parent))

    from watchers.filesystem_watcher import FilesystemWatcher

    try:
        from watchers.gmail_watcher import GmailWatcher
    except ImportError as e:
        logger.warning(f"GmailWatcher not available: {e}")
        GmailWatcher = None

    try:
        from watchers.whatsapp_watcher import WhatsAppWatcher
    except ImportError as e:
        logger.warning(f"WhatsAppWatcher not available: {e}")
        WhatsAppWatcher = None

    try:
        from watchers.approval_watcher import ApprovalWatcher
    except ImportError as e:
        logger.warning(f"ApprovalWatcher not available: {e}")
        ApprovalWatcher = None

    # Determine which watchers to start
    selected = args.watcher

    threads = []

    if selected == "gmail":
        # Gmail watcher — typically invoked by cron every 5 minutes
        if GmailWatcher is None:
            logger.error("GmailWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting GmailWatcher (5-min poll)")
        watcher = GmailWatcher(VAULT_PATH)
        watcher.run()  # Run in foreground for cron invocations

    elif selected == "whatsapp":
        # WhatsApp daemon — persistent, blocks until Ctrl+C
        if WhatsAppWatcher is None:
            logger.error("WhatsAppWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting WhatsAppWatcher (persistent 60s daemon)")
        watcher = WhatsAppWatcher(VAULT_PATH)
        watcher.run()

    elif selected == "approval":
        # Approval watcher only
        if ApprovalWatcher is None:
            logger.error("ApprovalWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting ApprovalWatcher (5s poll)")
        watcher = ApprovalWatcher(VAULT_PATH)
        watcher.run()

    elif selected == "filesystem":
        # Filesystem watcher only
        logger.info("Starting FilesystemWatcher")
        watcher = FilesystemWatcher(VAULT_PATH)
        watcher.run()

    else:
        # Default (no --watcher flag, or --watcher all):
        # Start FilesystemWatcher + ApprovalWatcher + WhatsAppWatcher
        logger.info("Starting default watchers: FilesystemWatcher + ApprovalWatcher + WhatsAppWatcher")
        logger.info("Press Ctrl+C to stop.")

        # FilesystemWatcher in a thread
        fs_watcher = FilesystemWatcher(VAULT_PATH)
        threads.append(_start_watcher_thread(fs_watcher, "FilesystemWatcher"))

        # ApprovalWatcher in a thread (if available)
        if ApprovalWatcher is not None:
            approval_watcher = ApprovalWatcher(VAULT_PATH)
            threads.append(_start_watcher_thread(approval_watcher, "ApprovalWatcher"))
        else:
            logger.warning("ApprovalWatcher unavailable — skipping")

        # WhatsAppWatcher in a thread (if available)
        if WhatsAppWatcher is not None:
            wa_watcher = WhatsAppWatcher(VAULT_PATH)
            threads.append(_start_watcher_thread(wa_watcher, "WhatsAppWatcher"))
        else:
            logger.warning("WhatsAppWatcher unavailable — skipping")

        # Keep main thread alive
        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            logger.info("Orchestrator shutting down (Ctrl+C)")


if __name__ == "__main__":
    main()
