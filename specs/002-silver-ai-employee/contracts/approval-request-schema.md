# Contract: Approval Request Schema

Files written to `AI_Employee_Vault/Pending_Approval/`.

**Filename**: `APPROVAL_<YYYYMMDDTHHMMSSz>_<action-type>_<slug>.md`

---

## type: send_email

```yaml
---
type: approval_request
action: send_email
plan_file: "PLAN_20260313T090000Z_EMAIL_invoice_reminder.md"
reason: "Reply to Alice Smith's invoice enquiry per Company_Handbook communication rules"
parameters:
  to: "alice@example.com"
  subject: "Re: Invoice #1001 — Payment Reminder"
  body: |
    Hi Alice,

    Thank you for following up. The payment for Invoice #1001 has been processed
    and you should see it reflected within 3–5 business days.

    Best regards,
    [Your Name]
  reply_to_uid: "12345"
timestamp: "2026-03-13T09:05:00Z"
status: pending
---

## Why Approval is Required

Sending an email is an external communication action. Per Company_Handbook §3
(Human-in-the-Loop Rules), all outbound email requires explicit human approval.

## Action Summary

**To**: alice@example.com
**Subject**: Re: Invoice #1001 — Payment Reminder
**Action**: Move this file to `Approved/` to send, or `Rejected/` to discard.
```

---

## type: linkedin_post

```yaml
---
type: approval_request
action: linkedin_post
plan_file: "PLAN_20260313T080000Z_linkedin.md"
reason: "Weekly LinkedIn lead-generation post per Business_Goals.md schedule"
parameters:
  post_content: |
    🚀 Exciting news for businesses looking to scale with AI...

    [Full 100–300 word post content here]

    #AI #BusinessAutomation #DigitalTransformation
timestamp: "2026-03-13T08:00:00Z"
status: pending
---

## Why Approval is Required

Publishing to LinkedIn is an external, irreversible action. Human review ensures
the content is accurate, on-brand, and appropriately timed.

## Action Summary

**Platform**: LinkedIn
**Post length**: ~250 words
**Action**: Move this file to `Approved/` to publish, or `Rejected/` to discard.
```

---

## Approval Workflow

```
Created in Pending_Approval/APPROVAL_*.md
        │
   Human reviews content
        │
   ┌────┴────┐
   ▼         ▼
Approved/  Rejected/
   │
   ApprovalWatcher detects
   │
   Needs_Action/ACTION_*.md (trigger)
   │
   execute-plan skill
   │
   MCP call → Done/
```
