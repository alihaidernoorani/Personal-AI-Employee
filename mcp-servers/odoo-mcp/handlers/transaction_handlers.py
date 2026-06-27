"""transaction_handlers.py — Odoo bank transaction and expense handlers."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def tool_create_transaction(
    amount: float,
    date: str,
    payee: str,
    reference: str,
    category: str,
    dry_run: bool,
    ensure_auth_fn,
    rpc_call_fn,
) -> dict:
    if dry_run:
        return {"dry_run": True, "transaction_id": f"MOCK_TXN_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"}
    if not ensure_auth_fn():
        return {"error": "AUTH_FAILED", "retryable": False}
    move_type = "in_invoice" if amount < 0 else "out_invoice"
    result = rpc_call_fn("account.move", "create", [{
        "move_type": move_type,
        "invoice_date": date,
        "ref": reference,
        "narration": f"{payee} | {category}",
        "invoice_line_ids": [[0, 0, {
            "name": f"{payee} — {category}",
            "quantity": 1,
            "price_unit": abs(amount),
        }]],
    }])
    if "error" in result:
        return result
    return {"transaction_id": str(result.get("result", "unknown")), "model": "account.move"}


def tool_sync_transaction(
    bank_transaction_id: str,
    odoo_transaction_id: str,
    dry_run: bool,
    rpc_call_fn,
) -> dict:
    if dry_run:
        return {"dry_run": True, "synced": True}
    result = rpc_call_fn(
        "account.bank.statement.line", "write",
        [[int(odoo_transaction_id)], {"internal_index": bank_transaction_id}],
    )
    if "error" in result:
        return result
    return {"synced": True}


def tool_update_expense(
    name: str,
    total_amount: float,
    dry_run: bool,
    ensure_auth_fn,
    rpc_call_fn,
    log_action_fn,
    expense_id: int | None = None,
    date: str | None = None,
    category: str | None = None,
    employee: str | None = None,
    reference: str | None = None,
) -> dict:
    action = "updated" if expense_id else "created"
    if dry_run:
        return {"dry_run": True, "action": action, "expense_id": expense_id or "MOCK_EXP_001", "name": name, "total_amount": total_amount}
    if not ensure_auth_fn():
        return {"error": "AUTH_FAILED", "retryable": False}

    employee_id = _resolve_employee(employee, rpc_call_fn)
    if not employee_id:
        return {"error": "No employee found in Odoo — create an employee record first.", "retryable": False}

    product_id = None
    if category:
        result = rpc_call_fn("product.product", "search_read",
            [[["name", "ilike", category], ["can_be_expensed", "=", True]]],
            {"fields": ["id", "name"], "limit": 1})
        rows = result.get("result") or []
        if rows:
            product_id = rows[0]["id"]

    expense_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    vals: dict = {"name": name, "total_amount": total_amount, "date": expense_date, "employee_id": employee_id}
    if product_id:
        vals["product_id"] = product_id
    if reference:
        vals["reference"] = reference

    if expense_id:
        result = rpc_call_fn("hr.expense", "write", [[expense_id], vals])
        if "error" in result:
            return result
        result_id = expense_id
    else:
        result = rpc_call_fn("hr.expense", "create", [vals])
        if "error" in result:
            return result
        result_id = result.get("result")

    read_result = rpc_call_fn("hr.expense", "read", [[result_id]],
        {"fields": ["name", "total_amount", "state", "date", "employee_id"]})
    record = (read_result.get("result") or [{}])[0]
    employee_name = record["employee_id"][1] if isinstance(record.get("employee_id"), list) else ""
    log_action_fn("update_expense", str(result_id), vals, "auto", {"status": "ok"})
    return {
        "status": "ok", "action": action, "expense_id": result_id,
        "name": record.get("name", name), "total_amount": record.get("total_amount", total_amount),
        "state": record.get("state", "draft"), "date": record.get("date", expense_date),
        "employee": employee_name,
    }


def _resolve_employee(employee: str | None, rpc_call_fn) -> int | None:
    if employee:
        result = rpc_call_fn("hr.employee", "search_read",
            [[["name", "ilike", employee]]], {"fields": ["id", "name"], "limit": 1})
        rows = result.get("result") or []
        if rows:
            return rows[0]["id"]
    result = rpc_call_fn("hr.employee", "search_read", [[]], {"fields": ["id", "name"], "limit": 1})
    rows = result.get("result") or []
    return rows[0]["id"] if rows else None
