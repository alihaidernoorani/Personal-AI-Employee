"""invoice_handlers.py — Odoo invoice create/post/list handlers."""

import logging
import time
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_payment_timestamps: deque = deque()
_MAX_PAYMENTS_PER_HOUR = 3
_RATE_WINDOW_SECONDS = 3600


def check_payment_rate_limit() -> bool:
    now = time.time()
    while _payment_timestamps and now - _payment_timestamps[0] > _RATE_WINDOW_SECONDS:
        _payment_timestamps.popleft()
    return len(_payment_timestamps) < _MAX_PAYMENTS_PER_HOUR


def record_payment() -> None:
    _payment_timestamps.append(time.time())


def tool_create_invoice(
    customer_id: str,
    line_items: list,
    due_date: str,
    dry_run: bool,
    ensure_auth_fn,
    rpc_call_fn,
    log_action_fn,
) -> dict:
    if dry_run:
        return {"dry_run": True, "invoice_id": "MOCK_001", "status": "draft"}
    if not ensure_auth_fn():
        return {"error": "AUTH_FAILED", "retryable": False}
    invoice_lines = [
        (0, 0, {
            "name": item.get("description", ""),
            "quantity": item.get("quantity", 1),
            "price_unit": item.get("unit_price", 0),
        })
        for item in line_items
    ]
    result = rpc_call_fn("account.move", "create", [{
        "move_type": "out_invoice",
        "partner_id": int(customer_id),
        "invoice_date_due": due_date,
        "invoice_line_ids": invoice_lines,
    }])
    if "error" in result:
        return result
    invoice_id = str(result.get("result", "unknown"))
    log_action_fn("create_invoice", customer_id, {"customer_id": customer_id, "due_date": due_date}, "approved", {"status": "draft"})
    return {"invoice_id": invoice_id, "status": "draft"}


def tool_post_invoice(
    invoice_id: str,
    approval_id: str,
    dry_run: bool,
    ensure_auth_fn,
    rpc_call_fn,
    log_action_fn,
) -> dict:
    if not approval_id:
        return {"error": "APPROVAL_REQUIRED", "retryable": False}
    if not check_payment_rate_limit():
        return {"error": "RATE_LIMIT_EXCEEDED", "retryable": False}
    if dry_run:
        record_payment()
        return {"dry_run": True, "invoice_id": invoice_id, "state": "posted"}
    if not ensure_auth_fn():
        return {"error": "AUTH_FAILED", "retryable": False}
    result = rpc_call_fn("account.move", "action_post", [[int(invoice_id)]])
    if "error" in result:
        return result
    record_payment()
    return {"invoice_id": invoice_id, "state": "posted"}


def tool_list_invoices(
    date_from: str | None,
    date_to: str | None,
    state: str | None,
    dry_run: bool,
    ensure_auth_fn,
    rpc_call_fn,
) -> list | dict:
    if dry_run:
        return {"dry_run": True, "invoices": [
            {"invoice_id": "MOCK_001", "customer": "Test Customer", "amount": 1000.0, "state": "draft", "due_date": "2026-04-01"},
        ]}
    if not ensure_auth_fn():
        return {"error": "AUTH_FAILED", "retryable": False}
    domain: list = []
    if date_from:
        domain.append(["invoice_date", ">=", date_from])
    if date_to:
        domain.append(["invoice_date", "<=", date_to])
    if state:
        domain.append(["state", "=", state])
    result = rpc_call_fn(
        "account.move", "search_read", [domain],
        {"fields": ["id", "partner_id", "amount_total", "state", "invoice_date_due"], "limit": 100},
    )
    if "error" in result:
        return result
    return [
        {
            "invoice_id": str(r["id"]),
            "customer": r["partner_id"][1] if r.get("partner_id") else "",
            "amount": r.get("amount_total", 0),
            "state": r.get("state", ""),
            "due_date": r.get("invoice_date_due", ""),
        }
        for r in (result.get("result") or [])
    ]
