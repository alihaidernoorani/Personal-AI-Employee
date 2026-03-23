#!/usr/bin/env python3
"""
Odoo Invoice Creator — JSON-RPC
Creates a draft customer invoice in Odoo via the /jsonrpc endpoint.

Usage:
    python create_invoice.py --customer "Acme Corp" --amount 1500.00
    python create_invoice.py --customer "Acme Corp" --amount 1500.00 --description "Consulting"
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


# ---------------------------------------------------------------------------
# Config — reads from .env if present, falls back to Docker-compose defaults
# ---------------------------------------------------------------------------

def _load_env() -> None:
    """Load .env from project root (two levels up from this script)."""
    env_path = Path(__file__).resolve().parents[4] / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_env()

ODOO_URL      = os.getenv("ODOO_URL",      "http://localhost:8069")
ODOO_DB       = os.getenv("ODOO_DB",       "odoo")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
JSONRPC_URL   = ODOO_URL.rstrip("/") + "/jsonrpc"


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

class OdooError(Exception):
    pass


_req_id = 0


def _jsonrpc(service: str, method: str, args: list) -> object:
    """Send a single JSON-RPC 2.0 request and return the result."""
    global _req_id
    _req_id += 1
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method":  "call",
        "id":      _req_id,
        "params": {
            "service": service,
            "method":  method,
            "args":    args,
        },
    }).encode()

    req = urllib.request.Request(
        JSONRPC_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise OdooError(
            f"Cannot reach Odoo at {JSONRPC_URL} — {exc.reason}. "
            "Is Docker running? (`docker ps`)"
        ) from exc

    if "error" in body:
        err = body["error"]
        msg = err.get("data", {}).get("message") or err.get("message") or str(err)
        raise OdooError(f"Odoo RPC error: {msg}")

    return body["result"]


def _call_kw(uid: int, model: str, method: str, args: list, kwargs: dict = None) -> object:
    """Convenience wrapper for object/execute_kw calls."""
    return _jsonrpc("object", "execute_kw", [
        ODOO_DB, uid, ODOO_PASSWORD,
        model, method, args, kwargs or {},
    ])


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate() -> int:
    """Authenticate and return uid. Raises OdooError on failure."""
    uid = _jsonrpc("common", "authenticate", [
        ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {},
    ])
    if not uid:
        raise OdooError(
            f"Authentication failed for user '{ODOO_USERNAME}' on db '{ODOO_DB}' "
            f"at {ODOO_URL}. Check credentials."
        )
    return uid


# ---------------------------------------------------------------------------
# Partner (customer) resolution
# ---------------------------------------------------------------------------

def resolve_partner(uid: int, name: str) -> tuple[int, str]:
    """
    Find a res.partner by name (case-insensitive ilike).
    Creates one if not found.
    Returns (partner_id, partner_name).
    """
    results = _call_kw(uid, "res.partner", "search_read",
        [[["name", "ilike", name]]],
        {"fields": ["id", "name"], "limit": 1},
    )
    if results:
        p = results[0]
        return p["id"], p["name"]

    # Create new partner
    partner_id = _call_kw(uid, "res.partner", "create",
        [{"name": name, "customer_rank": 1}],
    )
    return partner_id, name


# ---------------------------------------------------------------------------
# Invoice creation
# ---------------------------------------------------------------------------

def create_invoice(
    customer: str,
    amount: float,
    description: str = "Service",
) -> dict:
    """
    Create a draft customer invoice (account.move, move_type=out_invoice).
    Returns a dict with invoice_id, invoice_name, partner_id, partner_name, amount.
    """
    uid = authenticate()
    partner_id, partner_name = resolve_partner(uid, customer)

    invoice_vals = {
        "move_type":  "out_invoice",
        "partner_id": partner_id,
        "invoice_line_ids": [
            # (0, 0, vals) is Odoo's ORM command to create a new record
            (0, 0, {
                "name":       description,
                "quantity":   1.0,
                "price_unit": amount,
            })
        ],
    }

    invoice_id = _call_kw(uid, "account.move", "create", [invoice_vals])

    # Read back the generated reference name
    records = _call_kw(uid, "account.move", "read",
        [[invoice_id]],
        {"fields": ["name", "state", "amount_total"]},
    )
    invoice_name = records[0]["name"] if records else str(invoice_id)

    return {
        "status":       "ok",
        "invoice_id":   invoice_id,
        "invoice_name": invoice_name,
        "partner_id":   partner_id,
        "partner_name": partner_name,
        "amount":       amount,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a draft customer invoice in Odoo via JSON-RPC"
    )
    parser.add_argument("--customer",    required=True, help="Customer name")
    parser.add_argument("--amount",      required=True, type=float, help="Invoice amount")
    parser.add_argument("--description", default="Service", help="Line description")
    parser.add_argument("--url",      default=None, help="Override ODOO_URL")
    parser.add_argument("--db",       default=None, help="Override ODOO_DB")
    parser.add_argument("--username", default=None, help="Override ODOO_USERNAME")
    parser.add_argument("--password", default=None, help="Override ODOO_PASSWORD")
    args = parser.parse_args()

    # Apply CLI overrides
    global ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, JSONRPC_URL
    if args.url:
        ODOO_URL    = args.url
        JSONRPC_URL = ODOO_URL.rstrip("/") + "/jsonrpc"
    if args.db:       ODOO_DB       = args.db
    if args.username: ODOO_USERNAME = args.username
    if args.password: ODOO_PASSWORD = args.password

    try:
        result = create_invoice(
            customer=args.customer,
            amount=args.amount,
            description=args.description,
        )
        print(json.dumps(result, indent=2))
    except OdooError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        sys.exit(1)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"Unexpected: {exc}"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
