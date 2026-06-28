---
type: approval_request
action: reconcile_transaction
plan_file: PLAN_20260627T120005Z_FINANCE_TXN005_20260627T094821Z.md
reason: "Confirm and reconcile client payment from New Lead Ltd: +$1200.00 (INV-2026-012)"
parameters:
  source_id: TXN005
  payee: New Lead Ltd
  amount: "+1200.00"
  reference: INV-2026-012
  category: client_payment
  odoo_move_id: 60
timestamp: 2026-06-27T12:00:05Z
created: 2026-06-27T12:00:05Z
status: rejected
---

> [!caution] ⏳ Pending Approval — RECONCILE TRANSACTION
> **Payee**: New Lead Ltd · **Amount**: +$1,200.00 · **Ref**: INV-2026-012
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Financial transaction reconciliation. Per Company Handbook §3, all payment and financial
actions require explicit human approval. Amount $1200.00 exceeds $100 threshold.

## Action Summary

**Payee**: New Lead Ltd  
**Amount**: +$1,200.00  
**Reference**: INV-2026-012  
**Odoo Record**: account.move id=60  
**Action**: Move this file to `_System/Approved/` to confirm reconciliation, or `Rejected/` to flag for review.

```meta-bind-button
id: "approve-APPROVAL-20260627T120005Z-finance-TXN005"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T120005Z-finance-TXN005"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.