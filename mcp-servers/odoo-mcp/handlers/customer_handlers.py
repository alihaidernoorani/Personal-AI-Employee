"""customer_handlers.py — Odoo customer lookup handler."""

import logging

logger = logging.getLogger(__name__)


def tool_get_customer(
    name: str | None,
    email: str | None,
    dry_run: bool,
    ensure_auth_fn,
    rpc_call_fn,
) -> list | dict:
    if not name and not email:
        return {"error": "At least one of name or email is required", "retryable": False}
    if dry_run:
        return {
            "dry_run": True,
            "customers": [{"id": "1", "name": name or "Test Customer", "email": email or "test@example.com"}],
        }
    if not ensure_auth_fn():
        return {"error": "AUTH_FAILED", "retryable": False}
    domain: list = []
    if name:
        domain.append(["name", "ilike", name])
    if email:
        domain.append(["email", "ilike", email])
    if len(domain) > 1:
        domain = ["|"] + domain
    result = rpc_call_fn("res.partner", "search_read", [domain], {"fields": ["id", "name", "email"], "limit": 20})
    if "error" in result:
        return result
    return [
        {"id": str(r["id"]), "name": r["name"], "email": r.get("email", "")}
        for r in (result.get("result") or [])
    ]
