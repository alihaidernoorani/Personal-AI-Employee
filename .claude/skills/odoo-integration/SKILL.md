---
name: odoo-integration
description: Odoo accounting skill for creating invoices and managing customers via the Odoo JSON-RPC API. Use when asked to create an invoice, look up a customer, post/confirm an invoice, or perform any Odoo accounting operation. Triggered by requests like "create an invoice for X", "add invoice for customer Y for amount Z", or "run odoo-integration".
---

# Odoo Integration Skill

Performs Odoo accounting operations via JSON-RPC against a local or remote Odoo instance.

## Configuration

| Variable       | Default                  |
|----------------|--------------------------|
| ODOO_URL       | http://localhost:8069    |
| ODOO_DB        | odoo                     |
| ODOO_USERNAME  | admin                    |
| ODOO_PASSWORD  | admin                    |

Read these from `.env` if present; fall back to the defaults above.

## Supported Actions

### create_invoice

Creates a draft customer invoice in Odoo.

**Parameters:**
- `customer` (str) - customer name or ID. If a string name is given, look up or create the partner first.
- `amount` (float) - invoice line amount (unit price)
- `description` (str, optional) - product/service description, defaults to "Service"
- `currency` (str, optional) - currency code, defaults to the company default

**Workflow:**
1. Authenticate via JSON-RPC (`/web/dataset/call_kw`, model `res.users`)
2. Resolve customer name to `partner_id` (search `res.partner` by name; create if not found)
3. Create `account.move` record with `move_type="out_invoice"` and one `invoice_line_ids` entry
4. Return the new invoice ID and reference number

Execute by running the bundled script:

```bash
python .claude/skills/odoo-integration/scripts/create_invoice.py \
  --customer "Acme Corp" \
  --amount 1500.00 \
  --description "Consulting services"
```

## Error Handling

- **Authentication failure** - print credentials and URL, raise immediately (do not retry)
- **Partner not found** - create a new `res.partner` record automatically
- **JSON-RPC error** (fault code in response) - raise `OdooError` with the fault string
- **Connection refused** - surface the URL and advise checking Docker status

## Output

On success the script prints JSON to stdout:

```json
{
  "status": "ok",
  "invoice_id": 42,
  "invoice_name": "INV/2026/00001",
  "partner_id": 7,
  "partner_name": "Acme Corp",
  "amount": 1500.0
}
```

On failure it prints JSON with `"status": "error"` and an `"error"` key, then exits with code 1.

## Reference

See `scripts/create_invoice.py` for the full implementation.
For additional Odoo JSON-RPC patterns (list invoices, post invoice, search partners) see `references/jsonrpc-patterns.md`.
