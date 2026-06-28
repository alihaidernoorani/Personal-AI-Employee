---
type: approval_request
action: send_email
plan_file: "PLAN_20260321T180000Z_FILE_20260320T222328Z_client_email_march_payment.md"
reason: "Reply to email from bilal.client@example.com regarding: March Payment Confirmation"
parameters:
  to: "bilal.client@example.com"
  subject: "Re: March Payment Confirmation"
  body: |
    Hi Bilal,

    Thank you for confirming! We have received your notification of the $2,000 payment for the March project.

    We will verify the funds on our end and send you a formal invoice shortly. Please let me know if you need anything in the meantime.

    Best regards,
    AI Employee (on behalf of the team)
  reply_to_uid: "null"
timestamp: "2026-03-21T18:00:00Z"
created: "2026-03-21T18:00:00Z"
status: pending
---

> [!caution] ⏳ Pending Approval — SEND EMAIL
> **To**: bilal.client@example.com · **Subject**: Re: March Payment Confirmation
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook
Human-in-the-Loop Rules, all outbound email requires explicit human approval.

## Action Summary

**To**: bilal.client@example.com
**Subject**: Re: March Payment Confirmation
**Action**: Move this file to `_System/Approved/` to send, or `Rejected/` to discard.

```meta-bind-button
id: "approve-APPROVAL-20260321T180000Z-email-bilal-client-example-com"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260321T180000Z-email-bilal-client-example-com"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.