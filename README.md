# Personal AI Employee

*Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

An autonomous Digital FTE (Full-Time Equivalent) powered by **Claude Code** and **Obsidian**.

---

## Architecture

```
Inbox (file drop) ──► Filesystem Watcher ──► Needs_Action/
                                                    │
                                             Claude Code
                                          (process-needs-action skill)
                                                    │
                              ┌─────────────────────┼──────────────────┐
                         Safe actions          Sensitive actions    Errors
                              │                     │                  │
                           Done/           Pending_Approval/    Needs_Action/
                                                    │               ERROR_*
                                           Human approves
                                                    │
                                              Approved/ ──► MCP Action
```

**Perception:** Python Watcher scripts monitor inputs (files, Gmail, WhatsApp) and write structured `.md` files to `Needs_Action/`.

**Reasoning:** Claude Code reads the vault, applies `Company_Handbook.md` rules, and decides what to do.

**Action:** Safe actions execute directly; sensitive ones wait in `Pending_Approval/` for human sign-off before any MCP server acts.

---

## Current Tier: Silver

| Requirement | Status |
|-------------|--------|
| `AI_Employee_Vault/` with Dashboard + Handbook | Done |
| `/Inbox`, `/Needs_Action`, `/Done` folders | Done |
| `Pending_Approval/`, `Approved/`, `Rejected/` folders | Done |
| Filesystem Watcher script | Done |
| Gmail Watcher (IMAP, 5-min poll) | Done |
| WhatsApp Watcher (Playwright, 60s daemon) | Done |
| Approval Watcher (5s poll) | Done |
| Agent Skill: `process-needs-action` (extended for email+whatsapp) | Done |
| Agent Skill: `execute-plan` (email-mcp + LinkedIn) | Done |
| Agent Skill: `linkedin-post` (lead-gen content) | Done |
| MCP Server: `email-mcp` (send/draft/search) | Done |
| Cron scheduling: `scripts/install-cron.sh` | Done |
| `Business_Goals.md` with OKRs and LinkedIn topics | Done |

---

## Quickstart (8 steps, under 5 minutes)

**Prerequisites:** Windows 11 + WSL2 (Ubuntu), Python 3.12+, Git, Obsidian

### Step 1 — Clone and enter the repo

```bash
git clone <repo-url> "Personal AI Employee"
cd "Personal AI Employee"
```

### Step 2 — Create the Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Step 3 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
VAULT_PATH=/mnt/c/Users/<your-name>/Documents/GitHub/Personal AI Employee/AI_Employee_Vault
DRY_RUN=true
```

### Step 4 — Open the vault in Obsidian

Open Obsidian → **Open folder as vault** → select `AI_Employee_Vault/`

You should see `Dashboard.md` and `Company_Handbook.md`.

### Step 5 — Start the watcher

```bash
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py
```

Expected output:
```
[Orchestrator] INFO: AI Employee Orchestrator starting (Bronze tier)
[FilesystemWatcher] INFO: Watching inbox: .../AI_Employee_Vault/Inbox
```

### Step 6 — Drop a test file

In a second terminal:

```bash
echo "Test task content" > "$PWD/AI_Employee_Vault/Inbox/test.txt"
```

Within 3–5 seconds a `FILE_*.md` task file appears in `Needs_Action/`.

### Step 7 — Run Claude to process tasks

In a third terminal:

```bash
claude
```

Then tell Claude:
> "Run the process-needs-action skill"

Claude will:
1. Read `Company_Handbook.md`
2. Process all `.md` files in `Needs_Action/`
3. Create `Plans/PLAN_*.md` for each task
4. Move processed tasks to `Done/`
5. Update `Dashboard.md`

### Step 8 — Verify

Open `Dashboard.md` in Obsidian. You should see:
- Updated timestamp
- Zero items in Needs_Action
- Items completed today
- Recent completions summary

Check `Logs/YYYY-MM-DD.json` — every action is recorded.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| Watcher starts but no files detected | WSL2 inotify issue — confirm `PollingObserver` is used in `filesystem_watcher.py` |
| `externally-managed-environment` pip error | Use `python3 -m venv .venv` first, then `.venv/bin/pip install` |
| `VAULT_PATH not found` | Set `VAULT_PATH` in `.env` to the absolute path of `AI_Employee_Vault/` |
| Duplicate task files on watcher restart | Check `scripts/processed_inbox.json` — should list already-processed filenames |

---

## Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md          ← Real-time status (updated by Claude after each run)
├── Company_Handbook.md   ← Rules of engagement (edit to change AI behaviour)
├── Inbox/                ← Drop files here; watcher picks them up automatically
├── Needs_Action/         ← Pending items waiting for Claude to process
├── Done/                 ← Completed items (never deleted)
└── Logs/                 ← Audit log (YYYY-MM-DD.json, one JSON line per action)
```

---

## Silver Tier

### Prerequisites

- Gmail account with IMAP enabled and an App Password (16-char, from Google Account > Security > 2FA > App Passwords)
- WhatsApp account (Web access via QR code on first run)
- Playwright Chromium browser: `.venv/bin/playwright install chromium`

### Quickstart (Silver Tier — 6 steps)

**Step 1 — Install dependencies:**
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

**Step 2 — Configure `.env`:**
```bash
cp .env.example .env
# Set:
# VAULT_PATH=/absolute/path/to/AI_Employee_Vault
# GMAIL_EMAIL=your@gmail.com
# GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
# DRY_RUN=true
```

**Step 3 — Install scheduling:**

*Windows (PowerShell — recommended):*
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts\install-task-scheduler.ps1
```

*WSL2/Linux (alternative):*
```bash
bash scripts/install-cron.sh
sudo service cron start   # required every WSL2 session
```

**Step 4 — Start the orchestrator (runs filesystem + approval + WhatsApp watchers):**
```bash
VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py
```

> **Recommended for production:** Use `watchdog.py` instead to auto-restart on crash:
> ```bash
> VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python watchdog.py
> ```

**Step 5 — Invoke skills in Claude:**
```bash
# Process incoming emails and WhatsApp messages:
claude --print "Run the process-needs-action skill"

# Generate a LinkedIn post:
claude --print "Run the linkedin-post skill"

# Execute approved actions:
claude --print "Run the execute-plan skill"
```

**Step 6 — Approve actions in Obsidian:**
- Open `AI_Employee_Vault/Pending_Approval/` in Obsidian
- Review the approval file content
- Drag/move it to `Approved/` to trigger execution, or `Rejected/` to discard

See `specs/002-silver-ai-employee/quickstart.md` for detailed walkthrough.

### Silver Tier Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md          ← Real-time status (updated by Claude after each run)
├── Company_Handbook.md   ← Rules of engagement
├── Business_Goals.md     ← OKRs, services, LinkedIn post topics
├── Inbox/                ← File drop zone
├── Needs_Action/         ← All task files (EMAIL_, WA_, FILE_, ACTION_, ERROR_)
├── Plans/                ← Claude-generated PLAN_*.md files
├── Pending_Approval/     ← APPROVAL_*.md awaiting human decision
├── Approved/             ← Human-approved → triggers execution
├── Rejected/             ← Declined actions (archived)
├── Done/                 ← Completed items (never deleted)
└── Logs/                 ← Audit trail (YYYY-MM-DD.json, 90-day retention)
```

---

## Security Disclosure

### Credential Storage

| Secret | Where stored | Git-tracked? |
|--------|-------------|--------------|
| `GMAIL_APP_PASSWORD` | `.env` (project root) | **No** — `.env` is in `.gitignore` |
| MCP env vars (Gmail, vault path) | `.mcp.json` (project root) | **No** — `.mcp.json` is in `.gitignore` |
| WhatsApp session cookies | `whatsapp_session/` | **No** — in `.gitignore` |
| LinkedIn browser session | `playwright-profile/` | **No** — in `.gitignore` |

**Never** commit `.env` or `.mcp.json`. Both are listed in `.gitignore`.

### DRY_RUN Safety Default

All action scripts check `DRY_RUN` (default: `true`) before executing any
external action (email send, LinkedIn post). Set `DRY_RUN=false` in `.env`
only when you are ready for live execution.

### Human-in-the-Loop (HITL) Safeguards

Sensitive actions (email sends, LinkedIn posts) are **never executed automatically**.
The workflow requires explicit human approval:

1. Claude writes `Pending_Approval/APPROVAL_*.md` — no action taken yet
2. Human reviews the file in Obsidian
3. Human moves it to `Approved/` (or `Rejected/` to discard)
4. Only after file is in `Approved/` does `execute-plan` call any MCP tool

Rejected files are archived in `Rejected/` and never re-executed.

### Audit Logging

Every action (send, draft, approval, rejection, watcher start, error) is appended
to `AI_Employee_Vault/Logs/YYYY-MM-DD.json` in NDJSON format with:
- ISO-8601 timestamp
- actor (`claude_code`, `email-mcp`, `watchdog`, `scheduler`)
- `approval_status` (`auto`, `approved`, `dry_run`, `rejected`)
- `result` (`success`, `failure`, `dry_run`, `deferred`)

Logs are retained for 90 days. No action is silently discarded.

### Permission Boundaries

| Action | Auto-approved | Always requires human approval |
|--------|--------------|-------------------------------|
| Email replies | Never (always approval) | All email sends |
| LinkedIn posts | Never | All posts |
| File create/read/move in vault | Yes | Delete or move outside vault |
| Payments | N/A (Silver tier) | All (Gold tier) |

### Credential Rotation

Rotate the Gmail App Password monthly or after any suspected breach.
Generate a new App Password at **myaccount.google.com → Security → App passwords**,
update `.env` and `.mcp.json`, and restart the orchestrator.

---

## Submission

- Tier: **Silver**
