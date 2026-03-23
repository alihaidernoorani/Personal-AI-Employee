"""odoo-mcp — Python MCP server (stdio transport) for Odoo 19+ JSON-RPC.

Tools:
  - get_customer(name?, email?)
  - create_invoice(customer_id, line_items[], due_date)
  - post_invoice(invoice_id, approval_id)           [irreversible, requires approval]
  - create_transaction(amount, date, payee, reference, category)
  - sync_transaction(bank_transaction_id, odoo_transaction_id)
  - list_invoices(date_from?, date_to?, state?)

Authentication: session-based via /web/session/authenticate. Auto-reauth on expiry.
HTTPS only — ODOO_URL must begin with https://.
Rate limit: post_invoice max 3/hour.
DRY_RUN=true (default) — no real Odoo records created during development.
"""

import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"

ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# Rate limit state for post_invoice
_payment_timestamps: deque = deque()
_MAX_PAYMENTS_PER_HOUR = 3
_RATE_WINDOW_SECONDS = 3600

# Session state
_session_uid: int | None = None
_session_cookies: dict = {}
_rpc_call_id: int = 0

server = Server("odoo-mcp")


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def _log_action(action_type: str, target: str, parameters: dict, approval_status: str, result: dict) -> None:
    try:
        log_dir = VAULT_PATH / "Logs"
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
        logger.error(f"Failed to write log: {e}")


# ---------------------------------------------------------------------------
# Odoo JSON-RPC authentication
# ---------------------------------------------------------------------------

def _validate_odoo_url() -> bool:
    """Ensure ODOO_URL uses HTTPS."""
    if not ODOO_URL:
        return False
    if not ODOO_URL.startswith("https://"):
        logger.error(f"ODOO_URL must begin with https:// — got: {ODOO_URL}")
        return False
    return True


def _authenticate() -> bool:
    """Authenticate against Odoo and store session uid + cookies."""
    global _session_uid, _session_cookies
    if not REQUESTS_AVAILABLE:
        logger.error("requests library not available")
        return False
    if not _validate_odoo_url():
        return False
    try:
        resp = requests.post(
            f"{ODOO_URL}/web/session/authenticate",
            json={
                "jsonrpc": "2.0",
                "method": "call",
                "id": 1,
                "params": {"db": ODOO_DB, "login": ODOO_USERNAME, "password": ODOO_PASSWORD},
            },
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json().get("result", {})
        uid = result.get("uid")
        if not uid:
            logger.error(f"Odoo auth failed: {resp.json().get('error', 'no uid in response')}")
            return False
        _session_uid = uid
        _session_cookies = dict(resp.cookies)
        logger.info(f"Odoo session established uid={uid}")
        return True
    except Exception as e:
        logger.error(f"Odoo authentication error: {e}")
        return False


def _rpc_call(model: str, method: str, args: list, kwargs: dict | None = None) -> dict:
    """Make a JSON-RPC call to Odoo. Auto-reauth on session expiry."""
    global _rpc_call_id, _session_uid
    _rpc_call_id += 1
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "id": _rpc_call_id,
        "params": {
            "model": model,
            "method": method,
            "args": args,
            "kwargs": kwargs or {},
        },
    }
    try:
        resp = requests.post(
            f"{ODOO_URL}/web/dataset/call_kw",
            json=payload,
            cookies=_session_cookies,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Detect session expiry
        error = data.get("error")
        if error:
            msg = str(error)
            if "session" in msg.lower() or "Odoo Session Expired" in msg:
                logger.warning("Odoo session expired — re-authenticating")
                if _authenticate():
                    return _rpc_call(model, method, args, kwargs)
                return {"error": "AUTH_FAILED", "odoo_error_code": "session_expired", "retryable": False}
            return {"error": msg, "retryable": True}
        return {"result": data.get("result")}
    except requests.ConnectionError:
        return {"error": "ODOO_UNAVAILABLE", "retryable": True}
    except Exception as e:
        return {"error": str(e), "retryable": True}


def _ensure_auth() -> bool:
    """Ensure we have an active session; authenticate if not."""
    if DRY_RUN:
        return True  # mock session in dry-run
    if _session_uid is None:
        return _authenticate()
    return True


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _check_payment_rate_limit() -> bool:
    now = time.time()
    while _payment_timestamps and now - _payment_timestamps[0] > _RATE_WINDOW_SECONDS:
        _payment_timestamps.popleft()
    return len(_payment_timestamps) < _MAX_PAYMENTS_PER_HOUR


def _record_payment() -> None:
    _payment_timestamps.append(time.time())


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _tool_get_customer(name: str | None, email: str | None) -> list | dict:
    if not name and not email:
        return {"error": "At least one of name or email is required", "retryable": False}
    if DRY_RUN:
        return {"dry_run": True, "customers": [{"id": "1", "name": name or "Test Customer", "email": email or "test@example.com"}]}
    if not _ensure_auth():
        return {"error": "AUTH_FAILED", "retryable": False}
    domain = []
    if name:
        domain.append(["name", "ilike", name])
    if email:
        domain.append(["email", "ilike", email])
    if len(domain) > 1:
        domain = ["|"] + domain
    result = _rpc_call("res.partner", "search_read", [domain], {"fields": ["id", "name", "email"], "limit": 20})
    if "error" in result:
        return result
    return [{"id": str(r["id"]), "name": r["name"], "email": r.get("email", "")} for r in (result.get("result") or [])]


def _tool_create_invoice(customer_id: str, line_items: list, due_date: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "invoice_id": "MOCK_001", "status": "draft"}
    if not _ensure_auth():
        return {"error": "AUTH_FAILED", "retryable": False}
    invoice_lines = []
    for item in line_items:
        invoice_lines.append((0, 0, {
            "name": item.get("description", ""),
            "quantity": item.get("quantity", 1),
            "price_unit": item.get("unit_price", 0),
        }))
    result = _rpc_call("account.move", "create", [{
        "move_type": "out_invoice",
        "partner_id": int(customer_id),
        "invoice_date_due": due_date,
        "invoice_line_ids": invoice_lines,
    }])
    if "error" in result:
        return result
    invoice_id = str(result.get("result", "unknown"))
    _log_action("create_invoice", customer_id, {"customer_id": customer_id, "due_date": due_date}, "approved", {"status": "draft"})
    return {"invoice_id": invoice_id, "status": "draft"}


def _tool_post_invoice(invoice_id: str, approval_id: str) -> dict:
    if not approval_id:
        return {"error": "APPROVAL_REQUIRED", "retryable": False}
    if not _check_payment_rate_limit():
        return {"error": "RATE_LIMIT_EXCEEDED", "retryable": False}
    if DRY_RUN:
        _record_payment()
        return {"dry_run": True, "invoice_id": invoice_id, "state": "posted"}
    if not _ensure_auth():
        return {"error": "AUTH_FAILED", "retryable": False}
    result = _rpc_call("account.move", "action_post", [[int(invoice_id)]])
    if "error" in result:
        return result
    _record_payment()
    return {"invoice_id": invoice_id, "state": "posted"}


def _tool_create_transaction(amount: float, date: str, payee: str, reference: str, category: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "transaction_id": f"MOCK_TXN_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"}
    if not _ensure_auth():
        return {"error": "AUTH_FAILED", "retryable": False}
    # Odoo account.bank.statement.line for transaction recording
    result = _rpc_call("account.bank.statement.line", "create", [{
        "date": date,
        "payment_ref": reference,
        "partner_name": payee,
        "amount": amount,
        "narration": category,
    }])
    if "error" in result:
        return result
    return {"transaction_id": str(result.get("result", "unknown"))}


def _tool_sync_transaction(bank_transaction_id: str, odoo_transaction_id: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "synced": True}
    # Mark bank statement line as reconciled
    result = _rpc_call(
        "account.bank.statement.line",
        "write",
        [[int(odoo_transaction_id)], {"internal_index": bank_transaction_id}],
    )
    if "error" in result:
        return result
    return {"synced": True}


def _tool_update_expense(
    name: str,
    total_amount: float,
    expense_id: int | None = None,
    date: str | None = None,
    category: str | None = None,
    employee: str | None = None,
    reference: str | None = None,
) -> dict:
    action = "updated" if expense_id else "created"
    if DRY_RUN:
        return {
            "dry_run": True,
            "action": action,
            "expense_id": expense_id or "MOCK_EXP_001",
            "name": name,
            "total_amount": total_amount,
        }
    if not _ensure_auth():
        return {"error": "AUTH_FAILED", "retryable": False}

    # Resolve employee_id
    employee_id = None
    if employee:
        result = _rpc_call("hr.employee", "search_read",
            [[["name", "ilike", employee]]],
            {"fields": ["id", "name"], "limit": 1},
        )
        rows = result.get("result") or []
        if rows:
            employee_id = rows[0]["id"]
    if not employee_id:
        result = _rpc_call("hr.employee", "search_read",
            [[]], {"fields": ["id", "name"], "limit": 1})
        rows = result.get("result") or []
        if rows:
            employee_id = rows[0]["id"]
    if not employee_id:
        return {"error": "No employee found in Odoo — create an employee record first.", "retryable": False}

    # Resolve product_id from category name
    product_id = None
    if category:
        result = _rpc_call("product.product", "search_read",
            [[["name", "ilike", category], ["can_be_expensed", "=", True]]],
            {"fields": ["id", "name"], "limit": 1},
        )
        rows = result.get("result") or []
        if rows:
            product_id = rows[0]["id"]

    expense_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    vals: dict = {
        "name": name,
        "total_amount": total_amount,
        "date": expense_date,
        "employee_id": employee_id,
    }
    if product_id:
        vals["product_id"] = product_id
    if reference:
        vals["reference"] = reference

    if expense_id:
        result = _rpc_call("hr.expense", "write", [[expense_id], vals])
        if "error" in result:
            return result
        result_id = expense_id
    else:
        result = _rpc_call("hr.expense", "create", [vals])
        if "error" in result:
            return result
        result_id = result.get("result")

    # Read back confirmation
    read_result = _rpc_call("hr.expense", "read",
        [[result_id]],
        {"fields": ["name", "total_amount", "state", "date", "employee_id"]},
    )
    record = (read_result.get("result") or [{}])[0]

    employee_name = record["employee_id"][1] if isinstance(record.get("employee_id"), list) else ""
    _log_action("update_expense", str(result_id), vals, "auto", {"status": "ok"})
    return {
        "status": "ok",
        "action": action,
        "expense_id": result_id,
        "name": record.get("name", name),
        "total_amount": record.get("total_amount", total_amount),
        "state": record.get("state", "draft"),
        "date": record.get("date", expense_date),
        "employee": employee_name,
    }


def _tool_list_invoices(date_from: str | None, date_to: str | None, state: str | None) -> list | dict:
    if DRY_RUN:
        return {"dry_run": True, "invoices": [
            {"invoice_id": "MOCK_001", "customer": "Test Customer", "amount": 1000.0, "state": "draft", "due_date": "2026-04-01"},
        ]}
    if not _ensure_auth():
        return {"error": "AUTH_FAILED", "retryable": False}
    domain = []
    if date_from:
        domain.append(["invoice_date", ">=", date_from])
    if date_to:
        domain.append(["invoice_date", "<=", date_to])
    if state:
        domain.append(["state", "=", state])
    result = _rpc_call(
        "account.move",
        "search_read",
        [domain],
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


# ---------------------------------------------------------------------------
# MCP tool registry
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_customer",
            description="Search Odoo customers by name or email.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="create_invoice",
            description="Create a draft invoice in Odoo (does not post).",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                            },
                        },
                    },
                    "due_date": {"type": "string"},
                },
                "required": ["customer_id", "line_items", "due_date"],
            },
        ),
        types.Tool(
            name="post_invoice",
            description="Post (finalise) a draft invoice. Irreversible. Requires approval_id. Max 3/hour.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string"},
                    "approval_id": {"type": "string"},
                },
                "required": ["invoice_id", "approval_id"],
            },
        ),
        types.Tool(
            name="create_transaction",
            description="Record a bank transaction in Odoo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                    "payee": {"type": "string"},
                    "reference": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["amount", "date", "payee", "reference", "category"],
            },
        ),
        types.Tool(
            name="sync_transaction",
            description="Sync a bank transaction with its Odoo counterpart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bank_transaction_id": {"type": "string"},
                    "odoo_transaction_id": {"type": "string"},
                },
                "required": ["bank_transaction_id", "odoo_transaction_id"],
            },
        ),
        types.Tool(
            name="list_invoices",
            description="List invoices from Odoo with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "state": {"type": "string", "enum": ["draft", "posted", "cancel"]},
                },
            },
        ),
        types.Tool(
            name="update_expense",
            description="Create or update an employee expense (hr.expense) in Odoo. "
                        "If expense_id is provided, updates that record; otherwise creates a new one. "
                        "Resolves employee and expense-category product by name automatically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Expense description, e.g. 'Team lunch'"},
                    "total_amount": {"type": "number", "description": "Total expense amount including tax"},
                    "expense_id": {"type": "integer", "description": "Existing expense ID to update (omit to create)"},
                    "date": {"type": "string", "description": "Expense date YYYY-MM-DD (default: today)"},
                    "category": {"type": "string", "description": "Expense category/product name, e.g. 'Meals', 'Travel'"},
                    "employee": {"type": "string", "description": "Employee name (default: first employee in system)"},
                    "reference": {"type": "string", "description": "External reference or receipt number"},
                },
                "required": ["name", "total_amount"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_customer":
        result = _tool_get_customer(arguments.get("name"), arguments.get("email"))
        _log_action("odoo_get_customer", str(arguments.get("name") or arguments.get("email", "")), arguments, "auto", {"status": "ok"})
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "create_invoice":
        result = _tool_create_invoice(
            customer_id=arguments["customer_id"],
            line_items=arguments["line_items"],
            due_date=arguments["due_date"],
        )
        _log_action("odoo_create_invoice", arguments["customer_id"], arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "post_invoice":
        result = _tool_post_invoice(
            invoice_id=arguments["invoice_id"],
            approval_id=arguments.get("approval_id", ""),
        )
        _log_action("odoo_post_invoice", arguments["invoice_id"], arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "create_transaction":
        result = _tool_create_transaction(
            amount=arguments["amount"],
            date=arguments["date"],
            payee=arguments["payee"],
            reference=arguments["reference"],
            category=arguments["category"],
        )
        _log_action("odoo_sync", arguments.get("payee", ""), arguments, "auto", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "sync_transaction":
        result = _tool_sync_transaction(
            bank_transaction_id=arguments["bank_transaction_id"],
            odoo_transaction_id=arguments["odoo_transaction_id"],
        )
        _log_action("odoo_sync", arguments["bank_transaction_id"], arguments, "auto", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "list_invoices":
        result = _tool_list_invoices(
            date_from=arguments.get("date_from"),
            date_to=arguments.get("date_to"),
            state=arguments.get("state"),
        )
        _log_action("odoo_list_invoices", "", arguments, "auto", {"status": "ok"})
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "update_expense":
        result = _tool_update_expense(
            name=arguments["name"],
            total_amount=arguments["total_amount"],
            expense_id=arguments.get("expense_id"),
            date=arguments.get("date"),
            category=arguments.get("category"),
            employee=arguments.get("employee"),
            reference=arguments.get("reference"),
        )
        return [types.TextContent(type="text", text=json.dumps(result))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    if not DRY_RUN:
        logger.info("Starting Odoo session authentication...")
        _authenticate()
    else:
        logger.info("DRY_RUN=true — skipping real Odoo authentication (mock uid=1)")
        global _session_uid
        _session_uid = 1

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
