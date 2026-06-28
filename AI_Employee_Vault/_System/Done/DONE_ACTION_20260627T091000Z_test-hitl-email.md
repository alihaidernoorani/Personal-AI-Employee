---
type: action_trigger
action_type: send_email
priority: normal
approval_file: APPROVAL_20260627T090120Z_email_test-example-com.md
action_params: '{"to": "test@example.com", "subject": "Re: Test Verification Email", "body": "Hi,\n\nThank you for reaching out. This is a DRY_RUN test of the execute-plan skill.\n\nBest regards,\nAI Employee", "reply_to_uid": "TEST_001"}'
received: 2026-06-27T09:10:00Z
---

## Action Trigger: Send Email (T036 HITL test)

This action_trigger was created to test the HITL approval → execute-plan flow.
The approval file has been moved to Approved/.
execute-plan should process this with DRY_RUN=true.
