# Personal AI Employee

*Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

An autonomous Digital FTE (Full-Time Equivalent) powered by **Claude Code** and **Obsidian**. Monitors Gmail, WhatsApp, and bank transactions; drafts replies, social posts, and invoices; and executes approved actions — all while keeping humans in the loop for every sensitive decision.

---

## Current Tier: Platinum ✅

All four tiers complete. The system runs 24/7: a cloud agent on AWS EC2 handles continuous triage while the local machine retains all execution credentials and human approval authority.

| Tier | Status | Key capability |
|------|--------|---------------|
| Bronze | ✅ Complete | Vault + filesystem watcher + `process-needs-action` skill |
| Silver | ✅ Complete | Gmail + WhatsApp watchers + LinkedIn MCP + scheduling |
| Gold | ✅ Complete | Odoo + social media + CEO briefing + Ralph Wiggum loop |
| Platinum | ✅ Complete | 24/7 cloud agent + vault sync + multi-agent coordination |

---

## Architecture

### Platinum System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD VM (24/7)                          │
│                     AWS EC2 t2.micro                            │
│                                                                 │
│  Gmail Watcher ──► Needs_Action/EMAIL_*.md                      │
│  Signals Watcher ──► routes SIGNAL_*.md                         │
│  Heartbeat Writer ──► Updates/HEARTBEAT_*.md (every 5 min)      │
│  Stale Task Monitor ──► recovers In_Progress/local/ timeouts    │
│  Cloud Orchestrator ──► cloud-triage skill                      │
│        │                                                        │
│        ▼                                                        │
│  Plans/PLAN_*.md  ──────────────────────────────────────────┐   │
│  Pending_Approval/APPROVAL_*.md ────────────────────────┐   │   │
│  Signals/SIGNAL_*.md ───────────────────────────────┐   │   │   │
└─────────────────────────────────────────────────────│───│───│───┘
                      Syncthing (≤60s)                │   │   │
┌─────────────────────────────────────────────────────│───│───│───┐
│                  LOCAL MACHINE (Windows 11)          ▼   ▼   ▼   │
│                                                                 │
│  process-needs-action ◄── reads cloud Plans/PLAN_*.md           │
│  Human review ◄── Pending_Approval/APPROVAL_*.md                │
│        │                                                        │
│        ▼  (human moves file to Approved/)                       │
│  execute-plan ──► Email MCP / Social MCP / Odoo MCP             │
│        │                                                        │
│        ▼                                                        │
│  Done/ + Logs/YYYY-MM-DD.json (audit trail)                     │
│  Dashboard.md (single writer: local only)                       │
└─────────────────────────────────────────────────────────────────┘
```

**Perception:** Python watcher scripts on both machines monitor inputs (Gmail, WhatsApp, files, bank CSV) and write structured `.md` files to `Needs_Action/`.

**Reasoning:** Claude Code applies `Company_Handbook.md` rules, drafts plans, and decides what to do. The cloud agent drafts; the local agent executes.

**Action:** Safe actions execute directly. Sensitive ones wait in `Pending_Approval/` for human sign-off before any MCP tool is called.

### Cloud / Local Responsibility Split

| Responsibility | Cloud Agent | Local Agent |
|---------------|-------------|-------------|
| Gmail polling (24/7) | ✅ | Backup only |
| Task triage + plan drafting | ✅ | Reads cloud plans |
| Social post drafting | ✅ | — |
| Odoo draft invoices/expenses | ✅ (draft only) | — |
| Email send / social publish | ❌ Never | ✅ After approval |
| Odoo post invoice | ❌ Never | ✅ After approval |
| Dashboard.md writes | ❌ Never | ✅ Only |
| Execution credentials (.env) | ❌ Never | ✅ Only |
| Heartbeat + signals | ✅ Writes | ✅ Monitors |
| Stale task recovery | Monitors `In_Progress/local/` | Monitors `In_Progress/cloud/` |

---

## Project Structure

```
Personal_AI_Employee/
│
├── orchestrator.py              ← Local agent: starts all local watchers + watchdog
├── cloud_orchestrator.py        ← Cloud agent: starts cloud watchers + cron scheduler
│
├── watchers/
│   ├── base_watcher.py          ← Base class (PollingObserver, idempotency)
│   ├── filesystem_watcher.py    ← Monitors Inbox/ for file drops
│   ├── gmail_watcher.py         ← Gmail IMAP poller (AGENT_ROLE-aware)
│   ├── gmail_api_watcher.py     ← Gmail OAuth API poller
│   ├── gmail_api_auth.py        ← OAuth token refresh logic
│   ├── whatsapp_watcher.py      ← WhatsApp Web via Playwright
│   ├── approval_watcher.py      ← Polls Approved/ → triggers execute-plan
│   ├── finance_watcher.py       ← Bank CSV → Bank_Transactions.md
│   ├── heartbeat_writer.py      ← Cloud: writes HEARTBEAT_*.md every 5 min
│   ├── signals_watcher.py       ← Routes SIGNAL_*.md files by type
│   ├── stale_task_monitor.py    ← Recovers stuck In_Progress/ tasks
│   └── cloud_boundary.py        ← safe_vault_write() guard + write boundary
│
├── mcp-servers/
│   ├── email-mcp/               ← Gmail send/draft/search (Node.js)
│   ├── odoo-mcp/                ← Odoo JSON-RPC (invoices, transactions, expenses)
│   │   └── handlers/            ← invoice_handlers, customer_handlers, transaction_handlers
│   └── social-mcp/              ← LinkedIn, Facebook, Instagram, Twitter
│       └── handlers/            ← One handler per platform
│
├── .claude/skills/
│   ├── process-needs-action/    ← Main triage skill (reads Needs_Action/, creates Plans/)
│   ├── execute-plan/            ← Executes approved MCP actions
│   ├── cloud-triage/            ← Cloud: drafts plans, never calls execution MCP
│   ├── ceo-briefing/            ← Weekly CEO briefing (Sunday 23:00)
│   ├── cloud-briefing-prep/     ← Cloud: writes Updates/BRIEFING_DATA_*.md
│   ├── vault-health/            ← Checks vault folder health + sync lag
│   ├── constitution-check/      ← Verifies all 15 architecture principles
│   ├── linkedin-post/           ← Drafts LinkedIn lead-gen post
│   ├── facebook-post/           ← Drafts Facebook post for approval
│   ├── instagram-post/          ← Drafts Instagram post for approval
│   ├── twitter-post/            ← Drafts Twitter post for approval
│   ├── odoo-integration/        ← Odoo invoice + expense workflow
│   ├── reasoning-loop/          ← Ralph Wiggum persistence loop
│   ├── whatsapp-reply/          ← WhatsApp reply drafting
│   └── email-queue-manager/     ← Email queue management
│
├── scripts/
│   ├── provision-cloud.sh       ← Idempotent cloud VM provisioning (Ubuntu 24.04)
│   ├── check_loop_complete.py   ← Stop hook for Ralph Wiggum loop
│   ├── ralph_loop.py            ← Ralph Wiggum loop launcher
│   ├── sync/
│   │   ├── .stignore            ← Syncthing exclusion list (.env, sessions, processed JSONs)
│   │   ├── setup-syncthing.sh   ← Automates Syncthing device pairing + folder config
│   │   ├── audit-sync-log.sh    ← Polls Syncthing REST API → Sync/sync.log
│   │   └── security-boundary-test.sh ← Verifies cloud VM holds zero execution credentials
│   └── systemd/
│       ├── cloud-agent.service  ← systemd unit for cloud_orchestrator.py
│       └── syncthing-cloud.service ← systemd unit for Syncthing daemon
│
├── AI_Employee_Vault/           ← Obsidian vault (synced between local + cloud)
├── specs/                       ← Spec-Driven Development artifacts (all 4 tiers)
├── .env.example                 ← Environment variable reference
├── requirements.txt             ← Python dependencies
└── CLAUDE.md                    ← Agent instructions + project rules
```

---

## Vault Structure (Platinum)

```
AI_Employee_Vault/
├── Dashboard.md              ← Real-time status (local agent only — Single Writer Rule)
├── Company_Handbook.md       ← Rules of engagement (edit to change AI behaviour)
├── Business_Goals.md         ← OKRs, revenue targets, subscription audit rules
├── Bank_Transactions.md      ← Finance watcher output
│
├── Inbox/                    ← Drop zone: any file dropped here becomes a task
├── Needs_Action/             ← Task files: EMAIL_*, WA_*, FILE_*, SIGNAL_*, ERROR_*
├── In_Progress/
│   ├── cloud/                ← Tasks claimed by cloud agent (claim-by-move)
│   └── local/                ← Tasks claimed by local agent (claim-by-move)
├── Plans/                    ← PLAN_*.md files (cloud drafts, local reads)
├── Pending_Approval/         ← APPROVAL_*.md awaiting human decision
├── Approved/                 ← Human-approved → triggers execute-plan
├── Rejected/                 ← Declined actions (archived, never deleted)
├── Done/                     ← Completed tasks (never deleted)
│
├── Updates/                  ← Cloud-only writes: HEARTBEAT_*.md, BRIEFING_DATA_*.md
├── Signals/                  ← Inter-agent signals: SIGNAL_*.md (routed by signals_watcher)
├── Sync/                     ← sync.log, sync-config.md (Syncthing metadata)
│
├── Briefings/                ← Weekly CEO briefings + compliance reports
├── Accounting/               ← Monthly bank transaction logs
└── Logs/                     ← Audit trail: YYYY-MM-DD.json (90-day retention, NDJSON)
```

---

## Quickstart (Platinum)

**Prerequisites:** Windows 11, Python 3.12+, Git, Obsidian, Syncthing (Windows), AWS account

### Local setup (5 minutes)

```bash
git clone https://github.com/alihaidernoorani/Personal-AI-Employee.git
cd Personal-AI-Employee
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env   # set VAULT_PATH, GMAIL_EMAIL, GMAIL_APP_PASSWORD
python orchestrator.py
```

### Cloud VM setup (30–45 minutes)

See [`specs/004-platinum-ai-employee/quickstart.md`](specs/004-platinum-ai-employee/quickstart.md) for the full step-by-step guide covering:
1. Provisioning an AWS EC2 t2.micro (Ubuntu 24.04)
2. Running `scripts/provision-cloud.sh` — installs Python 3.13, Docker, Syncthing, Odoo, starts systemd services
3. Configuring Syncthing bidirectional vault sync (≤60s latency)
4. Verifying heartbeats, security boundary, and end-to-end email triage flow

---

## Security

### Credential Storage

| Secret | Where stored | Git-tracked? |
|--------|-------------|--------------|
| `GMAIL_APP_PASSWORD` | `.env` (local only) | No — `.gitignore` |
| MCP env vars | `.mcp.json` (local only) | No — `.gitignore` |
| WhatsApp session | `whatsapp_session/` | No — `.gitignore` |
| Cloud VM credentials | `/root/.env.cloud` (cloud VM only) | No — never synced |
| Odoo credentials | `.env` (local) + `/root/.env.cloud` (cloud, draft-only) | No |

### Security Boundary (Platinum)

The cloud VM is designed to hold **zero execution credentials**. Enforced at three independent layers:

1. **Syncthing `.stignore`** — `.env`, `*.token`, `*_session/`, `processed_*.json` are excluded from sync at the transport layer
2. **`safe_vault_write()` guard** — all cloud-side vault writes go through `watchers/cloud_boundary.py` which raises `PermissionError` on prohibited paths (`Dashboard.md`, `Done/`, `Approved/`, `Rejected/`)
3. **`cloud_orchestrator.py` startup check** — validates `AGENT_ROLE=cloud`, asserts no execution MCP tools registered, verifies `ODOO_DRAFT_ONLY=true`

Run `scripts/sync/security-boundary-test.sh` at any time to verify (8 checks, all must PASS).

### Human-in-the-Loop (HITL)

Sensitive actions are **never executed automatically**:

1. Claude writes `Pending_Approval/APPROVAL_*.md` — no action taken
2. Human reviews in Obsidian
3. Human moves to `Approved/` (execute) or `Rejected/` (archive)
4. Only then does `execute-plan` call any MCP tool

### Permission Boundaries

| Action | Auto-approved | Requires human approval |
|--------|--------------|------------------------|
| Email replies | Never | Always |
| Social media posts | Never | Always |
| Payments < $50, known payee | Yes | — |
| Payments > $100 or new payee | Never | Always |
| File create/read/move in vault | Yes | Delete or move outside vault |

---

## Key Architectural Decisions

**1. Syncthing over rsync/SSH**
P2P bidirectional sync with folder-authority modes enforces the write boundary at the transport layer. No custom merge logic. `.stignore` keeps secrets local.

**2. `AGENT_ROLE` environment variable**
One codebase, two machines. `AGENT_ROLE=cloud` activates `cloud_orchestrator.py`. Bug fixes and skill updates deploy everywhere with one `git pull`.

**3. Claim-by-move for task coordination**
Filesystem rename is atomic. First agent to move a file from `Needs_Action/` to `In_Progress/<agent>/` owns it — no distributed lock, no race condition.

---

## Cost

| Option | Monthly | Notes |
|--------|---------|-------|
| AWS EC2 t2.micro | Free (12 months) | Used in this project |
| Hetzner CX22 | ~€3.79/month | Recommended after AWS free tier expires |
| Oracle Cloud A1 | Free (always) | High demand — hard to provision |

---

## Submission

- Tier: **Platinum**
- Branch: `004-platinum-ai-employee`
- Cloud VM: AWS EC2 t2.micro (Ubuntu 24.04 LTS) — `54.242.137.247`
- Vault sync: Syncthing bidirectional, ≤60s latency verified
- Security boundary: 8/8 checks PASS
