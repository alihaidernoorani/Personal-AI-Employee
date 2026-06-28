---
type: approval_request
action: send_email
plan_file: "PLAN_20260321T120001Z_TEST_scheduler_20260321T000000Z.md"
reason: "Reply to email from scheduler-test@example.com regarding: Scheduler Test Email"
parameters:
  to: "scheduler-test@example.com"
  subject: "Re: Scheduler Test Email"
  body: |
    Hi,

    Thank you for the test message. The Personal AI Employee has received and processed
    your scheduler test email successfully. The process-needs-action workflow was triggered
    as expected.

    If you have any further questions or need to adjust the scheduler configuration,
    feel free to reach out.

    Best regards,
    AI Employee
  reply_to_uid: null
timestamp: "2026-03-21T12:00:01Z"
created: "2026-03-21T12:00:01Z"
status: pending
---

> [!caution] ⏳ Pending Approval — SEND EMAIL
> **To**: scheduler-test@example.com · **Subject**: Re: Scheduler Test Email
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook
Human-in-the-Loop Rules (Section 3), all outbound email requires explicit human approval.

## Action Summary

**To**: scheduler-test@example.com
**Subject**: Re: Scheduler Test Email
**Action**: Move this file to `_System/Approved/` to send, or `Rejected/` to discard.

```meta-bind-button
id: "approve-APPROVAL-20260321T120001Z-email-scheduler-test-example-com"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260321T120001Z-email-scheduler-test-example-com"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.