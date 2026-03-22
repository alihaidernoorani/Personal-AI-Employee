# Quickstart: Gold Tier Personal AI Employee

**Date**: 2026-03-22 | **Branch**: `003-gold-ai-employee`

---

## Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.13+ | Watchers, orchestrator, Odoo MCP |
| Node.js | v24+ LTS | Email MCP, Social MCP |
| Claude Code | Latest | Reasoning engine |
| Obsidian | v1.10.6+ | Vault GUI |
| Odoo Community | 19+ | Accounting system (self-hosted) |
| Git | Any | Version control |

---

## 1. Clone and Install

```bash
git clone <repo-url>
cd Personal_AI_Employee

# Python environment
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# Node.js dependencies (Email MCP + Social MCP)
cd mcp_servers/email_mcp && npm install && cd ../..
cd mcp_servers/social_mcp && npm install && cd ../..

# Browser MCP (Anthropic-provided)
npx @anthropic/browser-mcp --version  # confirms installation
```

---

## 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — fill in ALL values before starting:

```
# Vault
VAULT_PATH=/path/to/AI_Employee_Vault
VAULT_TEMP_PATH=/tmp/ai_employee_temp

# Gmail
GMAIL_CREDENTIALS_PATH=/path/to/gmail_credentials.json

# WhatsApp
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session

# Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=your_odoo_database
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password

# Social Media
LINKEDIN_ACCESS_TOKEN=...
FACEBOOK_PAGE_ACCESS_TOKEN=...
FACEBOOK_PAGE_ID=...
INSTAGRAM_ACCESS_TOKEN=...
TWITTER_BEARER_TOKEN=...

# Bank
BANK_API_TOKEN=...
BANK_CSV_PATH=...   # if using CSV export instead of API

# Operations
DRY_RUN=true        # set to false only for live execution
LOG_LEVEL=INFO
```

---

## 3. Initialise the Vault

Create all required folders inside your Obsidian vault:

```
AI_Employee_Vault/
├── Dashboard.md          ← create manually or run init script
├── Company_Handbook.md   ← fill with your rules of engagement
├── Business_Goals.md     ← fill with your OKRs and targets
├── Bank_Transactions.md  ← starts empty; Finance watcher appends
├── Inbox/
├── Needs_Action/
├── In_Progress/
│   └── local_agent/
├── Plans/
├── Pending_Approval/
├── Approved/
├── Rejected/
├── Done/
├── Briefings/
├── Accounting/
└── Logs/
```

---

## 4. Register MCP Servers

MCP servers are registered in `.mcp.json` at the **project root** (not in `~/.config`). Update this file to add Gold tier servers alongside existing ones:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["mcp-servers/email-mcp/server.py"]
    },
    "social-mcp": {
      "command": "python",
      "args": ["mcp-servers/social-mcp/server.py"]
    },
    "odoo-mcp": {
      "command": "python",
      "args": ["mcp-servers/odoo-mcp/server.py"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": { "HEADLESS": "true" }
    }
  }
}
```

---

## 5. Configure Ralph Wiggum Hook

> **Already implemented.** `scripts/check_loop_complete.py` and `scripts/ralph_loop.py` exist. Verify the stop hook is registered in `.claude/settings.json`. If not present, add:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/check_loop_complete.py"
          }
        ]
      }
    ]
  }
}
```

---

## 6. Start the System

```bash
# Dry-run mode (default) — safe for testing
python orchestrator.py

# Verify watchers are running
python orchestrator.py --status

# Run a manual test (process any files in Needs_Action/)
# In a second terminal:
claude "Run the process-needs-action skill"
```

---

## 7. Test the HITL Approval Gate

```bash
# Drop a test task into Needs_Action
echo '---
type: email
source: gmail
source_id: test001
created: 2026-03-22T09:00:00Z
priority: high
subject: Test approval gate
raw_content: |
  Please send a payment of $500 to new vendor.
---' > AI_Employee_Vault/Needs_Action/EMAIL_test001.md

# Run process-needs-action — should create APPROVAL_*.md in Pending_Approval/
claude "Run the process-needs-action skill"

# In Obsidian: move APPROVAL_*.md to Approved/
# Watch execute-plan run and log the action
```

---

## 8. Production: Windows Task Scheduler (Always-On)

For always-on operation, configure Windows Task Scheduler to start the orchestrator on login:

1. Open Task Scheduler → Create Basic Task
2. Trigger: At log on
3. Action: Start a program → `python` → Arguments: `C:\path\to\orchestrator.py`
4. Check "Run whether user is logged on or not"
5. Check "Run with highest privileges"

The orchestrator's internal `schedule` library handles all sub-task timing (CEO briefing, catch-up sweep, log cleanup) once the main process is running.

---

## 9. Verify End-to-End

Checklist before declaring Gold tier complete:

- [ ] Email arrives → `Needs_Action/EMAIL_*.md` created within 60 s
- [ ] Unknown-contact email → `APPROVAL_*.md` created; no reply sent until approved
- [ ] WhatsApp keyword message → `NEEDS_ACTION/WHATSAPP_*.md` created; single browser session
- [ ] Bank transaction → appended to `Bank_Transactions.md` + Odoo record created
- [ ] Sunday 23:00 → `Briefings/YYYY-MM-DD_Monday_Briefing.md` generated with all sections
- [ ] Social post approved → published + summary in next briefing
- [ ] Multi-step task → Ralph loop does not exit prematurely; prior output visible on re-inject
- [ ] All actions → corresponding entry in `Logs/YYYY-MM-DD.json`
- [ ] `Dashboard.md` updates within 30 s of state transitions
- [ ] `DRY_RUN=true` prevents any real sends in test mode
