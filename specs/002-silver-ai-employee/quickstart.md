# Quickstart: Silver Tier Functional Assistant

**Prerequisites**: Bronze Tier fully operational (orchestrator runs, filesystem watcher works, process-needs-action skill tested)

---

## Step 1 — Install new dependencies

```bash
cd "Personal AI Employee"
.venv/bin/pip install playwright mcp
.venv/bin/playwright install chromium
```

---

## Step 2 — Add Silver Tier credentials to `.env`

```bash
# Edit your .env file and add:
GMAIL_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # 16-char App Password from myaccount.google.com
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=yourpassword
DRY_RUN=true                              # Keep true until end-to-end tested
```

**Generate Gmail App Password**:
1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Enable 2-Step Verification if not already on
3. Search "App passwords" → Create for "Mail" on "Linux"
4. Copy the 16-character password into `.env`

---

## Step 3 — Create new vault folders

```bash
mkdir -p AI_Employee_Vault/{Pending_Approval,Approved,Rejected}
```

---

## Step 4 — Create `Business_Goals.md`

Open `AI_Employee_Vault/Business_Goals.md` in Obsidian and fill in your services:

```markdown
# Business Goals

## Services Offered
- AI consulting and automation setup
- Custom workflow development
- ...

## Target Audience
- Small business owners
- Entrepreneurs looking to automate operations

## LinkedIn Post Topics (rotate weekly)
- AI automation case studies
- Productivity tips for business owners
- ...

## Revenue Target (Monthly)
$X,000 MRR
```

---

## Step 5 — Register email-mcp in Claude Code

Edit `~/.config/claude-code/mcp.json` and add:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["/mnt/c/Users/DELL/Documents/GitHub/Personal AI Employee/mcp-servers/email-mcp/server.py"],
      "env": {
        "GMAIL_EMAIL": "your.email@gmail.com",
        "GMAIL_APP_PASSWORD": "xxxx-xxxx-xxxx-xxxx"
      }
    }
  }
}
```

Restart Claude Code to pick up the new MCP server.

---

## Step 6 — Start the WhatsApp watcher (first run — QR code scan)

```bash
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py --watcher whatsapp
```

A Chromium window will open with a WhatsApp QR code. Scan it with your phone (WhatsApp → Linked Devices → Link a Device). The session is saved in `whatsapp_session/` — you won't need to scan again unless the session expires.

---

## Step 7 — Start the full orchestrator

```bash
# Terminal 1 — main orchestrator (filesystem + approval watchers always-on)
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py

# Terminal 2 — Gmail watcher (or configure cron for automatic runs)
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py --watcher gmail

# Terminal 3 — Claude Code
claude
```

---

## Step 8 — Install the cron schedule (optional)

```bash
bash scripts/install-cron.sh
# Follow the prompts; confirms VAULT_PATH and installs crontab entries
# Start cron daemon (required once per WSL2 session):
sudo service cron start
```

---

## Step 9 — Test Gmail watcher

Send a test email to your Gmail account. Within 5 minutes, check:

```bash
ls AI_Employee_Vault/Needs_Action/EMAIL_*.md
```

---

## Step 10 — Run Claude to process tasks and approve

In the Claude terminal:

```
Run the process-needs-action skill
```

Claude will:
1. Read `Company_Handbook.md`
2. Process `EMAIL_*.md` and `WA_*.md` tasks
3. Create `Plans/PLAN_*.md` for each
4. Write `Pending_Approval/APPROVAL_*.md` for email replies

In Obsidian: open `Pending_Approval/APPROVAL_*.md`, review the draft reply, then drag it to `Approved/` to send (or `Rejected/` to discard).

Within 5 seconds, the approval watcher triggers the execute-plan skill, which calls `email-mcp send_email`.

---

## Step 11 — Test LinkedIn post generation

In Claude terminal:

```
Run the linkedin-post skill
```

Claude reads `Business_Goals.md` and generates a post. Review `Pending_Approval/APPROVAL_*_linkedin.md` in Obsidian, then move it to `Approved/` when satisfied.

Set `DRY_RUN=false` in `.env` when ready to publish for real.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Gmail watcher finds no emails | Verify App Password in `.env`; check IMAP is enabled in Gmail settings |
| WhatsApp QR code not showing | Install Chromium: `.venv/bin/playwright install chromium` |
| WhatsApp session expires | Re-run `orchestrator.py --watcher whatsapp`; re-scan QR code |
| email-mcp not found by Claude | Restart Claude Code after editing `mcp.json`; verify absolute paths |
| Approval watcher not triggering | Confirm file was moved to `Approved/` (not `Pending_Approval/`); check `processed_approvals.json` for stale entries |
| LinkedIn post not published | Verify `DRY_RUN=false` in `.env`; check `Logs/` for error entries |
| Cron jobs not running | Run `sudo service cron start`; check `crontab -l` shows entries |
