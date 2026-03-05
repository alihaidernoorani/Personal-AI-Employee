"""orchestrator.py — Bronze-tier launcher for the AI Employee.

Starts the filesystem watcher in the background so Claude Code can be
pointed at the vault and process items as they appear in Needs_Action/.

Usage:
    python orchestrator.py

Environment variables (see .env.example):
    VAULT_PATH   — absolute path to AI_Employee_Vault (default: ./AI_Employee_Vault)
    DRY_RUN      — set to 'true' to log actions without executing (default: true)
"""

import os
import sys
import logging
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


def main():
    logger.info(f"AI Employee Orchestrator starting (Bronze tier)")
    logger.info(f"Vault path : {VAULT_PATH}")
    logger.info(f"Dry-run    : {DRY_RUN}")

    if not Path(VAULT_PATH).exists():
        logger.error(f"Vault not found at: {VAULT_PATH}")
        logger.error("Create the vault first or set VAULT_PATH in your .env file.")
        sys.exit(1)

    # Import here so missing deps surface cleanly
    sys.path.insert(0, str(Path(__file__).parent / "watchers"))
    from filesystem_watcher import FilesystemWatcher

    logger.info("Starting filesystem watcher — drop files into AI_Employee_Vault/Inbox/")
    logger.info("Press Ctrl+C to stop.")

    watcher = FilesystemWatcher(VAULT_PATH)
    watcher.run()


if __name__ == "__main__":
    main()
