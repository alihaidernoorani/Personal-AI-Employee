---
name: finance-triage
description: |
  Processes FINANCE_*.md task files from AI_Employee_Vault/Needs_Action/.
  For each finance task: reads Company_Handbook.md permission boundaries,
  creates a Plans/PLAN_*.md, syncs transactions to Odoo via odoo-mcp MCP tools,
  and routes high-value or new-payee transactions to Pending_Approval/.
  Auto-approves: recurring payments <$50 to known payees (creates Odoo record directly).
  Requires approval: any payment >$100, new payees, invoice posting.
  On Odoo MCP unavailability: writes ERROR_*.md and schedules retry.
  Use this skill whenever FINANCE_*.md files appear in Needs_Action/, or on a
  scheduled basis after the finance watcher runs.
  Triggered by: "run finance-triage skill", "process finance tasks", "sync transactions".
---

# Finance Triage

Process finance task files and sync transactions to Odoo with appropriate
approval routing based on amount and payee thresholds.

---

## Step 1 — Read Rules

Read `AI_Employee_Vault/Company_Handbook.md` for:
- Known payees list
- Payment auto-approve thresholds ($50 recurring, $100 new/one-off)
- Finance categorisation rules

Read `AI_Employee_Vault/Business_Goals.md` for active project budgets and
expected recurring charges.

---

## Step 2 — Inventory Finance Tasks

List all files in `AI_Employee_Vault/Needs_Action/` matching `FINANCE_*.md`.
Sort by `created` timestamp ascending (oldest first).

If none found, output:
```
No FINANCE_*.md files to process.
<promise>TASK_COMPLETE</promise>
```

---

## Step 3 — Process Each Finance Task

For each `FINANCE_*.md`, perform the following steps.

### 3a. Parse the Task File

Extract from YAML frontmatter:
- `amount` — transaction amount (decimal, positive = income, negative = expense)
- `payee` — payee/merchant name
- `reference` — bank reference or transaction ID
- `date` — transaction date (YYYY-MM-DD)
- `category` — initial category guess from watcher (may be null)
- `source_id` — unique transaction ID from bank source
- `is_recurring` — true/false (set by finance watcher if known)
- `known_payee` — true/false (set by finance watcher against known-payees list)

### 3b. Determine Approval Requirement

Apply permission boundaries:

| Condition | Action |
|-----------|--------|
| Income (amount > 0) | Auto-approve: create Odoo transaction record |
| Expense, recurring, known payee, abs(amount) < $50 | Auto-approve: create Odoo transaction record |
| Expense, known payee, abs(amount) $50–$100 | Auto-approve: create Odoo transaction record (log note: "borderline threshold") |
| Expense, abs(amount) > $100 | Requires approval: write APPROVAL_*.md |
| Expense, unknown payee (any amount) | Requires approval: write APPROVAL_*.md |
| Invoice posting (post_invoice) | Always requires approval regardless of amount |

### 3c. Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_finance_<source_id_slug>.md`:

```markdown
---
type: plan
source_task: <FINANCE_*.md filename>
created_at: <ISO-8601 UTC timestamp>
requires_approval: <true|false>
status: <awaiting_approval|executing>
transaction_amount: <amount>
transaction_payee: <payee>
transaction_date: <date>
odoo_action: <create_transaction|create_invoice|none>
---

## Summary

Finance transaction: <payee> <amount> on <date>

## Decision Rationale

<Why auto-approved or why approval is required, referencing specific threshold>

## Actions

- [ ] <Create Odoo transaction record / Route to Pending_Approval>
- [ ] Move task to Done/
- [ ] Update Bank_Transactions.md sync status

## Risk Assessment

<Amount threshold, payee status, any anomalies noticed>
```

### 3d. Auto-Approve Path (no approval required)

Call `odoo-mcp` `create_transaction` with:
- `date`: transaction date
- `amount`: transaction amount
- `payee`: payee name
- `reference`: bank reference
- `category`: category from task or inferred

If `DRY_RUN=true`: log the intended call, do not call the MCP tool.

On success: proceed to Step 4.
On failure (MCP error): follow the Odoo Error Path (Step 3f).

### 3e. Approval Required Path

Write `AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_finance_<slug>.md`:

```markdown
---
type: approval_request
action: odoo_sync
plan_file: "PLAN_<timestamp>_finance_<slug>.md"
reason: "<threshold exceeded / unknown payee / invoice posting>"
parameters:
  transaction_date: "<YYYY-MM-DD>"
  amount: <decimal>
  payee: "<payee name>"
  reference: "<bank reference>"
  category: "<category>"
  odoo_action: "create_transaction"
risk_class: <medium|high>
payment_amount: <decimal>
known_payee: <true|false>
is_recurring: <true|false>
timestamp: "<ISO-8601 UTC>"
status: pending
---

## Why Approval is Required

<Specific reason: amount > $100 / unknown payee / invoice posting>

## Transaction Details

| Field | Value |
|-------|-------|
| Date | <date> |
| Amount | <amount> |
| Payee | <payee> |
| Reference | <reference> |
| Category | <category> |

## Action
Move this file to `Approved/` to sync to Odoo, or `Rejected/` to skip this transaction.
```

### 3f. Odoo Error Path

If any `odoo-mcp` call fails after 3 retries (exponential backoff 1s/2s/4s):

1. Write `AI_Employee_Vault/Needs_Action/ERROR_<ts>_odoo-sync-<source_id_slug>.md`:

```markdown
---
type: error
error_type: odoo_sync_failure
source_task: <FINANCE_*.md filename>
transaction_ref: <reference>
timestamp: <ISO-8601Z>
retry_count: 3
---

## Error: Odoo Sync Failed

Transaction <payee> <amount> on <date> could not be synced to Odoo
after 3 attempts.

## Recommended Action

1. Check Odoo MCP server status: `python mcp-servers/odoo-mcp/server.py`
2. Verify ODOO_URL/ODOO_DB/.env credentials
3. Re-run finance-triage after Odoo is reachable
```

2. Do NOT move the source `FINANCE_*.md` to `Done/` — leave it in `Needs_Action/`
   so the next finance-triage run can retry it.
3. Log the failure and continue to the next task.

---

## Step 4 — Move Task to Done

After a successful Plan + (Odoo sync OR approval file written):

Move `AI_Employee_Vault/Needs_Action/FINANCE_<id>.md`
→ `AI_Employee_Vault/Done/DONE_FINANCE_<id>.md`

---

## Step 5 — Update Bank_Transactions.md Sync Status

After each transaction is processed, append a sync status note to
`AI_Employee_Vault/Bank_Transactions.md` for the matching row:

- Auto-synced: `| <date> | <payee> | <amount> | synced_to_odoo |`
- Pending approval: `| <date> | <payee> | <amount> | pending_approval |`
- Sync failed: `| <date> | <payee> | <amount> | sync_failed |`

---

## Step 6 — Log Each Transaction

Append one NDJSON line per processed transaction to
`AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "finance_triage",
  "actor": "claude_code",
  "target": "<payee>",
  "parameters": {
    "amount": 0.00,
    "date": "<YYYY-MM-DD>",
    "reference": "<bank_ref>",
    "odoo_action": "create_transaction",
    "plan_file": "<PLAN_*.md>",
    "approval_file": "<APPROVAL_*.md or null>"
  },
  "approval_status": "auto | deferred | failed",
  "approved_by": "system | pending | null",
  "result": "success | deferred | failure"
}
```

---

## Completion Signal

When all `FINANCE_*.md` files are processed, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
