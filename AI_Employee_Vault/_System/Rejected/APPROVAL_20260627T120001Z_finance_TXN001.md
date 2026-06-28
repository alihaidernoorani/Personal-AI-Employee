---
type: approval_request
action: reconcile_transaction
plan_file: PLAN_20260627T120001Z_FINANCE_TXN001_20260627T094821Z.md
reason: "Confirm and reconcile client payment from Acme Corp Ltd: +$4500.00 (INV-2026-010)"
parameters:
  source_id: TXN001
  payee: Acme Corp Ltd
  amount: "+4500.00"
  reference: INV-2026-010
  category: client_payment
  odoo_move_id: 58
timestamp: 2026-06-27T12:00:01Z
created: 2026-06-27T12:00:01Z
status: rejected
---

> [!caution] ⏳ Pending Approval — RECONCILE TRANSACTION
> **Payee**: Acme Corp Ltd · **Amount**: +$4,500.00 · **Ref**: INV-2026-010
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Financial transaction reconciliation. Per Company Handbook §3, all payment and financial
actions require explicit human approval. Amount $4500.00 exceeds $100 threshold.

## Action Summary

**Payee**: Acme Corp Ltd  
**Amount**: +$4,500.00  
**Reference**: INV-2026-010  
**Odoo Record**: account.move id=58  
**Action**: Move this file to `_System/Approved/` to confirm reconciliation, or `Rejected/` to flag for review.

```meta-bind-button
id: "approve-APPROVAL-20260627T120001Z-finance-TXN001"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T120001Z-finance-TXN001"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.