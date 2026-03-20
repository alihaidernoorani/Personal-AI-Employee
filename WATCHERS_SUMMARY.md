# Watchers Implementation Summary

## Overview

Enhanced the AI Employee with three powerful watchers that monitor different channels for task creation:

1. **Gmail API Watcher** — OAuth 2.0, unread IMPORTANT emails, check_interval=120s
2. **WhatsApp Watcher** — Playwright + QR scan, keyword detection, check_interval=30s
3. **Email Watcher (IMAP)** — Traditional IMAP polling for basic Gmail (existing)

All watchers extend `BaseWatcher` and create `.md` files in `AI_Employee_Vault/Needs_Action/`.

---

## 1. Gmail API Watcher (`watchers/gmail_api_watcher.py`)

### Features
- ✓ Uses Google Gmail API (OAuth 2.0)
- ✓ Monitors **UNSEEN IMPORTANT** emails only
- ✓ Persistent token storage (`.gmail_token.json`)
- ✓ Automatic token refresh
- ✓ Check interval: **120 seconds** (2 minutes)
- ✓ Creates `GMAIL_*.md` files with metadata

### Metadata
```yaml
type: email
source: gmail_api
msg_id: "18c0e7f6e1234567"
sender: "billing@acme.com"
subject: "Invoice #12345 Due"
snippet: "Your invoice is due..."
priority: high
received: "2026-03-20T12:00:00Z"
status: pending
```

### Quick Start
```bash
# 1. Download OAuth credentials from Google Cloud Console
cp ~/Downloads/client_secret_*.json ./credentials.json

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the watcher (opens browser for authorization)
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher gmail_api

# 4. Authorize in browser, mark emails as IMPORTANT
```

### Setup Guide
See: `GMAIL_API_SETUP.md`

---

## 2. WhatsApp Watcher (`watchers/whatsapp_watcher.py`)

### Features
- ✓ Uses Playwright for WhatsApp Web automation
- ✓ Persistent browser session (`whatsapp_session/`)
- ✓ QR code scanning (first run only)
- ✓ **Keyword detection:** urgent, asap, invoice, payment
- ✓ **Priority escalation:** urgent → HIGH → normal
- ✓ Check interval: **30 seconds**
- ✓ Creates `WA_*.md` files with keyword matches

### Keyword Mapping
| Keyword | Priority |
|---------|----------|
| urgent | URGENT |
| asap | HIGH |
| invoice | HIGH |
| payment | HIGH |

### Metadata
```yaml
type: whatsapp
source: whatsapp_web
sender: "John Smith"
message_text: "Invoice due ASAP - urgent!"
priority: urgent
keywords_matched: ['urgent', 'asap', 'invoice']
received: "2026-03-20T13:00:00Z"
status: pending
```

### Quick Start
```bash
# 1. Install Playwright (one-time)
playwright install chromium

# 2. Run the watcher
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher whatsapp

# 3. Scan QR code in browser (first run only)
# 4. Send test message: "Urgent invoice due tomorrow"
# 5. Within 30 seconds, WA_*.md appears with priority: urgent
```

### Setup Guide
See: `WHATSAPP_WATCHER_SETUP.md`

---

## 3. Email Watcher (IMAP) — `watchers/gmail_watcher.py`

### Features
- ✓ Traditional IMAP polling (no OAuth required)
- ✓ Reads all unseen emails
- ✓ Tracks by UID (no duplicates)
- ✓ Check interval: **300 seconds** (5 minutes)
- ✓ Creates `EMAIL_*.md` files

### Quick Start
```bash
# 1. Generate Gmail App Password
#    Gmail Account → Security → App passwords → Select Mail + Windows Computer

# 2. Set environment variables
export GMAIL_EMAIL="your.email@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"  # 16-char password

# 3. Run the watcher
python orchestrator.py --watcher gmail
```

---

## File Structure

```
watchers/
├── base_watcher.py              # Abstract base class
├── gmail_watcher.py             # IMAP-based (existing)
├── gmail_api_watcher.py         # OAuth 2.0 Google API (NEW)
├── whatsapp_watcher.py          # Playwright + QR code (ENHANCED)
├── filesystem_watcher.py        # File drops
└── approval_watcher.py          # Approval workflow

scripts/
├── processed_gmail.json         # IMAP UID tracking
├── processed_gmail_api.json     # Gmail API message ID tracking (NEW)
└── processed_whatsapp.json      # WhatsApp message hash tracking

whatsapp_session/               # Persistent browser session (gitignored)
.gmail_token.json               # OAuth token for Gmail API (gitignored)

AI_Employee_Vault/
└── Needs_Action/
    ├── GMAIL_*.md              # Gmail API emails
    ├── WA_*.md                 # WhatsApp messages
    ├── EMAIL_*.md              # IMAP emails
    └── ERROR_*.md              # Watcher errors
```

---

## Configuration & Running

### Individual Watchers

```bash
# Gmail API (OAuth)
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher gmail_api

# WhatsApp (Playwright)
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher whatsapp

# IMAP Email
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher gmail

# All watchers
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher all

# Default (filesystem + approval + whatsapp)
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py
```

### Persistent Background Execution

```bash
# Keep watchers running with auto-restart
VAULT_PATH="./AI_Employee_Vault" python process_supervisor.py --watcher gmail_api

# Or all watchers
VAULT_PATH="./AI_Employee_Vault" python process_supervisor.py --watcher all
```

---

## Check Intervals Summary

| Watcher | Interval | Use Case |
|---------|----------|----------|
| **Gmail API** | 120s (2 min) | Important emails only, less API quota usage |
| **WhatsApp** | 30s | Real-time keyword detection, urgent messages |
| **IMAP Email** | 300s (5 min) | Basic email polling, lower resource usage |
| **Filesystem** | Real-time | File system changes (inotify / polling) |
| **Approval** | 5s | Human approval workflow |

---

## Priority Escalation

### Gmail API
- All marked IMPORTANT → `priority: high`

### WhatsApp (keyword-based)
- Contains "urgent" → `priority: urgent`
- Contains "asap" / "invoice" / "payment" → `priority: high`
- No keywords → `priority: normal`

### IMAP
- All → `priority: normal`

---

## Error Handling

All watchers write ERROR_*.md files on failure:

```markdown
---
type: error
source: whatsapp_watcher
priority: high
status: pending
---

## Error

Connection timeout to WhatsApp Web
```

Check `AI_Employee_Vault/Logs/YYYY-MM-DD.json` for structured audit logs.

---

## Dependencies Added

```
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.100.0
```

Note: `playwright>=1.40.0` was already in requirements.txt

---

## Security Checklist

- ✓ OAuth tokens stored in gitignored `.gmail_token.json`
- ✓ Credentials file (`credentials.json`) in `.gitignore`
- ✓ Browser session data in gitignored `whatsapp_session/`
- ✓ No credentials logged to audit files
- ✓ Gmail API uses read-only scope (`gmail.readonly`)
- ✓ WhatsApp uses persistent context (no login credentials stored)
- ✓ All actions logged with actor, target, result

---

## Testing Checklist

### Gmail API
- [ ] Download credentials.json from Google Cloud Console
- [ ] Run `python orchestrator.py --watcher gmail_api`
- [ ] Authorize in browser
- [ ] Send test email, mark as IMPORTANT
- [ ] Verify `GMAIL_*.md` appears in Needs_Action within 2 minutes

### WhatsApp
- [ ] Run `playwright install chromium` (one-time)
- [ ] Run `python orchestrator.py --watcher whatsapp`
- [ ] Scan QR code in browser
- [ ] Send test message: "Urgent payment due"
- [ ] Verify `WA_*.md` appears with `priority: urgent` within 30 seconds

### IMAP
- [ ] Set GMAIL_EMAIL and GMAIL_APP_PASSWORD
- [ ] Run `python orchestrator.py --watcher gmail`
- [ ] Send test email to inbox
- [ ] Verify `EMAIL_*.md` appears within 5 minutes

---

## Next Steps

1. **Commit changes:**
   ```bash
   git add -A
   git commit -m "feat(silver): add Gmail API and enhance WhatsApp watchers"
   ```

2. **Deploy to production:**
   ```bash
   python process_supervisor.py --watcher all
   ```

3. **Monitor logs:**
   ```bash
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
   ```

4. **Customize keywords:**
   Edit `PRIORITY_KEYWORDS` in `watchers/whatsapp_watcher.py`

---

## Troubleshooting

See individual setup guides:
- **Gmail API:** `GMAIL_API_SETUP.md`
- **WhatsApp:** `WHATSAPP_WATCHER_SETUP.md`
- **IMAP Email:** Built-in docstring in `watchers/gmail_watcher.py`

---

## Architecture Notes

### BaseWatcher Interface

All watchers implement:

```python
class Watcher(BaseWatcher):
    def check_for_updates(self) -> list[Path]:
        """Return new task file paths"""

    def create_action_file(self, item: dict) -> Path:
        """Write .md to Needs_Action/ and return path"""

    def run(self):
        """Main loop with configurable check_interval"""
```

### Idempotency

- **Gmail API:** Message ID deduplication (`scripts/processed_gmail_api.json`)
- **WhatsApp:** Message hash deduplication (SHA256)
- **IMAP:** UID deduplication

No duplicate action files created, even if watcher is restarted.

---

## Silver Tier Requirements Met

- ✓ Multi-channel monitoring (Gmail API, WhatsApp, IMAP)
- ✓ Keyword detection and priority escalation
- ✓ Persistent sessions (WhatsApp, Gmail tokens)
- ✓ Structured task files (YAML frontmatter)
- ✓ Audit logging (Logs/YYYY-MM-DD.json)
- ✓ Error handling and recovery
- ✓ Idempotent operations (no duplicates)
