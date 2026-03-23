# Odoo JSON-RPC Patterns

All requests go to `POST /jsonrpc` with body:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "service": "<service>",
    "method": "<method>",
    "args": [...]
  }
}
```

## Authentication

```python
uid = jsonrpc("common", "authenticate", [DB, USERNAME, PASSWORD, {}])
```

## Read records

```python
# Search
ids = jsonrpc("object", "execute_kw", [
    DB, uid, PASSWORD,
    "account.move", "search",
    [[["move_type", "=", "out_invoice"], ["state", "=", "posted"]]]
])

# Read fields
records = jsonrpc("object", "execute_kw", [
    DB, uid, PASSWORD,
    "account.move", "read",
    [ids],
    {"fields": ["name", "partner_id", "amount_total", "state"]}
])
```

## List invoices

```python
invoices = jsonrpc("object", "execute_kw", [
    DB, uid, PASSWORD,
    "account.move", "search_read",
    [[["move_type", "=", "out_invoice"]]],
    {"fields": ["name", "partner_id", "amount_total", "state", "invoice_date"], "limit": 50}
])
```

## Post (confirm) a draft invoice

```python
# Changes state from draft -> posted
jsonrpc("object", "execute_kw", [
    DB, uid, PASSWORD,
    "account.move", "action_post",
    [[invoice_id]]
])
```

## Search partner by name

```python
partners = jsonrpc("object", "execute_kw", [
    DB, uid, PASSWORD,
    "res.partner", "search_read",
    [[["name", "ilike", "Acme"]]],
    {"fields": ["id", "name", "email"], "limit": 5}
])
```

## Create partner

```python
partner_id = jsonrpc("object", "execute_kw", [
    DB, uid, PASSWORD,
    "res.partner", "create",
    [{"name": "Acme Corp", "customer_rank": 1}]
])
```

## ORM commands for one2many fields

| Tuple | Meaning |
|-------|---------|
| `(0, 0, vals)` | Create new record with vals |
| `(1, id, vals)` | Update existing record id with vals |
| `(2, id, 0)` | Delete record id |
| `(4, id, 0)` | Link existing record id |
| `(5, 0, 0)` | Unlink all records |
| `(6, 0, [ids])` | Replace all with given ids |
