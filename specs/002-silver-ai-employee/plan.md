# Implementation Plan: Silver Tier Functional Assistant

**Branch**: `002-silver-ai-employee` | **Date**: 2026-03-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-silver-ai-employee/spec.md`

---

## Summary

Extend the Bronze Tier with a three-layer architecture: **Perception** (Gmail + WhatsApp watchers), **Reasoning** (Claude Agent Skills loop), and **Action** (email-mcp + Playwright LinkedIn). State lives exclusively in the Obsidian vault. HITL approval uses explicit folder movement (`Pending_Approval/` → `Approved/`). One working MCP server required: `email-mcp`.

---

## Technical Context

**Language/Version**: Python 3.12+ (watchers, email-mcp), Node.js v18+ not required (Playwright MCP already exists)
**Primary Dependencies**: `imaplib`/`smtplib` (stdlib), `playwright>=1.40.0` (Python), `mcp>=1.0.0` (PyPI), `watchdog>=4.0.0` (existing)
**Storage**: Obsidian vault markdown files only — no external databases
**Testing**: Manual end-to-end per acceptance scenario; `DRY_RUN=true` for all external actions during dev
**Target Platform**: WSL2 Ubuntu on Windows 11 Pro, `/mnt/c` NTFS mount — `PollingObserver` required
**Performance Goals**: Gmail task ≤5 min (SC-001), WhatsApp task ≤60s (SC-002), 10 tasks planned <3 min (SC-003)
**Constraints**: No inotify; all secrets in `.env`; `DRY_RUN=true` default; one Claude instance

---

## Constitution Check

| Principle | Requirement | Status |
|-----------|-------------|--------|
| I. Skills-First & MCP | Watchers perception-only; email sending and LinkedIn via MCP | ✅ PASS — Gmail/WhatsApp watchers only write `.md` files; `email-mcp` handles all outbound email; Playwright MCP handles LinkedIn |
| I. Idempotency | Each watcher tracks processed IDs in `scripts/processed_*.json` | ✅ PASS — `processed_gmail.json`, `processed_whatsapp.json`, `processed_approvals.json` |
| II. Folder State Machine | One-way: Needs_Action → Plans → Pending_Approval → Approved → Done | ✅ PASS — Approval files move forward only; Rejected folder for declined actions |
| III. HITL Safety | Email sends, LinkedIn posts require human approval before execution | ✅ PASS — ApprovalWatcher only fires after file lands in `Approved/`; no auto-approval |
| IV. Proactive BI | Weekly CEO briefing — Gold tier; not required for Silver | ✅ PASS — Out of scope, documented |
| V. Security & Ops | Secrets in `.env`; PollingObserver; forward-slash paths; `feat(silver):` commits | ✅ PASS — All credentials in `.env`; PollingObserver on all vault watchers |

**Constitution Check: ALL PASS.**

---

## System Architecture

### Three-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  PERCEPTION LAYER — Watchers (Python background processes)       │
│                                                                  │
│  GmailWatcher          WhatsAppWatcher      FilesystemWatcher    │
│  (imaplib, 5-min poll) (playwright, 60s)    (PollingObserver)    │
│         │                     │                    │             │
│         └─────────────────────┴────────────────────┘             │
│                               │                                  │
│                        Needs_Action/                             │
│              EMAIL_*.md  WA_*.md  FILE_*.md                      │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  REASONING LAYER — Claude Agent Skills (Reasoning Loop)          │
│                                                                  │
│  process-needs-action     linkedin-post     execute-plan         │
│  (reads Needs_Action,     (reads            (reads Approved/,    │
│   creates Plans/,          Business_Goals,   calls MCP tools)    │
│   creates Pending_         creates           moves to Done/)     │
│   Approval/ for            Pending_                              │
│   sensitive actions)       Approval/)                            │
│                                                                  │
│  Plans/PLAN_*.md           Pending_Approval/APPROVAL_*.md        │
└──────────────────────────────────────────────────────────────────┘
                               │
                    Human moves APPROVAL_*.md
                    to Approved/ or Rejected/
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  ACTION LAYER — MCP Servers (External Execution)                 │
│                                                                  │
│  email-mcp (Python/stdio)        browsing-with-playwright (MCP)  │
│  send_email / draft_reply /      linkedin_post / whatsapp_read   │
│  search_inbox                                                    │
│                                                                  │
│  → Gmail SMTP (send)             → LinkedIn Web (post)           │
│  → Gmail IMAP (draft/search)     → WhatsApp Web (read)           │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                         Done/ + Logs/
```

---

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-ai-employee/
├── plan.md              ← this file
├── research.md          ← R-001 through R-006
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── task-file-schema.md       (email + whatsapp types added)
│   ├── approval-request-schema.md (new)
│   ├── plan-file-schema.md        (unchanged from Bronze)
│   └── log-entry-schema.md        (mcp_call action type added)
└── tasks.md             ← /sp.tasks output (not this command)
```

### Source Code (repository root)

```text
watchers/
├── base_watcher.py              (existing)
├── filesystem_watcher.py        (existing)
├── gmail_watcher.py             NEW
├── whatsapp_watcher.py          NEW
└── approval_watcher.py          NEW

mcp-servers/
└── email-mcp/
    ├── server.py                NEW — Python MCP server (stdio)
    └── smtp_imap.py             NEW — smtplib + imaplib helpers

.claude/skills/
├── process-needs-action/        (existing, extended for email+whatsapp types)
│   └── SKILL.md
├── linkedin-post/               NEW
│   └── SKILL.md
└── execute-plan/                NEW
    └── SKILL.md

scripts/
├── processed_inbox.json         (existing)
├── processed_gmail.json         NEW
├── processed_whatsapp.json      NEW
├── processed_approvals.json     NEW
└── install-cron.sh              NEW

AI_Employee_Vault/
├── Dashboard.md                 (existing, extended)
├── Company_Handbook.md          (existing)
├── Business_Goals.md            NEW — services, OKRs, LinkedIn topics
├── Inbox/                       (existing)
├── Needs_Action/                (existing)
├── Plans/                       (existing)
├── Pending_Approval/            NEW
├── Approved/                    NEW
├── Rejected/                    NEW
├── Done/                        (existing)
└── Logs/                        (existing)

orchestrator.py                  (existing, extended — adds ApprovalWatcher, --watcher flag)
requirements.txt                 (updated: playwright>=1.40.0, mcp>=1.0.0)
```

---

## Module Descriptions

### Module 1 — GmailWatcher (`watchers/gmail_watcher.py`)

**Layer**: Perception
**Responsibility**: Poll Gmail INBOX for UNSEEN messages every 5 minutes. Create `EMAIL_<timestamp>_<subject-slug>.md` in `Needs_Action/`. Track processed IMAP UIDs in `scripts/processed_gmail.json`.

**Inputs**: `GMAIL_EMAIL`, `GMAIL_APP_PASSWORD` from `.env`
**Outputs**: `Needs_Action/EMAIL_*.md` with frontmatter `type: email, source: gmail, sender, subject, body_snippet, uid, received, priority: normal, status: pending`
**Key behaviour**: `SEARCH (UNSEEN)` → fetch `RFC822.HEADER` only → parse sender/subject → write task file → mark as read → persist UID to registry
**Error handling**: `check_for_updates()` MUST wrap its body in `try/except`. On any non-fatal exception: write `Needs_Action/ERROR_<ts>_gmail_watcher.md` and continue the polling loop. Fatal errors (e.g. unrecoverable auth failure) log before exit. (FR-005)

---

### Module 2 — WhatsAppWatcher (`watchers/whatsapp_watcher.py`)

**Layer**: Perception
**Responsibility**: Poll WhatsApp Web every 60 seconds for new messages. Create `WA_<timestamp>_<sender-slug>.md` in `Needs_Action/`. Track processed message hashes in `scripts/processed_whatsapp.json`.

**Inputs**: Browser session in `whatsapp_session/` (QR code scan on first run)
**Outputs**: `Needs_Action/WA_*.md` with frontmatter `type: whatsapp, source: whatsapp, sender, message_text, received, priority: normal, status: pending`
**Key behaviour**: `sync_playwright()` → persistent context → navigate `web.whatsapp.com` → accessibility snapshot → find unread chats → extract sender + text → hash for idempotency → write task file
**Lifecycle**: Runs as a **persistent long-running daemon** with an internal 60s sleep loop — NOT a cron job. Started once by `orchestrator.py` (default run or `--watcher whatsapp`). This is required to satisfy SC-002 (≤60s detection).
**Error handling**: `check_for_updates()` MUST wrap its body in `try/except`. On any non-fatal exception: write `Needs_Action/ERROR_<ts>_whatsapp_watcher.md` and continue the loop. (FR-005)

---

### Module 3 — ApprovalWatcher (`watchers/approval_watcher.py`)

**Layer**: Perception (polls vault state)
**Responsibility**: Poll `Approved/` every 5 seconds for new approval files. When a file is detected, write `ACTION_<timestamp>_<slug>.md` to `Needs_Action/` to trigger `execute-plan` skill. Also poll `Rejected/` to log and archive rejected approvals.

**Inputs**: `Approved/APPROVAL_*.md` files (moved there by human)
**Outputs**: `Needs_Action/ACTION_*.md` with frontmatter `type: action_trigger, approval_file, action_type, action_params`
**Idempotency**: `scripts/processed_approvals.json` — key: `filename`, value: timestamp processed

---

### Module 4 — `process-needs-action` Skill (extended)

**Layer**: Reasoning
**Responsibility**: Existing Bronze skill extended for `type: email` and `type: whatsapp`. Reads Company_Handbook.md first. Creates `Plans/PLAN_*.md` and writes `Pending_Approval/APPROVAL_*.md` for any outbound action.

**New task type handling**:
- `type: email` → draft reply per Handbook comms rules → create plan → write `Pending_Approval/APPROVAL_*.md` with `action: send_email, parameters: {to, subject, body, reply_to_uid}`
- `type: whatsapp` → summarise message → create plan → no outbound action for Silver (receive-only)
- Existing types (`file_drop`, `error`) — unchanged from Bronze

---

### Module 5 — `linkedin-post` Skill

**Layer**: Reasoning
**Responsibility**: Generate a 100–300 word LinkedIn post. Read `Business_Goals.md` for services + target audience. Write `Plans/PLAN_*_linkedin.md` and `Pending_Approval/APPROVAL_*_linkedin.md`.

**Inputs**: `AI_Employee_Vault/Business_Goals.md`, `AI_Employee_Vault/Company_Handbook.md`
**Outputs**: `Plans/PLAN_*_linkedin.md` + `Pending_Approval/APPROVAL_*_linkedin.md` with `action: linkedin_post, parameters: {post_content}`
**Invocation**: Manually via `claude "Run the linkedin-post skill"` or Monday 8 AM cron

---

### Module 6 — `execute-plan` Skill

**Layer**: Reasoning → triggers Action
**Responsibility**: Process `type: action_trigger` files. Read the referenced approval file, identify the action type, call the appropriate MCP tool. Move processed files to `Done/` on success. On failure: update plan status, create `ERROR_*.md`, restore approval file to `Pending_Approval/`.

**MCP calls**:
- `action: send_email` → `email-mcp` tool `send_email(...)`
- `action: linkedin_post` → `browsing-with-playwright` tool (LinkedIn workflow)

**Retry**: Up to 3 attempts with 5s backoff before writing `ERROR_*.md`.
**Failure branch** (FR-018): On final failure — (1) update `Plans/PLAN_*.md` frontmatter `status: awaiting_approval`; (2) write `Needs_Action/ERROR_<ts>_<slug>.md`; (3) move `APPROVAL_*.md` back to `Pending_Approval/`. This ensures the plan reverts to a reviewable state.

---

### Module 7 — `email-mcp` Server (`mcp-servers/email-mcp/server.py`)

**Layer**: Action
**Responsibility**: Python MCP server (stdio transport) with three tools.

**Tools**:
| Tool | Parameters | Returns |
|------|-----------|---------|
| `send_email` | `to, subject, body, reply_to_message_id?` | `{status, message_id}` |
| `draft_reply` | `message_id, draft_body` | `{status, draft_id}` |
| `search_inbox` | `query, max_results?` | `[{uid, from, subject, snippet}]` |

**Registration** in `~/.config/claude-code/mcp.json`:
```json
{
  "email-mcp": {
    "command": "python",
    "args": ["/path/to/mcp-servers/email-mcp/server.py"],
    "env": {
      "GMAIL_EMAIL": "${GMAIL_EMAIL}",
      "GMAIL_APP_PASSWORD": "${GMAIL_APP_PASSWORD}"
    }
  }
}
```

---

### Module 8 — Orchestrator (extended, `orchestrator.py`)

**Responsibility**: Extend with `--watcher <name>` and `--cron` flags. Default run starts `FilesystemWatcher` + `ApprovalWatcher` + `WhatsAppWatcher` (persistent daemons). Gmail watcher started by cron via `--watcher gmail --cron`.

**New flags**:
- `--watcher filesystem | gmail | whatsapp | approval | all` — select which watcher(s) to start
- `--cron` — boolean flag indicating this run was triggered by cron; causes a `actor: scheduler` log entry to be written to `Logs/YYYY-MM-DD.json`. Manual `--watcher` runs do NOT pass `--cron` and are NOT logged as scheduler events. (FR-020, resolves I2)

---

### Module 9 — Scheduler (`scripts/install-cron.sh`)

**Responsibility**: Generate crontab entries from `VAULT_PATH` in `.env`. User runs once to install.

**Schedule generated** (3 entries — WhatsApp is a persistent daemon, not cron-managed):
```
*/5 * * * *  VAULT_PATH=... python orchestrator.py --watcher gmail --cron
0   8 * * 1  VAULT_PATH=... claude --print "Run the linkedin-post skill"
0   9 * * *  VAULT_PATH=... claude --print "Run the process-needs-action skill"
```

**Note**: WhatsApp watcher runs as a persistent long-running daemon started by `orchestrator.py` default run. It is NOT in the crontab. Adding it to cron would violate SC-002 (≤60s detection) since a one-shot cron job cannot maintain a 60s polling loop.

---

## Data Flow

### Flow A — Incoming Email → Reply Sent

```
1. GmailWatcher (every 5 min)
   Gmail IMAP SEARCH UNSEEN
   → Needs_Action/EMAIL_<ts>_<slug>.md
     (type: email, sender, subject, body_snippet, uid)

2. process-needs-action skill (9 AM cron or manual)
   Reads EMAIL_*.md
   → Plans/PLAN_<ts>_EMAIL_<slug>.md   (objective, steps, status: awaiting_approval)
   → Pending_Approval/APPROVAL_<ts>_email_<slug>.md
     (action: send_email, reason, parameters: {to, subject, body, reply_to_uid})
   Moves EMAIL_*.md → Done/DONE_EMAIL_*.md

3. Human in Obsidian
   Drags APPROVAL_*.md from Pending_Approval/ → Approved/

4. ApprovalWatcher (every 5s)
   Detects new file in Approved/
   → Needs_Action/ACTION_<ts>_<slug>.md
     (type: action_trigger, approval_file, action_type: send_email, action_params)

5. execute-plan skill
   Reads ACTION_*.md
   Calls email-mcp send_email(to, subject, body, reply_to_uid)
   On success:
     → Moves ACTION_*.md → Done/
     → Updates PLAN_*.md status: executed
     → Moves APPROVAL_*.md → Done/
     → Appends Logs/YYYY-MM-DD.json

6. email-mcp
   smtplib.SMTP_SSL → sends email
   Returns {status: sent, message_id}
```

### Flow B — LinkedIn Post Generated and Published

```
1. linkedin-post skill (Monday 8 AM cron or manual)
   Reads Business_Goals.md
   Generates 100–300 word post
   → Plans/PLAN_<ts>_linkedin.md
   → Pending_Approval/APPROVAL_<ts>_linkedin.md
     (action: linkedin_post, parameters: {post_content})

2. Human in Obsidian
   Reviews post content in APPROVAL_*.md
   Drags to Approved/ (or Rejected/ to discard)

3. ApprovalWatcher (every 5s)
   Detects file in Approved/
   → Needs_Action/ACTION_<ts>_linkedin.md

4. execute-plan skill
   Calls browsing-with-playwright MCP (LinkedIn workflow)
   DRY_RUN=true → logs to Logs/; no real post
   DRY_RUN=false → Playwright navigates LinkedIn → posts content
   On success: moves all files to Done/

5. Dashboard.md updated
   Pending approvals count: 0
   Recent completions: LinkedIn post published
```

### Flow C — WhatsApp Message Captured (Receive-Only)

```
1. WhatsAppWatcher (every 60s)
   Playwright polls web.whatsapp.com
   → Needs_Action/WA_<ts>_<sender>.md
     (type: whatsapp, sender, message_text, received)

2. process-needs-action skill
   Reads WA_*.md
   Summarises message context
   → Plans/PLAN_<ts>_WA_<slug>.md (status: complete — no outbound action in Silver)
   Moves WA_*.md → Done/DONE_WA_*.md
   Updates Dashboard.md
```

---

## Agent Skills Design

All skills created via the `skill-creator` skill (per CLAUDE.md rule).

| Skill | Purpose | Inputs | Outputs | MCP Calls |
|-------|---------|--------|---------|-----------|
| `process-needs-action` | Process all Needs_Action tasks | `Needs_Action/*.md`, `Company_Handbook.md` | `Plans/PLAN_*.md`, `Pending_Approval/APPROVAL_*.md` | None |
| `linkedin-post` | Generate LinkedIn lead-gen post | `Business_Goals.md`, `Company_Handbook.md` | `Plans/PLAN_*_linkedin.md`, `Pending_Approval/APPROVAL_*_linkedin.md` | None |
| `execute-plan` | Execute approved actions | `Approved/APPROVAL_*.md` (via ACTION_* trigger) | `Done/DONE_*.md`, `Logs/` entries | `send_email`, `browsing-with-playwright` |

---

## Vault Structure (Extended from Bronze)

```
AI_Employee_Vault/
├── Dashboard.md              ← live counts: pending, approvals, completions, health
├── Company_Handbook.md       ← rules of engagement
├── Business_Goals.md         ← NEW: services, OKRs, LinkedIn post topics
├── Inbox/                    ← file drop zone (filesystem watcher)
├── Needs_Action/             ← all task files (EMAIL_, WA_, FILE_, ACTION_, ERROR_)
├── Plans/                    ← PLAN_*.md (Claude-generated plans)
├── Pending_Approval/         ← NEW: APPROVAL_*.md awaiting human decision
├── Approved/                 ← NEW: APPROVAL_*.md moved here by human → triggers execution
├── Rejected/                 ← NEW: APPROVAL_*.md moved here by human → archived
├── Done/                     ← all completed items (never deleted)
└── Logs/                     ← YYYY-MM-DD.json NDJSON audit trail
```

**Dashboard.md sections** (extended):
- System Status — watcher health
- Inbox Summary — `Needs_Action` count, `Inbox` count, `Done` today
- **Pending Approvals** — count of files in `Pending_Approval/` + list of filenames
- Active Items — items in `Needs_Action/`
- Recent Completions — last 5 Done/ items
- Recent Rejections — last 3 Rejected/ items

---

## Implementation Phases

### Phase 1 — Vault + Watcher Foundation (US1 — P1)
**Objective**: Gmail and WhatsApp watchers producing task files. New vault folders created.
**Deliverables**: `gmail_watcher.py`, `whatsapp_watcher.py`, `Pending_Approval/`, `Approved/`, `Rejected/`, `Business_Goals.md`, `processed_gmail.json`, `processed_whatsapp.json`
**Verification**: Send test email → `EMAIL_*.md` in `Needs_Action/` within 5 min. Send WhatsApp → `WA_*.md` within 60s.

### Phase 2 — Planning Skills (US2 — P2)
**Objective**: `process-needs-action` extended for email/whatsapp; LinkedIn post skill created; approval files written to `Pending_Approval/`.
**Deliverables**: Extended `process-needs-action` SKILL.md, new `linkedin-post` SKILL.md, `Business_Goals.md` populated
**Verification**: Email task in `Needs_Action/` → run skill → `Plans/PLAN_*.md` + `Pending_Approval/APPROVAL_*.md` created.

### Phase 3 — email-mcp (US2 — P2)
**Objective**: Python MCP server operational; `send_email`, `draft_reply`, `search_inbox` tools working.
**Deliverables**: `mcp-servers/email-mcp/server.py`, `smtp_imap.py`, MCP registration in `mcp.json`
**Verification**: Claude calls `send_email` tool → `DRY_RUN=true` logs action; `DRY_RUN=false` delivers email.

### Phase 4 — Approval Pipeline (US2 — P2)
**Objective**: `approval_watcher.py` detects files in `Approved/`; `execute-plan` skill fires MCP call.
**Deliverables**: `approval_watcher.py`, `execute-plan` SKILL.md, `processed_approvals.json`, orchestrator `--watcher` flag
**Verification**: Move APPROVAL_*.md to `Approved/` → within 5s `ACTION_*.md` in `Needs_Action/` → run execute-plan → email sent or LinkedIn posted.

### Phase 5 — Scheduling (US4 — P3)
**Objective**: Cron runs watchers and skills automatically.
**Deliverables**: `scripts/install-cron.sh`, orchestrator `--watcher` flag complete
**Verification**: Configure cron → wait for trigger → `Logs/` entry with `actor: scheduler`.

---

## End-to-End Acceptance Flow

1. Start `VAULT_PATH="$PWD/AI_Employee_Vault" .venv/bin/python orchestrator.py` → filesystem + approval watchers running
2. Send test email → within 5 min, `Needs_Action/EMAIL_*.md` appears **(SC-001)**
3. Send WhatsApp message → within 60s, `Needs_Action/WA_*.md` appears **(SC-002)**
4. Run `process-needs-action` → `Plans/PLAN_*.md` + `Pending_Approval/APPROVAL_*.md` created **(FR-007, FR-008)**
5. Move APPROVAL_*.md to `Approved/` → within 5s `ACTION_*.md` triggers → run `execute-plan` → email sent **(SC-006)**
6. Run `linkedin-post` skill → `Pending_Approval/APPROVAL_*_linkedin.md` → approve → LinkedIn post published **(SC-005)**
7. Check `Dashboard.md` → updated counts, zero pending approvals **(FR-023)**
8. Check `Logs/YYYY-MM-DD.json` → entries for every action with actor, result **(V. Security & Ops)**
9. Restart Gmail watcher; resend same email → no duplicate task **(SC-004)**
10. Confirm no credentials in any `.md` or committed file **(SC-008)**
