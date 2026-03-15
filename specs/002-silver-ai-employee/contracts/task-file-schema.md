# Contract: Task File Schema (Silver Tier)

Extends Bronze Tier task-file-schema with `email` and `whatsapp` types.

---

## Common Fields (all types)

```yaml
---
type: email | whatsapp | file_drop | action_trigger | error
source: gmail | whatsapp | filesystem | system
received: "2026-03-13T09:00:00Z"   # ISO-8601 UTC
priority: urgent | high | normal | low
status: pending | processing | done
---
```

---

## type: email

```yaml
---
type: email
source: gmail
sender: "alice@example.com"
subject: "Invoice #1001 — Payment Reminder"
body_snippet: "Hi, just following up on the invoice..."
imap_uid: "12345"
received: "2026-03-13T09:00:00Z"
priority: normal
status: pending
---

## Email Summary

[First 300 characters of email body]

## Suggested Actions

- [ ] Draft a reply
- [ ] File the email
```

---

## type: whatsapp

```yaml
---
type: whatsapp
source: whatsapp
sender: "Alice Smith"
message_text: "Hey, are you available for a call tomorrow?"
message_hash: "sha256hex..."
received: "2026-03-13T09:05:00Z"
priority: normal
status: pending
---

## Message

[Full message text]

## Suggested Actions

- [ ] Review message
- [ ] Draft reply (requires approval)
```

---

## type: action_trigger

```yaml
---
type: action_trigger
source: system
action_type: send_email | linkedin_post
approval_file: "APPROVAL_20260313T090500Z_send_email_alice.md"
action_params: '{"to": "alice@example.com", "subject": "Re: Invoice", "body": "...", "reply_to_uid": "12345"}'
received: "2026-03-13T09:10:00Z"
priority: high
status: pending
---

## Action Details

Execute the approved action referenced in `approval_file`.
```
