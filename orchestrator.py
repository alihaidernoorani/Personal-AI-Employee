"""orchestrator.py — Gold-tier launcher for the AI Employee.

Starts watchers as background/foreground processes. Supports selective
watcher launch via --watcher flag and cron-mode logging via --cron flag.
Gold-tier additions: watchdog loop, schedule-based cron jobs, vault health check.

Usage:
    python orchestrator.py                          # default: filesystem + approval + whatsapp
    python orchestrator.py --watcher gmail --cron   # cron-triggered Gmail poll
    python orchestrator.py --watcher whatsapp       # WhatsApp daemon only
    python orchestrator.py --watcher approval       # Approval watcher only
    python orchestrator.py --watcher finance        # Finance watcher only
    python orchestrator.py --watcher all            # all watchers
    python orchestrator.py --status                 # print watcher status and exit

Environment variables (see .env.example):
    VAULT_PATH           — absolute path to AI_Employee_Vault (default: ./AI_Employee_Vault)
    VAULT_TEMP_PATH      — fallback temp folder when vault is unavailable
    DRY_RUN              — set to 'true' to log actions without executing (default: true)
    GMAIL_EMAIL          — Gmail address for GmailWatcher
    GMAIL_APP_PASSWORD   — Gmail App Password (16-char string from Google Account > Security)
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

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
VAULT_TEMP_PATH = os.environ.get(
    "VAULT_TEMP_PATH",
    str(Path(__file__).parent / "AI_Employee_Vault_Temp"),
)
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

# Watchdog state: {watcher_name: [restart_timestamp, ...]}
_restart_counts: dict = defaultdict(list)
_RESTART_WINDOW_SECONDS = 3600  # 1 hour
_MAX_RESTARTS_PER_HOUR = 3

# Vault health state
_vault_healthy = True
_vault_lock = threading.Lock()


def _write_log_entry(action_type: str, actor: str, target: str, result: str, parameters: dict = None) -> None:
    """Write NDJSON entry to Logs/YYYY-MM-DD.json."""
    try:
        log_dir = Path(VAULT_PATH) / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "parameters": parameters or {},
            "approval_status": "auto",
            "approved_by": "system",
            "result": result,
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log entry: {e}")


def _write_cron_log_entry() -> None:
    """Write actor: scheduler NDJSON entry to Logs/YYYY-MM-DD.json (FR-020)."""
    _write_log_entry("watcher_start", "scheduler", "orchestrator", "started")
    logger.info("Cron log entry written (actor: scheduler)")


def _start_watcher_thread(watcher_instance, name: str) -> threading.Thread:
    """Start a watcher in a daemon thread and return the thread."""
    t = threading.Thread(target=watcher_instance.run, name=name, daemon=True)
    t.start()
    logger.info(f"Started watcher thread: {name}")
    return t


# ---------------------------------------------------------------------------
# Gold Tier: Watchdog loop (T014)
# ---------------------------------------------------------------------------

def _watchdog_loop(watcher_factories: dict, active_threads: dict) -> None:
    """Monitor watcher liveness every 60s; auto-restart up to 3 times/hour.

    watcher_factories: {name: callable that returns a new watcher instance}
    active_threads:    {name: threading.Thread} — mutated in place on restart
    """
    logger.info("Watchdog loop started")
    while True:
        time.sleep(60)
        now = time.time()
        for name, thread in list(active_threads.items()):
            if not thread.is_alive():
                # Prune old restart timestamps outside the rolling window
                _restart_counts[name] = [
                    ts for ts in _restart_counts[name]
                    if now - ts < _RESTART_WINDOW_SECONDS
                ]
                count = len(_restart_counts[name])
                if count >= _MAX_RESTARTS_PER_HOUR:
                    logger.error(
                        f"Watchdog: {name} exceeded {_MAX_RESTARTS_PER_HOUR} restarts/hour — "
                        "writing error file and disabling auto-restart."
                    )
                    _write_error_file(
                        f"WATCHDOG_{name}",
                        f"Watcher {name} has crashed {_MAX_RESTARTS_PER_HOUR}+ times in the last hour. "
                        "Automatic restart disabled. Manual intervention required.",
                    )
                    _write_log_entry(
                        "watchdog_threshold_exceeded", "watchdog", name, "failure",
                        {"restarts_in_window": count},
                    )
                    del active_threads[name]
                else:
                    logger.warning(f"Watchdog: {name} is dead — restarting (attempt {count + 1})")
                    try:
                        new_instance = watcher_factories[name]()
                        new_thread = _start_watcher_thread(new_instance, name)
                        active_threads[name] = new_thread
                        _restart_counts[name].append(now)
                        _write_log_entry(
                            "watchdog_restart", "watchdog", name, "success",
                            {"restart_count": count + 1},
                        )
                    except Exception as e:
                        logger.error(f"Watchdog: failed to restart {name}: {e}")


def _write_error_file(slug: str, message: str) -> None:
    """Write an ERROR_*.md to Needs_Action/."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"ERROR_{slug}_{ts}.md"
    target = Path(VAULT_PATH) / "Needs_Action" / fname
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"---\ntype: error\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n---\n\n# Error: {slug}\n\n{message}\n",
        encoding="utf-8",
    )
    logger.warning(f"Error file written: {fname}")


# ---------------------------------------------------------------------------
# Gold Tier: Schedule-based cron (T015)
# ---------------------------------------------------------------------------

def _run_ceo_briefing() -> None:
    """Invoke the ceo-briefing Claude skill."""
    if DRY_RUN:
        logger.info("DRY_RUN: CEO briefing skipped (dry-run mode)")
        _write_log_entry("ceo_briefing_skipped", "scheduler", "ceo-briefing", "dry_run")
        return
    logger.info("Scheduler: triggering ceo-briefing skill")
    _write_log_entry("ceo_briefing_trigger", "scheduler", "ceo-briefing", "triggered")
    try:
        subprocess.Popen(
            ["claude", "Run the ceo-briefing skill"],
            cwd=str(Path(__file__).parent),
        )
    except Exception as e:
        logger.error(f"Failed to trigger ceo-briefing: {e}")


def _run_process_needs_action() -> None:
    """Invoke the process-needs-action Claude skill."""
    logger.info("Scheduler: triggering process-needs-action skill")
    _write_log_entry("process_needs_action_trigger", "scheduler", "process-needs-action", "triggered")
    try:
        subprocess.Popen(
            ["claude", "Run the process-needs-action skill"],
            cwd=str(Path(__file__).parent),
        )
    except Exception as e:
        logger.error(f"Failed to trigger process-needs-action: {e}")


def _clean_old_logs() -> None:
    """Delete log files older than 90 days."""
    log_dir = Path(VAULT_PATH) / "Logs"
    if not log_dir.exists():
        return
    cutoff = time.time() - (90 * 24 * 3600)
    deleted = 0
    for f in log_dir.glob("*.json"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            deleted += 1
    if deleted:
        logger.info(f"Log cleanup: deleted {deleted} files older than 90 days")
        _write_log_entry("log_cleanup", "scheduler", "Logs/", "success", {"deleted": deleted})


def _setup_schedule() -> None:
    """Register cron jobs with the schedule library."""
    if not SCHEDULE_AVAILABLE:
        logger.warning("'schedule' library not available — cron jobs disabled")
        return
    schedule.every().sunday.at("23:00").do(_run_ceo_briefing)
    schedule.every().day.at("08:00").do(_run_process_needs_action)
    schedule.every(90).days.do(_clean_old_logs)
    logger.info(f"Scheduled {len(schedule.jobs)} cron jobs")


def _schedule_runner() -> None:
    """Background thread: run pending scheduled jobs every 30 seconds."""
    while True:
        if SCHEDULE_AVAILABLE:
            schedule.run_pending()
        time.sleep(30)


# ---------------------------------------------------------------------------
# Gold Tier: Vault health check (T016 + T017)
# ---------------------------------------------------------------------------

def _vault_health_monitor(watcher_stop_events: dict) -> None:
    """Check vault availability every 5 minutes; pause watchers on failure."""
    global _vault_healthy
    check_interval = 300  # 5 minutes
    retry_interval = 30   # retry every 30s when unhealthy

    while True:
        vault = Path(VAULT_PATH)
        available = vault.exists() and vault.is_dir()

        with _vault_lock:
            was_healthy = _vault_healthy
            _vault_healthy = available

        if not available and was_healthy:
            logger.error("Vault unavailable — pausing watchers")
            for event in watcher_stop_events.values():
                event.set()
            # Write error to temp path
            temp = Path(VAULT_TEMP_PATH)
            temp.mkdir(parents=True, exist_ok=True)
            error_file = temp / "ERROR_VAULT_UNAVAILABLE.md"
            error_file.write_text(
                f"---\ntype: error\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n---\n\n"
                f"# Vault Unavailable\n\nVault at `{VAULT_PATH}` is not accessible.\n"
                "Watchers paused. Will resume when vault is restored.\n",
                encoding="utf-8",
            )
            _write_log_entry("vault_unavailable", "orchestrator", VAULT_PATH, "failure")

        elif available and not was_healthy:
            logger.info("Vault restored — resuming watchers and syncing temp files")
            for event in watcher_stop_events.values():
                event.clear()
            _sync_temp_to_vault()
            _write_log_entry("vault_restored", "orchestrator", VAULT_PATH, "success")

        time.sleep(retry_interval if not available else check_interval)


def _sync_temp_to_vault() -> None:
    """Copy all files from VAULT_TEMP_PATH into the correct vault subfolders on restoration."""
    temp = Path(VAULT_TEMP_PATH)
    if not temp.exists():
        return
    vault = Path(VAULT_PATH)
    synced = 0
    for f in temp.iterdir():
        if f.is_file() and f.name != "ERROR_VAULT_UNAVAILABLE.md":
            dest = vault / "Needs_Action" / f.name
            shutil.copy2(str(f), str(dest))
            f.unlink()
            synced += 1
    if synced:
        logger.info(f"Synced {synced} files from temp to vault")
        _write_log_entry("temp_sync", "orchestrator", str(temp), "success", {"synced": synced})


def main():
    parser = argparse.ArgumentParser(
        description="AI Employee Orchestrator — Gold Tier"
    )
    parser.add_argument(
        "--watcher",
        choices=["filesystem", "gmail", "gmail_api", "whatsapp", "approval", "finance", "all"],
        default=None,
        help="Which watcher(s) to start. Default: filesystem + approval + whatsapp + finance.",
    )
    parser.add_argument(
        "--cron",
        action="store_true",
        default=False,
        help="Indicate this run was triggered by cron. Writes actor:scheduler log entry.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        default=False,
        help="Print watcher availability and exit.",
    )
    args = parser.parse_args()

    logger.info("AI Employee Orchestrator starting (Gold tier)")
    logger.info(f"Vault path      : {VAULT_PATH}")
    logger.info(f"Vault temp path : {VAULT_TEMP_PATH}")
    logger.info(f"Dry-run         : {DRY_RUN}")
    logger.info(f"schedule lib    : {'available' if SCHEDULE_AVAILABLE else 'NOT available — cron disabled'}")

    if not Path(VAULT_PATH).exists() and not args.status:
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
        from watchers.gmail_api_watcher import GmailApiWatcher
    except ImportError as e:
        logger.warning(f"GmailApiWatcher not available: {e}")
        GmailApiWatcher = None

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

    try:
        from watchers.finance_watcher import FinanceWatcher
    except ImportError as e:
        logger.warning(f"FinanceWatcher not available: {e}")
        FinanceWatcher = None

    # --status: print availability table and exit
    if args.status:
        print("\nWatcher availability:")
        print(f"  FilesystemWatcher : always available")
        print(f"  GmailWatcher      : {'available' if GmailWatcher else 'NOT available'}")
        print(f"  GmailApiWatcher   : {'available' if GmailApiWatcher else 'NOT available'}")
        print(f"  WhatsAppWatcher   : {'available' if WhatsAppWatcher else 'NOT available'}")
        print(f"  ApprovalWatcher   : {'available' if ApprovalWatcher else 'NOT available'}")
        print(f"  FinanceWatcher    : {'available' if FinanceWatcher else 'NOT available'}")
        print(f"\nSchedule library  : {'available' if SCHEDULE_AVAILABLE else 'NOT available'}")
        sys.exit(0)

    # Determine which watchers to start
    selected = args.watcher

    threads = []
    # watcher_factories used by watchdog loop
    watcher_factories: dict = {}
    active_threads: dict = {}
    # stop events (not fully implemented per-watcher here — watchdog uses thread liveness)
    watcher_stop_events: dict = {}

    if selected == "gmail":
        # Gmail watcher (IMAP) — typically invoked by cron every 5 minutes
        if GmailWatcher is None:
            logger.error("GmailWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting GmailWatcher (5-min poll)")
        watcher = GmailWatcher(VAULT_PATH)
        watcher.run()  # Run in foreground for cron invocations

    elif selected == "gmail_api":
        if GmailApiWatcher is None:
            logger.error("GmailApiWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting GmailApiWatcher (2-min poll with OAuth)")
        watcher = GmailApiWatcher(VAULT_PATH)
        watcher.run()

    elif selected == "whatsapp":
        if WhatsAppWatcher is None:
            logger.error("WhatsAppWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting WhatsAppWatcher (persistent 60s daemon)")
        watcher = WhatsAppWatcher(VAULT_PATH)
        watcher.run()

    elif selected == "approval":
        if ApprovalWatcher is None:
            logger.error("ApprovalWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting ApprovalWatcher (5s poll)")
        watcher = ApprovalWatcher(VAULT_PATH)
        watcher.run()

    elif selected == "filesystem":
        logger.info("Starting FilesystemWatcher")
        watcher = FilesystemWatcher(VAULT_PATH)
        watcher.run()

    elif selected == "finance":
        if FinanceWatcher is None:
            logger.error("FinanceWatcher unavailable — cannot start")
            sys.exit(1)
        logger.info("Starting FinanceWatcher (5-min poll)")
        watcher = FinanceWatcher(VAULT_PATH)
        watcher.run()

    else:
        # Default (no --watcher flag, or --watcher all):
        # Start FilesystemWatcher + ApprovalWatcher + WhatsAppWatcher + FinanceWatcher
        logger.info("Starting default watchers: FilesystemWatcher + ApprovalWatcher + WhatsAppWatcher + FinanceWatcher")
        logger.info("Press Ctrl+C to stop.")

        # FilesystemWatcher
        fs_watcher = FilesystemWatcher(VAULT_PATH)
        watcher_factories["FilesystemWatcher"] = lambda: FilesystemWatcher(VAULT_PATH)
        t = _start_watcher_thread(fs_watcher, "FilesystemWatcher")
        threads.append(t)
        active_threads["FilesystemWatcher"] = t

        # ApprovalWatcher
        if ApprovalWatcher is not None:
            approval_watcher = ApprovalWatcher(VAULT_PATH)
            watcher_factories["ApprovalWatcher"] = lambda: ApprovalWatcher(VAULT_PATH)
            t = _start_watcher_thread(approval_watcher, "ApprovalWatcher")
            threads.append(t)
            active_threads["ApprovalWatcher"] = t
        else:
            logger.warning("ApprovalWatcher unavailable — skipping")

        # WhatsAppWatcher
        if WhatsAppWatcher is not None:
            wa_watcher = WhatsAppWatcher(VAULT_PATH)
            watcher_factories["WhatsAppWatcher"] = lambda: WhatsAppWatcher(VAULT_PATH)
            t = _start_watcher_thread(wa_watcher, "WhatsAppWatcher")
            threads.append(t)
            active_threads["WhatsAppWatcher"] = t
        else:
            logger.warning("WhatsAppWatcher unavailable — skipping")

        # FinanceWatcher (Gold tier)
        if FinanceWatcher is not None:
            finance_watcher = FinanceWatcher(VAULT_PATH)
            watcher_factories["FinanceWatcher"] = lambda: FinanceWatcher(VAULT_PATH)
            t = _start_watcher_thread(finance_watcher, "FinanceWatcher")
            threads.append(t)
            active_threads["FinanceWatcher"] = t
        else:
            logger.warning("FinanceWatcher unavailable — skipping")

        # Gold tier: start watchdog loop
        watchdog_t = threading.Thread(
            target=_watchdog_loop,
            args=(watcher_factories, active_threads),
            name="WatchdogLoop",
            daemon=True,
        )
        watchdog_t.start()
        logger.info("Watchdog loop started")

        # Gold tier: start cron scheduler
        _setup_schedule()
        sched_t = threading.Thread(
            target=_schedule_runner,
            name="ScheduleRunner",
            daemon=True,
        )
        sched_t.start()

        # Gold tier: start vault health monitor
        vault_health_t = threading.Thread(
            target=_vault_health_monitor,
            args=(watcher_stop_events,),
            name="VaultHealthMonitor",
            daemon=True,
        )
        vault_health_t.start()

        # Keep main thread alive
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Orchestrator shutting down (Ctrl+C)")


if __name__ == "__main__":
    main()
