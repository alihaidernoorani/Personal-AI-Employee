"""cloud_orchestrator.py — Cloud VM process manager for Platinum AI Employee.

Activates only when AGENT_ROLE=cloud. Starts and watchdogs:
  - gmail_watcher.py (primary email triage)
  - signals_watcher.py (cross-agent alert channel)
  - heartbeat_writer.py (liveness beacon)
  - stale_task_monitor.py (monitors In_Progress/local/ for stale tasks)

Cron schedule (via schedule library):
  - Tuesday 09:00 UTC → create social post trigger
  - Sunday 22:00 UTC  → invoke cloud-briefing-prep skill
  - daily 06:00 UTC   → invoke vault-health skill

Graceful shutdown: on SIGNAL_shutdown_request detected, drains in-progress
tasks and exits all processes cleanly.

Usage:
    AGENT_ROLE=cloud python cloud_orchestrator.py
"""

import json
import logging
import os
import shutil
import signal
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
    format="%(asctime)s [CloudOrchestrator] %(levelname)s: %(message)s",
)
logger = logging.getLogger("CloudOrchestrator")

AGENT_ROLE = os.environ.get("AGENT_ROLE", "local")
VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    str(Path(__file__).parent / "AI_Employee_Vault"),
)
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
STALE_TASK_TIMEOUT_SECONDS = int(os.environ.get("STALE_TASK_TIMEOUT_SECONDS", "600"))
ODOO_DRAFT_ONLY = os.environ.get("ODOO_DRAFT_ONLY", "false").lower() == "true"
ODOO_AVAILABLE = True  # Updated by health check

_shutdown_requested = threading.Event()
_restart_counts: dict = defaultdict(list)
_RESTART_WINDOW = 3600
_MAX_RESTARTS = 3


def _write_signal(signal_type: str, severity: str, message: str, requires_human: bool = False) -> None:
    """Write a SIGNAL_*.md to Signals/ directory."""
    signals_dir = Path(VAULT_PATH) / "Signals"
    signals_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    signal_file = signals_dir / f"SIGNAL_{signal_type}_{ts}.md"
    content = (
        f"---\n"
        f"signal_type: {signal_type}\n"
        f"severity: {severity}\n"
        f"created: {datetime.now(timezone.utc).isoformat()}Z\n"
        f"agent_id: cloud_orchestrator\n"
        f"requires_human_action: {str(requires_human).lower()}\n"
        f"---\n\n"
        f"# Signal: {signal_type}\n\n{message}\n"
    )
    signal_file.write_text(content, encoding="utf-8")
    logger.info(f"Signal written: {signal_file.name}")


def _write_error(slug: str, message: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"ERROR_{slug}_{ts}.md"
    target = Path(VAULT_PATH) / "Needs_Action" / fname
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"---\ntype: error\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n---\n\n"
        f"# Error: {slug}\n\n{message}\n",
        encoding="utf-8",
    )


_EXECUTION_TOOLS = {
    "post_invoice", "send_email", "queue_email", "flush_queue",
    "post_twitter", "post_linkedin", "post_facebook", "post_instagram",
    "draft_reply", "search_inbox",
}


def _validate_startup() -> None:
    """Validate cloud VM environment before starting watchers."""
    if AGENT_ROLE != "cloud":
        logger.error(f"AGENT_ROLE={AGENT_ROLE} — cloud_orchestrator.py must run with AGENT_ROLE=cloud")
        sys.exit(1)

    # Check .mcp.json for prohibited execution tools
    mcp_config = Path(__file__).parent / ".mcp.json"
    if mcp_config.exists():
        try:
            config = json.loads(mcp_config.read_text(encoding="utf-8"))
            registered_tools: set = set()
            for server_cfg in config.get("mcpServers", {}).values():
                for tool in server_cfg.get("tools", []):
                    registered_tools.add(tool)
            violations = registered_tools & _EXECUTION_TOOLS
            if violations:
                _write_signal(
                    "single_writer_violation", "critical",
                    f"Cloud .mcp.json registers execution tools: {sorted(violations)}. "
                    "Only create_invoice and update_expense are permitted on cloud VM.",
                    True,
                )
                logger.error(f"Cloud .mcp.json has prohibited execution tools: {violations}")
                sys.exit(1)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not parse .mcp.json: {e}")

    # Verify no email/social MCP server processes are running
    try:
        import psutil
        suspicious = []
        for proc in psutil.process_iter(["pid", "cmdline"]):
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if any(kw in cmdline for kw in ("email-mcp", "social-mcp", "browser-mcp")):
                suspicious.append(f"pid={proc.info['pid']} cmd={cmdline[:80]}")
        if suspicious:
            _write_signal(
                "single_writer_violation", "critical",
                f"Execution MCP processes detected on cloud VM: {suspicious}",
                True,
            )
            logger.error(f"Execution MCP processes running on cloud VM: {suspicious}")
            sys.exit(1)
    except ImportError:
        logger.debug("psutil not available — skipping MCP process check")

    # Verify disk usage < 80%
    vault = Path(VAULT_PATH)
    if vault.exists():
        usage = shutil.disk_usage(str(vault))
        pct = usage.used / usage.total * 100
        if pct > 80:
            _write_signal("disk_alert", "warning", f"Cloud VM disk usage at {pct:.1f}%", True)
            logger.warning(f"Disk usage at {pct:.1f}% — above 80% threshold")

    # Verify ODOO_DRAFT_ONLY is set on cloud
    if not ODOO_DRAFT_ONLY:
        _write_signal("config_warning", "warning",
                      "ODOO_DRAFT_ONLY is not true on cloud VM — only draft Odoo operations are permitted.", False)
        logger.warning("ODOO_DRAFT_ONLY is not set to true on cloud VM")

    logger.info("Cloud startup validation passed")


def _startup_health_check() -> None:
    """Write startup health signal after validating key services."""
    import ssl
    try:
        import ssl
        from urllib import request as urllib_request
        checks = {}

        # Check Syncthing
        try:
            urllib_request.urlopen("http://127.0.0.1:8384/rest/system/ping", timeout=5)
            checks["syncthing"] = "ok"
        except Exception:
            checks["syncthing"] = "unavailable"

        severity = "info" if all(v == "ok" for v in checks.values()) else "warning"
        _write_signal(
            "startup_health", severity,
            f"Cloud orchestrator started. Service status: {json.dumps(checks)}"
        )
    except Exception as e:
        logger.warning(f"Startup health check failed: {e}")


def _start_thread(target, name: str, args: tuple = ()) -> threading.Thread:
    t = threading.Thread(target=target, args=args, name=name, daemon=True)
    t.start()
    logger.info(f"Started thread: {name}")
    return t


def _watchdog_loop(factories: dict, threads: dict) -> None:
    """Restart dead watcher threads up to MAX_RESTARTS/hour."""
    while not _shutdown_requested.is_set():
        time.sleep(60)
        now = time.time()
        for name, thread in list(threads.items()):
            if _shutdown_requested.is_set():
                break
            if not thread.is_alive():
                _restart_counts[name] = [
                    ts for ts in _restart_counts[name] if now - ts < _RESTART_WINDOW
                ]
                count = len(_restart_counts[name])
                if count >= _MAX_RESTARTS:
                    logger.error(f"Watchdog: {name} exceeded {_MAX_RESTARTS} restarts/hour — disabling")
                    _write_error(f"WATCHDOG_{name}", f"Watcher {name} crashed {_MAX_RESTARTS}+ times. Manual restart required.")
                    del threads[name]
                else:
                    logger.warning(f"Watchdog: restarting {name} (attempt {count + 1})")
                    new_thread = _start_thread(*factories[name](), name=name)
                    threads[name] = new_thread
                    _restart_counts[name].append(now)


def _check_shutdown_signal() -> bool:
    """Return True if SIGNAL_shutdown_request_*.md detected in Signals/."""
    signals_dir = Path(VAULT_PATH) / "Signals"
    if not signals_dir.exists():
        return False
    return any(signals_dir.glob("SIGNAL_shutdown_request_*.md"))


def _graceful_shutdown(in_progress_cloud: Path, needs_action: Path) -> None:
    """Return any remaining In_Progress/cloud/ tasks to Needs_Action/ and write final heartbeat."""
    logger.info("Initiating graceful shutdown...")
    _shutdown_requested.set()

    time.sleep(5)  # Brief pause for threads to observe the flag

    if in_progress_cloud.exists():
        for task_file in in_progress_cloud.iterdir():
            if task_file.is_file() and task_file.name != ".gitkeep":
                try:
                    dest = needs_action / task_file.name
                    needs_action.mkdir(parents=True, exist_ok=True)
                    task_file.rename(dest)
                    logger.info(f"Returned task to Needs_Action: {task_file.name}")
                except OSError as e:
                    logger.error(f"Could not return task {task_file.name}: {e}")

    # Write final heartbeat
    try:
        from watchers.heartbeat_writer import _write_heartbeat
        _write_heartbeat(Path(VAULT_PATH), "cloud_agent_shutdown")
    except Exception as e:
        logger.warning(f"Final heartbeat failed: {e}")

    logger.info("Graceful shutdown complete")


def _check_odoo_health() -> None:
    """Check cloud Odoo health every 600s and write signals on failure/recovery."""
    global ODOO_AVAILABLE
    import ssl
    from urllib import request as urllib_request
    from urllib.error import URLError

    while not _shutdown_requested.is_set():
        time.sleep(600)
        try:
            resp = urllib_request.urlopen("https://localhost/web/health", timeout=10)
            if resp.status < 300:
                if not ODOO_AVAILABLE:
                    _write_signal("odoo_recovered", "info", "Odoo HTTPS endpoint is responding again.")
                    ODOO_AVAILABLE = True
            else:
                raise ValueError(f"Non-2xx response: {resp.status}")
        except Exception as e:
            if ODOO_AVAILABLE:
                _write_signal("odoo_down", "warning", f"Odoo HTTPS health check failed: {e}", False)
                ODOO_AVAILABLE = False

        # Check TLS cert expiry
        try:
            import ssl as ssl_module
            import socket
            ctx = ssl_module.create_default_context()
            with ctx.wrap_socket(socket.create_connection(("localhost", 443), timeout=10), server_hostname="localhost") as conn:
                cert = conn.getpeercert()
                expiry_str = cert.get("notAfter", "")
                if expiry_str:
                    expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_left = (expiry - datetime.now(timezone.utc)).days
                    if days_left <= 0:
                        _write_signal("cert_expiry", "critical", f"TLS certificate has EXPIRED ({expiry_str})", True)
                    elif days_left <= 14:
                        _write_signal("cert_expiry", "warning", f"TLS certificate expires in {days_left} days ({expiry_str})", False)
        except Exception as e:
            logger.debug(f"TLS cert check skipped (Odoo may not be configured): {e}")


def _run_cron_skill(skill_name: str) -> None:
    if DRY_RUN:
        logger.info(f"DRY_RUN: {skill_name} skill trigger skipped")
        return
    logger.info(f"Triggering {skill_name} skill")
    try:
        subprocess.Popen(
            ["claude", f"Run the {skill_name} skill"],
            cwd=str(Path(__file__).parent),
        )
    except Exception as e:
        logger.error(f"Failed to trigger {skill_name}: {e}")


def _create_social_trigger() -> None:
    vault = Path(VAULT_PATH)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    trigger_file = vault / "Needs_Action" / f"SOCIAL_POST_TRIGGER_linkedin_{ts}.md"
    trigger_file.parent.mkdir(parents=True, exist_ok=True)
    trigger_file.write_text(
        f"---\ntype: social_post_trigger\nplatform: linkedin\nreceived: {datetime.now(timezone.utc).isoformat()}Z\n---\n\n"
        "# LinkedIn Post Trigger\n\nWeekly LinkedIn post trigger created by cloud_orchestrator cron.\n",
        encoding="utf-8",
    )
    logger.info(f"Social post trigger created: {trigger_file.name}")


def _setup_schedule() -> None:
    if not SCHEDULE_AVAILABLE:
        logger.warning("'schedule' library not available — cron jobs disabled")
        return
    schedule.every().tuesday.at("09:00").do(_create_social_trigger)
    schedule.every().sunday.at("22:00").do(lambda: _run_cron_skill("cloud-briefing-prep"))
    schedule.every().day.at("06:00").do(lambda: _run_cron_skill("vault-health"))
    logger.info(f"Scheduled {len(schedule.jobs)} cloud cron jobs")


def _schedule_runner() -> None:
    while not _shutdown_requested.is_set():
        if SCHEDULE_AVAILABLE:
            schedule.run_pending()
        time.sleep(30)


def main() -> None:
    _validate_startup()

    sys.path.insert(0, str(Path(__file__).parent))

    vault = Path(VAULT_PATH)
    in_progress_cloud = vault / "In_Progress" / "cloud"
    needs_action = vault / "Needs_Action"

    signal.signal(signal.SIGTERM, lambda *_: _graceful_shutdown(in_progress_cloud, needs_action))

    logger.info(f"Cloud Orchestrator starting (VAULT={VAULT_PATH}, DRY_RUN={DRY_RUN})")
    _startup_health_check()

    threads: dict = {}
    factories: dict = {}

    # Import watchers
    from watchers.heartbeat_writer import run as hb_run
    from watchers.stale_task_monitor import run as stale_run
    from watchers.signals_watcher import run as signals_run

    try:
        from watchers.gmail_watcher import GmailWatcher
        gw = GmailWatcher(VAULT_PATH)
        t = _start_thread(gw.run, "gmail_watcher")
        threads["gmail_watcher"] = t
        factories["gmail_watcher"] = lambda: (gw.run,)
    except Exception as e:
        logger.warning(f"GmailWatcher unavailable: {e}")

    t = _start_thread(signals_run, "signals_watcher", args=(VAULT_PATH,))
    threads["signals_watcher"] = t
    factories["signals_watcher"] = lambda: (signals_run, "signals_watcher", (VAULT_PATH,))

    t = _start_thread(hb_run, "heartbeat_writer", args=(VAULT_PATH,))
    threads["heartbeat_writer"] = t

    t = _start_thread(stale_run, "stale_task_monitor", args=(VAULT_PATH,))
    threads["stale_task_monitor"] = t

    # Watchdog
    watchdog_t = threading.Thread(
        target=_watchdog_loop, args=(factories, threads),
        name="WatchdogLoop", daemon=True,
    )
    watchdog_t.start()

    # Cron scheduler
    _setup_schedule()
    _start_thread(_schedule_runner, "ScheduleRunner")

    # Odoo health monitor
    _start_thread(_check_odoo_health, "OdooHealthMonitor")

    logger.info("All cloud watchers started. Monitoring for shutdown signal...")

    try:
        while not _shutdown_requested.is_set():
            if _check_shutdown_signal():
                logger.info("Shutdown signal detected in Signals/")
                _graceful_shutdown(in_progress_cloud, needs_action)
                break
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
        _graceful_shutdown(in_progress_cloud, needs_action)


if __name__ == "__main__":
    main()
