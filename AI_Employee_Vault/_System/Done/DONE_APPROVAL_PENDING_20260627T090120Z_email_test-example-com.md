---
type: approval_request
action: send_email
plan_file: "PLAN_20260627T090120Z_EMAIL_20260627T085953Z_test-verification.md"
reason: "Reply to email from test@example.com regarding: Test Verification Email"
parameters:
  to: "test@example.com"
  subject: "Re: Test Verification Email"
  body: |
    Hi,

    Thank you for reaching out. I can confirm receipt of your test email. Everything is working correctly on our end.

    Please don't hesitate to contact us if you need anything further.

    Best regards,
    Ali Haider Noorani
  reply_to_uid: "TEST_001"
timestamp: "2026-06-27T09:01:20Z"
status: pending
---

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook
Human-in-the-Loop Rules, all outbound email requires explicit human approval.

## Action Summary

**To**: test@example.com  
**Subject**: Re: Test Verification Email  
**Action**: Move this file to `Approved/` to send, or `Rejected/` to discard.
