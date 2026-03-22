# Contract: Odoo MCP

**Server**: `mcp-servers/odoo-mcp/server.py` | **Transport**: stdio | **Runtime**: Python 3.13+
**Status**: ❌ To build.
**Target**: Odoo Community 19+ | **API**: External JSON-RPC (`/web/dataset/call_kw`)

## Responsibilities
All Odoo 19+ interactions: invoice lifecycle, transaction tracking, customer lookup.

## Authentication
Session-based via `/web/session/authenticate`. Server authenticates at startup; re-authenticates automatically on `session.invalid`. Credentials from `.env` (`ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`).

## Tools

### `create_invoice`
**Input**: `{ customer_id: string, line_items: [{ description: string, quantity: number, unit_price: number }], due_date: string }`
**Output (success)**: `{ invoice_id: string, status: "draft" }`
**Output (error)**: `{ error: string, odoo_error_code?: string, retryable: boolean }`
**Note**: Creates invoice in `draft` state. Does not post. Posting requires separate `post_invoice` call after approval.

### `post_invoice`
**Input**: `{ invoice_id: string, approval_id: string }`
**Output (success)**: `{ invoice_id: string, state: "posted" }`
**Output (error)**: `{ error: string, odoo_error_code?: string, retryable: boolean }`
**Note**: Irreversible action. Requires `approval_id` from a file in `Approved/`. Counts against payment rate limit (3/hour).

### `create_transaction`
**Input**: `{ amount: number, date: string, payee: string, reference: string, category: string }`
**Output (success)**: `{ transaction_id: string }`
**Output (error)**: `{ error: string, odoo_error_code?: string, retryable: boolean }`

### `sync_transaction`
**Input**: `{ bank_transaction_id: string, odoo_transaction_id: string }`
**Output (success)**: `{ synced: true }`
**Output (error)**: `{ error: string, retryable: boolean }`

### `get_customer`
**Input**: `{ name?: string, email?: string }` (at least one required)
**Output (success)**: `[{ id: string, name: string, email: string }]`
**Output (error)**: `{ error: string, retryable: boolean }`

### `list_invoices`
**Input**: `{ date_from?: string, date_to?: string, state?: "draft" | "posted" | "cancel" }`
**Output (success)**: `[{ invoice_id: string, customer: string, amount: number, state: string, due_date: string }]`
**Output (error)**: `{ error: string, retryable: boolean }`

## Rate Limit
`post_invoice` and payment-related calls: max 3/hour (shared counter with Email MCP payment category).

## Error Codes
| Code | Meaning | Retryable |
|---|---|---|
| `AUTH_FAILED` | Session expired, re-auth failed | false |
| `APPROVAL_REQUIRED` | No approval_id on post_invoice | false |
| `ODOO_UNAVAILABLE` | Odoo server unreachable | true |
| `RECORD_NOT_FOUND` | Customer/invoice ID invalid | false |
| `RECORD_CONFLICT` | Duplicate or conflicting record | false |
| `RATE_LIMIT_EXCEEDED` | Payment rate limit hit | false |
