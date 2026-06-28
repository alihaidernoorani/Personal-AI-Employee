---
type: approval_request
action: reconcile_transaction
plan_file: PLAN_20260627T120002Z_FINANCE_TXN002_20260627T094821Z.md
reason: "Confirm subscription payment to Adobe Creative Cloud: -$59.99 (SUB-ADOBE-JUN)"
parameters:
  source_id: TXN002
  payee: Adobe Creative Cloud
  amount: "-59.99"
  reference: SUB-ADOBE-JUN
  category: subscription
  odoo_move_id: 61
timestamp: 2026-06-27T12:00:02Z
created: 2026-06-27T12:00:02Z
status: rejected
---

> [!caution] ⏳ Pending Approval — RECONCILE TRANSACTION
> **Payee**: Adobe Creative Cloud · **Amount**: -$59.99 · **Ref**: SUB-ADOBE-JUN
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Financial transaction reconciliation. Per Company Handbook §3, all payment and financial
actions require explicit human approval.

## Action Summary

**Payee**: Adobe Creative Cloud  
**Amount**: -$59.99  
**Reference**: SUB-ADOBE-JUN  
**Odoo Record**: account.move id=61  
**Action**: Move this file to `_System/Approved/` to confirm reconciliation, or `Rejected/` to flag for review.

```meta-bind-button
id: "approve-APPROVAL-20260627T120002Z-finance-TXN002"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T120002Z-finance-TXN002"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.