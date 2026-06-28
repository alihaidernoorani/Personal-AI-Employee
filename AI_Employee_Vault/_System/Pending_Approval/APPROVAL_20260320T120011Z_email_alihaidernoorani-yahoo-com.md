---
type: approval_request
action: send_email
plan_file: "PLAN_20260320T120011Z_GMAIL_20260320T082255Z_urgent-invoice-payment-reminder.md"
reason: "Reply to email from alihaidernoorani@yahoo.com regarding: Urgent: Invoice Payment Reminder"
parameters:
  to: "alihaidernoorani@yahoo.com"
  subject: "Re: Urgent: Invoice Payment Reminder"
  body: |
    Hi Ali Haider,

    Thank you for the reminder. I've received your message regarding the pending invoice payment. I will review the invoice details and confirm the payment status shortly.

    Could you please resend the invoice or reference the specific invoice number so I can prioritize this? I want to ensure this is resolved promptly.

    Best regards,
    Ali Haider Noorani
  reply_to_uid: "19d0a55e0951f46e"
timestamp: "2026-03-20T12:00:11Z"
created: "2026-03-20T12:00:11Z"
status: pending
---

> [!caution] ⏳ Pending Approval — SEND EMAIL
> **To**: alihaidernoorani@yahoo.com · **Subject**: Re: Urgent: Invoice Payment Reminder
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook Human-in-the-Loop Rules §3, all outbound email requires explicit human approval. Additionally, this email concerns a financial matter (pending invoice payment), which requires extra caution per Financial Rule §2.

## Action Summary

**To**: alihaidernoorani@yahoo.com
**Subject**: Re: Urgent: Invoice Payment Reminder
**Action**: Move this file to `_System/Approved/` to send, or `Rejected/` to discard.

> **Note**: Before approving, review the full email thread in Gmail (msg_id: 19d0a55e0951f46e) to confirm invoice details. Do not initiate any payment without a separate approval per Financial Rule §2.

```meta-bind-button
id: "approve-APPROVAL-20260320T120011Z-email-alihaidernoorani-yahoo-com"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260320T120011Z-email-alihaidernoorani-yahoo-com"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.