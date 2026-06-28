---
type: approval_request
action: send_email
plan_file: PLAN_20260627T123500Z_EMAIL_T073_smoke-test.md
reason: "T073 smoke test: Reply to smoketest@example.com"
parameters:
  to: smoketest@example.com
  subject: "Re: T073 Smoke Test Email"
  body: T073 smoke test reply
  reply_to_uid: T073_001
timestamp: 2026-06-27T12:35:10Z
created: 2026-06-27T12:35:10Z
status: rejected
---

> [!caution] ⏳ Pending Approval — SEND EMAIL
> **To**: smoketest@example.com · **Subject**: Re: T073 Smoke Test Email
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

T073 smoke test email approval.

```meta-bind-button
id: "approve-APPROVAL-20260627T123500Z-email-smoketest-example-com"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T123500Z-email-smoketest-example-com"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.