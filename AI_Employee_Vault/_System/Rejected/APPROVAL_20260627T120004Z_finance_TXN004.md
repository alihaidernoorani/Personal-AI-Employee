---
type: approval_request
action: reconcile_transaction
plan_file: PLAN_20260627T120004Z_FINANCE_TXN004_20260627T094821Z.md
reason: "Confirm AWS cloud hosting subscription: -$89.50 (AWS-JUN-2026)"
parameters:
  source_id: TXN004
  payee: AWS
  amount: "-89.50"
  reference: AWS-JUN-2026
  category: subscription
  odoo_move_id: 62
timestamp: 2026-06-27T12:00:04Z
created: 2026-06-27T12:00:04Z
status: rejected
---

> [!caution] ⏳ Pending Approval — RECONCILE TRANSACTION
> **Payee**: AWS · **Amount**: -$89.50 · **Ref**: AWS-JUN-2026
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Financial transaction reconciliation. Per Company Handbook §3, all payment and financial
actions require explicit human approval.

## Action Summary

**Payee**: AWS  
**Amount**: -$89.50  
**Reference**: AWS-JUN-2026  
**Odoo Record**: account.move id=62  
**Action**: Move this file to `_System/Approved/` to confirm reconciliation, or `Rejected/` to flag for review.

```meta-bind-button
id: "approve-APPROVAL-20260627T120004Z-finance-TXN004"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T120004Z-finance-TXN004"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.