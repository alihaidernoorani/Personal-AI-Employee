---
type: approval_request
action: reconcile_transaction
plan_file: PLAN_20260627T120003Z_FINANCE_TXN003_20260627T094821Z.md
reason: "Confirm and reconcile client payment from TechStart Solutions: +$2800.00 (INV-2026-011)"
parameters:
  source_id: TXN003
  payee: TechStart Solutions
  amount: "+2800.00"
  reference: INV-2026-011
  category: client_payment
  odoo_move_id: 59
timestamp: 2026-06-27T12:00:03Z
created: 2026-06-27T12:00:03Z
status: rejected
---

> [!caution] ⏳ Pending Approval — RECONCILE TRANSACTION
> **Payee**: TechStart Solutions · **Amount**: +$2,800.00 · **Ref**: INV-2026-011
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Financial transaction reconciliation. Per Company Handbook §3, all payment and financial
actions require explicit human approval. Amount $2800.00 exceeds $100 threshold.

## Action Summary

**Payee**: TechStart Solutions  
**Amount**: +$2,800.00  
**Reference**: INV-2026-011  
**Odoo Record**: account.move id=59  
**Action**: Move this file to `_System/Approved/` to confirm reconciliation, or `Rejected/` to flag for review.

```meta-bind-button
id: "approve-APPROVAL-20260627T120003Z-finance-TXN003"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T120003Z-finance-TXN003"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.