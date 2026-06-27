"""odoo_rpc.py — Odoo JSON-RPC session management and audit logging."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

_session_uid: int | None = None
_session_cookies: dict = {}
_rpc_call_id: int = 0


def log_action(vault_path: Path, action_type: str, target: str, parameters: dict, approval_status: str, result: dict) -> None:
    try:
        log_dir = vault_path / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type,
            "actor": "odoo-mcp",
            "target": target,
            "parameters": {k: v for k, v in parameters.items() if k not in ("approval_id",)},
            "approval_status": approval_status,
            "result": result.get("status", result.get("error", "ok")),
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


def _validate_odoo_url() -> bool:
    if not ODOO_URL:
        return False
    return any(ODOO_URL.startswith(p) for p in ("https://", "http://localhost", "http://127.0.0.1"))


def authenticate() -> bool:
    global _session_uid, _session_cookies
    try:
        import requests
    except ImportError:
        return False
    if not _validate_odoo_url():
        return False
    try:
        resp = requests.post(
            f"{ODOO_URL}/web/session/authenticate",
            json={"jsonrpc": "2.0", "method": "call", "id": 1,
                  "params": {"db": ODOO_DB, "login": ODOO_USERNAME, "password": ODOO_PASSWORD}},
            timeout=15,
        )
        resp.raise_for_status()
        uid = resp.json().get("result", {}).get("uid")
        if not uid:
            logger.error("Odoo auth failed: no uid in response")
            return False
        _session_uid = uid
        _session_cookies = dict(resp.cookies)
        return True
    except Exception as e:
        logger.error(f"Odoo authentication error: {e}")
        return False


def rpc_call(model: str, method: str, args: list, kwargs: dict | None = None) -> dict:
    global _rpc_call_id, _session_uid
    try:
        import requests
    except ImportError:
        return {"error": "requests not installed", "retryable": False}
    _rpc_call_id += 1
    payload = {"jsonrpc": "2.0", "method": "call", "id": _rpc_call_id,
               "params": {"model": model, "method": method, "args": args, "kwargs": kwargs or {}}}
    try:
        resp = requests.post(f"{ODOO_URL}/web/dataset/call_kw",
                             json=payload, cookies=_session_cookies, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        error = data.get("error")
        if error:
            msg = str(error)
            if "session" in msg.lower() or "Odoo Session Expired" in msg:
                _session_uid = None
                if authenticate():
                    return rpc_call(model, method, args, kwargs)
                return {"error": "AUTH_FAILED", "retryable": False}
            return {"error": msg, "retryable": True}
        return {"result": data.get("result")}
    except Exception as e:
        return {"error": str(e), "retryable": True}


def ensure_auth(dry_run: bool) -> bool:
    if dry_run:
        return True
    if _session_uid is None:
        return authenticate()
    return True
