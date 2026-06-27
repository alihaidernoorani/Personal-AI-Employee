"""odoo-mcp — MCP server entry point for Odoo 19+ JSON-RPC.

ODOO_DRAFT_ONLY=true (cloud VM): registers only create_invoice + update_expense.
DRY_RUN=true (default): no real Odoo records created.
"""

import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv

load_dotenv()

import odoo_rpc as rpc
from handlers.customer_handlers import tool_get_customer
from handlers.invoice_handlers import tool_create_invoice, tool_post_invoice, tool_list_invoices
from handlers.transaction_handlers import tool_create_transaction, tool_sync_transaction, tool_update_expense

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"
ODOO_DRAFT_ONLY = os.getenv("ODOO_DRAFT_ONLY", "false").lower() == "true"

server = Server("odoo-mcp")

_TOOLS = {
    "get_customer": {"description": "Search Odoo customers by name or email.", "schema": {"type": "object", "properties": {"name": {"type": "string"}, "email": {"type": "string"}}}},
    "create_invoice": {"description": "Create a draft invoice in Odoo.", "schema": {"type": "object", "properties": {"customer_id": {"type": "string"}, "line_items": {"type": "array", "items": {"type": "object", "properties": {"description": {"type": "string"}, "quantity": {"type": "number"}, "unit_price": {"type": "number"}}}}, "due_date": {"type": "string"}}, "required": ["customer_id", "line_items", "due_date"]}},
    "post_invoice": {"description": "Post a draft invoice. Irreversible. Requires approval_id.", "schema": {"type": "object", "properties": {"invoice_id": {"type": "string"}, "approval_id": {"type": "string"}}, "required": ["invoice_id", "approval_id"]}},
    "create_transaction": {"description": "Record a bank transaction in Odoo.", "schema": {"type": "object", "properties": {"amount": {"type": "number"}, "date": {"type": "string"}, "payee": {"type": "string"}, "reference": {"type": "string"}, "category": {"type": "string"}}, "required": ["amount", "date", "payee", "reference", "category"]}},
    "sync_transaction": {"description": "Sync a bank transaction with its Odoo counterpart.", "schema": {"type": "object", "properties": {"bank_transaction_id": {"type": "string"}, "odoo_transaction_id": {"type": "string"}}, "required": ["bank_transaction_id", "odoo_transaction_id"]}},
    "list_invoices": {"description": "List invoices from Odoo with optional filters.", "schema": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "state": {"type": "string", "enum": ["draft", "posted", "cancel"]}}}},
    "update_expense": {"description": "Create or update an employee expense in Odoo.", "schema": {"type": "object", "properties": {"name": {"type": "string"}, "total_amount": {"type": "number"}, "expense_id": {"type": "integer"}, "date": {"type": "string"}, "category": {"type": "string"}, "employee": {"type": "string"}, "reference": {"type": "string"}}, "required": ["name", "total_amount"]}},
}
_DRAFT_ONLY_TOOLS = {"create_invoice", "update_expense"}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    names = _DRAFT_ONLY_TOOLS if ODOO_DRAFT_ONLY else set(_TOOLS)
    return [types.Tool(name=n, description=_TOOLS[n]["description"], inputSchema=_TOOLS[n]["schema"]) for n in names]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if ODOO_DRAFT_ONLY and name not in _DRAFT_ONLY_TOOLS:
        result: dict = {"error": f"'{name}' disabled in ODOO_DRAFT_ONLY mode", "retryable": False}
    elif name == "get_customer":
        result = tool_get_customer(arguments.get("name"), arguments.get("email"), DRY_RUN, lambda: rpc.ensure_auth(DRY_RUN), rpc.rpc_call)
    elif name == "create_invoice":
        result = tool_create_invoice(arguments["customer_id"], arguments["line_items"], arguments["due_date"], DRY_RUN, lambda: rpc.ensure_auth(DRY_RUN), rpc.rpc_call, lambda *a: rpc.log_action(VAULT_PATH, *a))
    elif name == "post_invoice":
        result = tool_post_invoice(arguments["invoice_id"], arguments.get("approval_id", ""), DRY_RUN, lambda: rpc.ensure_auth(DRY_RUN), rpc.rpc_call, lambda *a: rpc.log_action(VAULT_PATH, *a))
    elif name == "create_transaction":
        result = tool_create_transaction(arguments["amount"], arguments["date"], arguments["payee"], arguments["reference"], arguments["category"], DRY_RUN, lambda: rpc.ensure_auth(DRY_RUN), rpc.rpc_call)
        rpc.log_action(VAULT_PATH, "odoo_sync", arguments.get("payee", ""), arguments, "auto", result)
    elif name == "sync_transaction":
        result = tool_sync_transaction(arguments["bank_transaction_id"], arguments["odoo_transaction_id"], DRY_RUN, rpc.rpc_call)
        rpc.log_action(VAULT_PATH, "odoo_sync", arguments["bank_transaction_id"], arguments, "auto", result)
    elif name == "list_invoices":
        result = tool_list_invoices(arguments.get("date_from"), arguments.get("date_to"), arguments.get("state"), DRY_RUN, lambda: rpc.ensure_auth(DRY_RUN), rpc.rpc_call)
    elif name == "update_expense":
        result = tool_update_expense(arguments["name"], arguments["total_amount"], DRY_RUN, lambda: rpc.ensure_auth(DRY_RUN), rpc.rpc_call, lambda *a: rpc.log_action(VAULT_PATH, *a), expense_id=arguments.get("expense_id"), date=arguments.get("date"), category=arguments.get("category"), employee=arguments.get("employee"), reference=arguments.get("reference"))
    else:
        raise ValueError(f"Unknown tool: {name}")
    return [types.TextContent(type="text", text=json.dumps(result))]


async def main():
    if not DRY_RUN:
        rpc.authenticate()
    else:
        logger.info("DRY_RUN=true — mock mode")
        rpc._session_uid = 1
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
