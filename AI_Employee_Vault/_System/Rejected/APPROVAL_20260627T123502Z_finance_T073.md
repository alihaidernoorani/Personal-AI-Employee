---
type: approval_request
action: reconcile_transaction
plan_file: PLAN_20260627T123502Z_FINANCE_T073_smoke-test.md
reason: "T073 smoke test: Confirm Smoke Test Corp +$999.00"
parameters:
  source_id: T073_TXN
  payee: Smoke Test Corp
  amount: "+999.00"
  reference: T073-SMOKE
timestamp: 2026-06-27T12:35:12Z
created: 2026-06-27T12:35:12Z
status: rejected
---

> [!caution] ⏳ Pending Approval — RECONCILE TRANSACTION
> **Payee**: Smoke Test Corp · **Amount**: +$999.00 · **Ref**: T073-SMOKE
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

T073 smoke test finance approval.

```meta-bind-button
id: "approve-APPROVAL-20260627T123502Z-finance-T073"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T123502Z-finance-T073"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.