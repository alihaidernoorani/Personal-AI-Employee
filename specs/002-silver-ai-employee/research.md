# Research: Silver Tier Functional Assistant

**Feature**: 002-silver-ai-employee
**Date**: 2026-03-13
**Branch**: 002-silver-ai-employee

---

## R-001: Gmail Watcher — API vs IMAP

**Decision**: `imaplib` (Python stdlib) + Gmail App Password. No OAuth2.

**Rationale**: App Password requires zero GCP setup — enable 2FA, generate a 16-char password, store in `.env`. 2-minute setup vs 20+ minutes for Google Cloud OAuth2 consent screen. `imaplib` is stdlib — no new dependencies. `SEARCH (UNSEEN)` is server-side filtering; `RFC822.HEADER` fetch avoids downloading full bodies. Track processed messages by IMAP **UID** in `scripts/processed_gmail.json`.

**Alternatives considered**:
- Gmail API (`google-api-python-client`) — requires GCP project + OAuth2 consent screen + token refresh. Unnecessary complexity for single-user local deployment.
- IMAPv4 IDLE (push) — persistent connection management; polling every 5 min is sufficient.

**Implementation**:
```python
# watchers/gmail_watcher.py — GmailWatcher(BaseWatcher)
imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
imap.select("INBOX")
_, uids = imap.search(None, "UNSEEN")  # server-side filter
# Fetch RFC822.HEADER, parse with email.message_from_bytes()
# Mark as read after processing; store UID in processed_gmail.json
```

**New Python deps**: None (imaplib, email are stdlib). `.env` additions: `GMAIL_EMAIL`, `GMAIL_APP_PASSWORD`.

---

## R-002: WhatsApp Watcher

**Decision**: `playwright` Python library polling WhatsApp Web. No whatsapp-web.js.

**Rationale**: Research confirmed `whatsapp-web.js` was last maintained in 2022 and breaks frequently on WhatsApp Web updates. The Python `playwright` library (same engine as the existing `browsing-with-playwright` MCP skill) is more stable — uses accessibility snapshots rather than brittle CSS selectors. WhatsApp Business API requires business verification + dedicated phone number — not viable for a personal assistant. The watcher polls every 60 seconds (sufficient for Silver), caches the browser session in `whatsapp_session/linkedin/` after first QR scan.

**Alternatives considered**:
- `whatsapp-web.js` (Node.js) — high maintenance burden, unmaintained.
- WhatsApp Business API — requires Meta business registration; not viable.
- Claude skill on 60-second cron — calling Claude every 60s is wasteful; Python watcher is lighter.

**Implementation**:
```python
# watchers/whatsapp_watcher.py — WhatsAppWatcher(BaseWatcher)
# sync_playwright() → persistent_context(whatsapp_session/) → navigate(web.whatsapp.com)
# accessibility snapshot → find unread chats → extract sender + text
# Track processed message hashes in scripts/processed_whatsapp.json
```

**New deps**: `playwright>=1.40.0` (add to requirements.txt); `playwright install chromium` (one-time).

---

## R-003: LinkedIn Automation

**Decision**: Use the **existing `browsing-with-playwright` Playwright MCP skill**. No new linkedin-mcp server.

**Rationale**: Research confirmed no official `linkedin-mcp` exists in the ecosystem. LinkedIn REST API v2 blocks personal accounts (requires LinkedIn Partner Program — weeks of approval). The existing Playwright MCP already handles browser automation; extending it with a LinkedIn workflow (login → compose → post) is the simplest path. Constitution Principle I satisfied: LinkedIn accessed via MCP (Playwright MCP), not via ad-hoc subprocess. Rate risk mitigated by: 1 post/week schedule, `DRY_RUN=true` default, `Pending_Approval/` gate.

**Playwright workflow**:
```
1. Navigate https://linkedin.com/feed → check login state
2. Click "Start a post" → type content → click "Post"
3. Snapshot → confirm "Your post was shared"
4. Log to Logs/YYYY-MM-DD.json
```

**Alternatives considered**: Custom Node.js linkedin-mcp server (redundant — would just wrap Playwright). `linkedin-api` Python package (unofficial, fragile, TOS grey area).

---

## R-004: email-mcp — Python smtplib MCP Server

**Decision**: Python MCP server (`mcp-servers/email-mcp/server.py`) with three tools: `send_email`, `draft_reply`, `search_inbox`.

**Rationale**: Gmail SMTP (port 465 SSL) + App Password — same credentials as the Gmail watcher, zero extra setup. `smtplib.SMTP_SSL("smtp.gmail.com", 465)` works out of the box. Python `mcp` SDK provides the stdio transport. Constitution Principle I: email sending accessed via MCP tool, not direct subprocess call.

**Tools**:
- `send_email(to, subject, body, reply_to_message_id?)` → `{status, message_id}`
- `draft_reply(message_id, draft_body)` → `{status, draft_id}` (Gmail Drafts via IMAP APPEND)
- `search_inbox(query, max_results?)` → `[{uid, from, subject, snippet}]`

**New deps**: `mcp>=1.0.0` (add to requirements.txt).

---

## R-005: HITL Approval — Folder-Movement Pattern

**Decision**: File-movement approval flow: `Plans/` → `Pending_Approval/` → `Approved/` or `Rejected/` → execution → `Done/`.

**Rationale**: The user-defined approval workflow uses explicit vault folders (`Pending_Approval/`, `Approved/`, `Rejected/`) rather than checkbox-in-place editing. This is cleaner for Obsidian — the user moves files between folders (drag-and-drop in Obsidian, or using the file explorer), which is more intuitive than editing markdown syntax. The `ApprovalWatcher` polls `Approved/` for new files and writes `ACTION_*.md` triggers to `Needs_Action/`.

**Approval request file schema** (written to `Pending_Approval/`):
```markdown
---
type: approval_request
action: send_email | linkedin_post
plan_file: PLAN_<timestamp>_<slug>.md
reason: <why this action is needed>
parameters: {to, subject, body} or {post_content}
timestamp: ISO-8601
status: pending
---
```

**Flow**: Claude writes approval file → human moves to `Approved/` → ApprovalWatcher detects → execute-plan skill fires MCP call → moves to `Done/`.

---

## R-006: Cron / Scheduling on WSL2

**Decision**: System `cron` inside WSL2 with a `scripts/install-cron.sh` generator.

**WSL2 note**: `cron` does not auto-start on WSL2 boot. User must run `sudo service cron start` once per WSL2 session (or add to `/etc/wsl.conf` `[boot]` section for auto-start).

**Schedule**:
```
*/5 * * * *  .venv/bin/python orchestrator.py --watcher gmail
0   * * * *  .venv/bin/python orchestrator.py --watcher whatsapp
0   8 * * 1  claude --print "Run the linkedin-post skill"
0   9 * * *  claude --print "Run the process-needs-action skill"
```

**New deps**: None (system cron).
