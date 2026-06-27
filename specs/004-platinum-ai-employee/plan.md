# Implementation Plan: Platinum Tier Personal AI Employee

**Branch**: `004-platinum-ai-employee` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-platinum-ai-employee/spec.md`
**Baseline**: Builds on `003-gold-ai-employee` — all Gold components remain unchanged unless noted.

---

## Summary

Extend the Gold-tier AI Employee to run 24/7 by splitting reasoning and execution across a cloud VM and the local machine. The cloud agent handles continuous triage, drafting, and scheduling via a synchronised vault replica; the local agent retains exclusive execution authority and all credentials. Bidirectional rsync-over-SSH vault sync (≤60 s latency SLA) is the sole communication bus. Multi-agent task ownership is enforced by claim-by-move across two `In_Progress/` subdirectories. All 15 constitution principles are verified by a new `constitution-check` skill before the tier is declared complete.

---

## Technical Context

**Language/Version**: Python 3.13+ (cloud watchers, heartbeat writer, stale-task monitor, orchestrator extensions); inherits all Gold Python dependencies on both machines  
**Primary Dependencies (new)**: `rsync` ≥ 3.2.7 (sync); `paramiko>=3.4` or `openssh-client` (SSH key management); `pytest>=8.0.0` with `pytest-mock` (tests)  
**Storage**: Obsidian vault (markdown files) replicated on both machines; `Sync/sync.log` (append-only plain text); heartbeat files auto-expire after 10 minutes  
**Testing**: `pytest` unit + integration; multi-agent coordination test (two concurrent Python processes hitting the same vault replica); latency test (file write → sync → detect on remote, measured in seconds)  
**Target Platform (cloud VM)**: Ubuntu 24.04 LTS; Hetzner CX22 (2 vCPU AMD, 4 GB RAM, 40 GB NVMe SSD) ~€3.79/month (~$4.10); SSH key-only auth; 99.9% uptime SLA  
**Target Platform (local)**: Windows 11 Pro + WSL2 Ubuntu (all Python daemons run inside WSL2 for POSIX compatibility); vault on NTFS, accessed via `/mnt/c/` — `PollingObserver` required  
**Sync Mechanism**: Syncthing (P2P daemon); sub-second file detection via inotify; `.stignore` exclusion list enforces secrets boundary; folder-level Send-Only / Receive-Only modes enforce conflict resolution by policy (no custom logic needed)  
**Project Type**: Distributed single-user system — local daemon cluster + cloud daemon cluster + shared vault (rsync)  
**Performance Goals**: Email → cloud plan in `Plans/` within 5 min; vault sync round-trip ≤ 60 s; heartbeat detection lag ≤ 10 min; stale task recovery ≤ 20 min  
**Constraints**: Cloud VM holds zero execution credentials; Dashboard.md written by local only; cloud writes exclusively to `Updates/`, `Signals/`, `Plans/`, `In_Progress/cloud/`; `DRY_RUN=true` default; all 15 constitution principles enforced and verified  
**Scale/Scope**: Single-user; ~5 cloud daemon processes + ~6 local daemon processes; vault ~1,200 files at steady state; ~15 GB cloud VM storage (vault + venv + logs)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| # | Principle | Requirement | Status |
|---|-----------|-------------|--------|
| I | Production First | Every Platinum component ships-ready; no demo stubs | ✅ All phases gated on acceptance criteria; no placeholder code |
| II | Local First | Sensitive data (credentials, sessions, .env) never leaves local machine | ✅ Sync excludes `.env`, session dirs, processed_*.json; cloud holds only read-only Gmail OAuth + sync token |
| III | Cloud Worker | Cloud agent MUST NOT call execution MCP tools | ✅ Cloud agent accesses only cloud-side `odoo-mcp` in draft-only mode (`create_invoice`, `update_expense`); all execution operations (email send, social post, `post_invoice`, payment) remain local-only |
| IV | Human In The Loop | All sensitive actions require `APPROVAL_*.md` before execution | ✅ HITL gate unchanged from Gold; cloud prepares plans, local presents for approval |
| V | Vault Driven Architecture | Agents communicate only through vault files; no direct inter-agent network calls | ✅ rsync vault is the only shared bus; no direct cloud↔local socket |
| VI | Claim-by-Move | Task ownership = first agent to move to `In_Progress/<agent>/` | ✅ Cloud uses `In_Progress/cloud/`; local uses `In_Progress/local/`; stale-task recovery defined |
| VII | Single Writer Rule | `Dashboard.md` written by local only; cloud writes `Updates/`, `Signals/`, `Plans/` only | ✅ Cloud agent never writes Dashboard.md; violation produces `SINGLE_WRITER_VIOLATION_*.md` |
| VIII | Event Driven | No busy-wait; `PollingObserver` on NTFS; sleep between cycles | ✅ All watchers use configurable `check_interval`; heartbeat writer sleeps 300 s between cycles |
| IX | Modular Design | Each integration isolated; no God Objects | ✅ New skills (`cloud-triage`, `vault-health`, `constitution-check`, `cloud-briefing-prep`) each have single responsibility |
| X | Agent Skills | All AI logic in `.claude/skills/`; watchers are perception-only | ✅ Cloud-side triage encapsulated in `cloud-triage` skill; cloud watchers write task files only |
| XI | Observability | Every action → structured audit record in `Logs/YYYY-MM-DD.json` | ✅ Sync operations → `Sync/sync.log`; heartbeats → `Updates/`; all MCP calls logged on local |
| XII | Reliability | Retry, timeout, watchdog, graceful degradation | ✅ Stale-task recovery, heartbeat monitor, network-partition buffering all defined |
| XIII | Security | No secrets in .md files; `.env` gitignored; `DRY_RUN=true` default | ✅ Rsync exclude list; cloud VM secrets audit in constitution-check; `DRY_RUN=true` on both machines |
| XIV | Documentation | Every folder/module/watcher/skill documented | ✅ Deployment guide, architecture diagram, per-component docs required as deliverables |
| XV | Code Quality | SOLID, DI, strong typing, no file >300 lines | ✅ `constitution-check` enforces file-size limit; new modules follow same patterns as Gold |

**GATE: PASSED — all 15 principles satisfied by design. Proceeding to Phase 0 research.**

---

## Project Structure

### Documentation (this feature)

```text
specs/004-platinum-ai-employee/
├── plan.md                          ← This file
├── research.md                      ← Phase 0 findings (sync mechanism, VM specs, automation)
├── data-model.md                    ← Platinum entity additions and state machine extensions
├── quickstart.md                    ← Cloud VM provisioning + vault sync setup guide
├── checklists/
│   └── requirements.md              ← Spec quality checklist (already complete)
├── contracts/
│   ├── vault-sync-protocol.md       ← rsync config, exclusion list, conflict rules
│   ├── cloud-agent-interface.md     ← What the cloud agent may/may not write
│   ├── heartbeat-protocol.md        ← Heartbeat format and monitoring contract
│   └── signals-protocol.md          ← Signal types, routing, and response rules
└── tasks.md                         ← Generated by /sp.tasks (not this command)
```

### Source Code (repository root)

```text
watchers/
├── base_watcher.py                  # ✅ EXISTS — no changes
├── gmail_watcher.py                 # ✅ EXISTS (local) — deploy copy to cloud VM
├── gmail_api_watcher.py             # ✅ EXISTS — deploy copy to cloud VM (alternative)
├── whatsapp_watcher.py              # ✅ EXISTS — local only (browser session)
├── filesystem_watcher.py            # ✅ EXISTS (local Inbox/) — cloud variant for Signals/
├── approval_watcher.py              # ✅ EXISTS — local only
├── finance_watcher.py               # ✅ EXISTS — local only (bank credentials)
├── heartbeat_writer.py              # ❌ TO BUILD — cloud: writes HEARTBEAT_*.md every 5 min
├── stale_task_monitor.py            # ❌ TO BUILD — both agents: returns stranded tasks
└── signals_watcher.py               # ❌ TO BUILD — both agents: monitors Signals/ for alerts

scripts/
├── processed_gmail.json             # ✅ EXISTS — cloud copy at cloud:scripts/processed_gmail.json
├── sync/
│   ├── setup-syncthing.sh           # ❌ TO BUILD — automates device pairing via Syncthing REST API
│   ├── audit-sync-log.sh            # ❌ TO BUILD — polls Syncthing /rest/events, writes Sync/sync.log
│   └── .stignore                    # ❌ TO BUILD — Syncthing exclusion list (secrets, sessions, state)
└── provision-cloud.sh               # ❌ TO BUILD — cloud VM provisioning (installs Syncthing + Python)

mcp-servers/
├── email-mcp/                       # ✅ EXISTS — local only; no changes
├── social-mcp/                      # ✅ EXISTS — local only; no changes
└── odoo-mcp/                        # ✅ EXISTS — extended for Platinum dual-mode:
#                                      Cloud VM: draft-only (create_invoice, update_expense);
#                                      activated by AGENT_ROLE=cloud + ODOO_DRAFT_ONLY=true
#                                      Local: full operations (post_invoice, etc.);
#                                      ODOO_URL points to cloud Odoo HTTPS endpoint

scripts/
├── odoo/
│   ├── docker-compose.yml           # ❌ TO BUILD — Odoo Community + PostgreSQL on cloud VM
│   ├── nginx.conf                   # ❌ TO BUILD — HTTPS reverse proxy + Let's Encrypt
│   └── backup-odoo.sh               # ❌ TO BUILD — daily pg_dump + 7-day retention cron

.claude/
├── skills/
│   ├── process-needs-action/SKILL.md    # ✅ EXISTS — local; no changes
│   ├── execute-plan/SKILL.md            # ✅ EXISTS — local; no changes
│   ├── ceo-briefing/SKILL.md            # ✅ EXISTS — local; update to consume Updates/BRIEFING_DATA_*.md
│   ├── linkedin-post/SKILL.md           # ✅ EXISTS — local; no changes
│   ├── facebook-post/SKILL.md           # ✅ EXISTS — local; no changes
│   ├── instagram-post/SKILL.md          # ✅ EXISTS — local; no changes
│   ├── twitter-post/SKILL.md            # ✅ EXISTS — local; no changes
│   ├── whatsapp-reply/SKILL.md          # ✅ EXISTS — local; no changes
│   ├── finance-triage/SKILL.md          # ✅ EXISTS — local; no changes
│   ├── odoo-integration/SKILL.md        # ✅ EXISTS — local; no changes
│   ├── cloud-triage/SKILL.md            # ❌ TO BUILD — cloud: classify + draft plans
│   ├── vault-health/SKILL.md            # ❌ TO BUILD — both: validate vault structure + sync recency
│   ├── constitution-check/SKILL.md      # ❌ TO BUILD — local: 15-principle compliance scan
│   └── cloud-briefing-prep/SKILL.md     # ❌ TO BUILD — cloud: gather data → Updates/BRIEFING_DATA_*.md
└── settings.json                        # ✅ EXISTS — local; add stale-task monitor + heartbeat detection

AI_Employee_Vault/
├── Dashboard.md                         # ✅ EXISTS — add Cloud Agent Status section
├── Company_Handbook.md                  # ✅ EXISTS — no changes
├── Business_Goals.md                    # ✅ EXISTS — no changes
├── Bank_Transactions.md                 # ✅ EXISTS — no changes
├── Inbox/                               # ✅ EXISTS
├── Needs_Action/                        # ✅ EXISTS
├── In_Progress/
│   ├── local/                           # ❌ RENAME from local_agent/ → local/ (spec alignment)
│   └── cloud/                           # ❌ TO CREATE — cloud agent's claimed tasks
├── Plans/                               # ✅ EXISTS
├── Pending_Approval/                    # ✅ EXISTS
├── Approved/                            # ✅ EXISTS
├── Rejected/                            # ✅ EXISTS
├── Done/                                # ✅ EXISTS
├── Briefings/                           # ✅ EXISTS
├── Accounting/                          # ✅ EXISTS
├── Logs/                                # ✅ EXISTS
├── Updates/                             # ❌ TO CREATE — cloud agent status + heartbeats
├── Signals/                             # ❌ TO CREATE — cross-agent alerts
└── Sync/                                # ❌ TO CREATE — sync.lock + sync.log

orchestrator.py                          # ✅ EXISTS — extend with cloud health monitor
cloud_orchestrator.py                    # ❌ TO BUILD — cloud VM process manager (subset of orchestrator.py)
.env.example                             # ✅ EXISTS — add CLOUD_VM_HOST, CLOUD_VM_USER, CLOUD_VAULT_PATH, SYNC_INTERVAL_SECONDS
requirements.txt                         # ✅ EXISTS — add paramiko, schedule (if not present)
```

**Structure Decision**: Same single-project layout as Gold. Cloud VM runs a subset of the same codebase (checked out via git or rsync'd). No separate repo. Cloud-specific processes are activated by environment variable `AGENT_ROLE=cloud` vs. `AGENT_ROLE=local`.

---

## Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║               PLATINUM TIER AI EMPLOYEE — CLOUD / LOCAL SPLIT OVERVIEW               ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

 ┌─────────────────────────────────┐         ┌──────────────────────────────────────┐
 │       CLOUD VM (24/7)           │         │         LOCAL MACHINE                │
 │  Hetzner CX21 / Ubuntu 24.04   │         │  Windows 11 + WSL2 Ubuntu            │
 │                                 │         │                                      │
 │  PERCEPTION                     │         │  PERCEPTION                          │
 │  ─────────                      │         │  ─────────                           │
 │  gmail_watcher.py (primary)     │         │  gmail_watcher.py (fallback)         │
 │  signals_watcher.py             │         │  signals_watcher.py                  │
 │  heartbeat_writer.py            │         │  whatsapp_watcher.py                 │
 │  stale_task_monitor.py          │         │  finance_watcher.py                  │
 │                                 │         │  filesystem_watcher.py               │
 │  REASONING (Claude Code)        │         │  approval_watcher.py                 │
 │  ─────────────────────          │         │  stale_task_monitor.py               │
 │  cloud-triage skill             │         │                                      │
 │  cloud-briefing-prep skill      │         │  REASONING (Claude Code)             │
 │  vault-health skill             │         │  ─────────────────────               │
 │                                 │         │  process-needs-action skill          │
 │  WRITES ONLY TO:                │         │  execute-plan skill                  │
 │  ✅ Plans/                      │         │  ceo-briefing skill                  │
 │  ✅ Updates/                    │         │  constitution-check skill            │
 │  ✅ Signals/                    │         │  vault-health skill                  │
 │  ✅ In_Progress/cloud/          │         │  linkedin-post + social skills       │
 │  ✅ Needs_Action/ (new only)    │         │                                      │
 │                                 │         │  WRITES TO:                          │
 │  NEVER WRITES TO:               │         │  ✅ Dashboard.md (exclusive)         │
 │  ❌ Dashboard.md                │         │  ✅ Done/                            │
 │  ❌ Done/                       │         │  ✅ Approved/ (after human move)     │
 │  ❌ Approved/                   │         │  ✅ Rejected/ (after human move)     │
 │  ❌ Rejected/                   │         │  ✅ In_Progress/local/               │
 │                                 │         │  ✅ Logs/ (all MCP audit records)    │
 │  MCP (draft-only, local Odoo):  │         │                                      │
 │  ✅ odoo-mcp (ODOO_DRAFT_ONLY)  │         │  MCP (full, cloud Odoo via HTTPS):   │
 │     create_invoice (draft)      │         │  ✅ odoo-mcp post_invoice etc.       │
 │     update_expense (draft)      │         │  ✅ email-mcp  social-mcp  browser   │
 │  ❌ All other MCP tools         │         │                                      │
 │                                 │         │                                      │
 └───────────────┬─────────────────┘         └──────────────────┬───────────────────┘
                 │                                               │
                 │          VAULT SYNC (rsync over SSH)          │
                 │  ◄──────────────────────────────────────────► │
                 │  Interval: every 30 s (bidirectional)         │
                 │  Encrypted: SSH transport                     │
                 │  Excluded: .env, sessions, credentials        │
                 │  Conflict: local wins for authoritative       │
                 │  folders; cloud wins for Updates/Signals/     │
                 │  Audit: Sync/sync.log (append-only)           │
                 │                                               │
                 └──────────────┬────────────────────────────────┘
                                │
                 ┌──────────────▼──────────────────┐
                 │         OBSIDIAN VAULT           │
                 │   (single source of truth)       │
                 │                                  │
                 │  Needs_Action/  ← watchers write │
                 │  In_Progress/                    │
                 │  ├── cloud/    ← cloud claims    │
                 │  └── local/    ← local claims    │
                 │  Plans/        ← cloud writes    │
                 │  Updates/      ← cloud writes    │
                 │  Signals/      ← either writes   │
                 │  Pending_Approval/ ← local skill │
                 │  Approved/     ← human moves     │
                 │  Rejected/     ← human moves     │
                 │  Done/         ← local skill     │
                 │  Dashboard.md  ← local only      │
                 │  Logs/         ← local MCP audit │
                 │  Briefings/    ← local skill     │
                 │  Sync/         ← rsync process   │
                 └─────────────────────────────────-┘

 ACTION LAYER (local machine only — no cloud access)
 ────────────────────────────────────────────────────
 email-mcp/    social-mcp/    odoo-mcp/    browser-mcp/
 (Python)      (Python)       (Python)     (npx Playwright)
     │               │              │            │
     └───────────────┴──────────────┴────────────┘
                          │
              All results → Logs/YYYY-MM-DD.json
              (NDJSON, 90-day retention)

 HITL APPROVAL GATE (local only)
 ──────────────────────────────────
 Pending_Approval/APPROVAL_*.md
    │
    ▼ (human moves in Obsidian)
 Approved/  →  approval_watcher.py  →  execute-plan skill  →  MCP call  →  Done/
 Rejected/  →  permanent archive (never executed)

 SCHEDULED OPERATIONS (cloud_orchestrator.py + local orchestrator.py)
 ─────────────────────────────────────────────────────────────────────
 Cloud  every 30 s  → rsync bidirectional sync
 Cloud  every 5 min → heartbeat_writer.py → Updates/HEARTBEAT_*.md
 Cloud  every 10 min → Odoo health check → SIGNAL_odoo_down / SIGNAL_cert_expiry on failure
 Cloud  every 2 min → stale_task_monitor.py (In_Progress/cloud/)
 Cloud  Sunday 22:00 → cloud-briefing-prep skill → Updates/BRIEFING_DATA_*.md
 Cloud  daily 00:05 → backup-odoo.sh cron → /opt/odoo-backups/ (pg_dump)
 Local  every 30 s  → rsync bidirectional sync
 Local  every 2 min → stale_task_monitor.py (In_Progress/cloud/)
 Local  every 10 min → heartbeat monitor check (detect cloud agent down)
 Local  Sunday 23:00 → ceo-briefing skill (reads BRIEFING_DATA_*.md)
 Local  daily 08:00  → process-needs-action skill (catch-up sweep)
 Local  on demand   → constitution-check skill
```

---

## Implementation Phases

### Phase 0: Cloud VM Infrastructure & Vault Sync

**Goal**: Establish the 24/7 cloud VM and bidirectional vault synchronisation before any cloud agent logic is built. Infrastructure first — nothing else works without it.

**Deliverables**:
- Cloud VM provisioned (Ubuntu 24.04 LTS, SSH key-only auth, Python 3.13 venv)
- `scripts/provision-cloud.sh` — idempotent provisioning script (installs Syncthing + Python env + Odoo)
- `scripts/sync/setup-syncthing.sh` — device-pairing script (automates API-based config after first daemon start)
- `scripts/sync/.stignore` — Syncthing exclusion list (`.env`, session dirs, credentials, `processed_*.json`)
- Syncthing folder configuration: local-authoritative folders set as Send-Only on local / Receive-Only on cloud; cloud-authoritative folders inverted
- `AI_Employee_Vault/Sync/` — sync metadata folder (`sync.log` written by cron audit script)
- `AI_Employee_Vault/Updates/` — cloud agent output folder
- `AI_Employee_Vault/Signals/` — cross-agent alert folder
- `AI_Employee_Vault/In_Progress/cloud/` — cloud agent claim folder
- Rename `In_Progress/local_agent/` → `In_Progress/local/` (spec alignment)
- Vault sync cron (every 30 s) active on cloud VM
- `.env.example` updated with `CLOUD_VM_HOST`, `CLOUD_VM_USER`, `CLOUD_VAULT_PATH`, `SYNC_INTERVAL_SECONDS`, `ODOO_CLOUD_URL`, `ODOO_DRAFT_ONLY`
- `scripts/odoo/docker-compose.yml` — Odoo Community + PostgreSQL containers on cloud VM
- `scripts/odoo/nginx.conf` — nginx HTTPS reverse proxy with Let's Encrypt TLS termination
- `scripts/odoo/backup-odoo.sh` — daily `pg_dump` cron; 7-day retention under `/opt/odoo-backups/`
- Cloud-side `odoo-mcp` deployed on cloud VM with `ODOO_DRAFT_ONLY=true` (only `create_invoice` and `update_expense` tools registered)

**Dependencies**:
- Gold tier fully operational on local machine
- SSH key pair generated and deployed to cloud VM
- Vault accessible on local machine at `VAULT_PATH`

**Acceptance Criteria**:
- Write a test file to `Signals/` on the local machine; verify it appears on the cloud VM within 60 seconds
- Write a test file to `Updates/` on the cloud VM; verify it appears on the local machine within 60 seconds
- Verify `.env` and `watchers/` session files do NOT appear on the cloud VM after sync
- Verify `sync.log` records each sync operation with correct fields
- Provisioning script completes on a fresh VM in under 30 minutes
- Sync operates for 1 hour without errors; `sync.log` shows at least 100 entries

**Risks**:
- **NTFS /mnt/c inotify**: Syncthing's inotify watcher does not work on WSL2 NTFS `/mnt/c` mounts; mitigate by running Syncthing on Windows-native (not WSL2) or configuring Syncthing's fallback polling mode for the vault path
- **Syncthing exclusion gaps**: secrets could leak if `.stignore` is incomplete; mitigate by running security boundary test (cloud VM file scan) immediately after first sync
- **Device pairing manual step**: Syncthing's initial device-ID exchange is one-time manual work; mitigate by scripting it via Syncthing REST API in `setup-syncthing.sh`
- **Clock skew**: Syncthing conflict detection uses vector clocks, but audit timestamps still need NTP; verify NTP active on both machines

---

### Phase 1: Design & Contracts

**Goal**: Document all Platinum data entities, cross-agent interface contracts, and developer quickstart before any cloud logic is coded.

**Deliverables**:
- `specs/004-platinum-ai-employee/research.md` — vault sync decision, VM specs, constitution-check automation matrix
- `specs/004-platinum-ai-employee/data-model.md` — all new Platinum entities, state machine extensions
- `specs/004-platinum-ai-employee/contracts/vault-sync-protocol.md`
- `specs/004-platinum-ai-employee/contracts/cloud-agent-interface.md`
- `specs/004-platinum-ai-employee/contracts/heartbeat-protocol.md`
- `specs/004-platinum-ai-employee/contracts/signals-protocol.md`
- `specs/004-platinum-ai-employee/quickstart.md` — cloud VM + vault sync developer guide
- Agent context updated (`update-agent-context.sh claude`)

**Dependencies**:
- Phase 0 complete (vault sync operational — validates contract assumptions)

**Acceptance Criteria**:
- All contracts reference specific file paths and schema fields
- `data-model.md` covers all 6 new Platinum entities and the 3 new state transitions
- `quickstart.md` allows a developer unfamiliar with the project to provision the cloud VM and verify sync in one session
- No unresolved NEEDS CLARIFICATION items in any contract

**Risks**:
- Sync protocol contract too prescriptive about rsync flags → mitigate by keeping contract at behaviour level (latency, conflict rules) not implementation level

---

### Phase 2: Cloud Agent Core

**Goal**: Build the cloud agent's perception layer, claim-by-move coordination, and stale-task recovery — establishing 24/7 task claim capability before cloud intelligence skills are added.

**Deliverables**:
- `watchers/heartbeat_writer.py` — writes `Updates/HEARTBEAT_*.md` every 5 minutes
- `watchers/stale_task_monitor.py` — detects + recovers stale `In_Progress/<agent>/` tasks
- `watchers/signals_watcher.py` — monitors `Signals/` on both machines
- `cloud_orchestrator.py` — cloud-side process manager (gmail watcher + heartbeat writer + stale monitor + signals watcher)
- `orchestrator.py` updated — add cloud health monitor (heartbeat absence detection), stale-task monitor, signals watcher
- `AI_Employee_Vault/Dashboard.md` updated — Cloud Agent Status section added

**Dependencies**:
- Phase 0 complete (vault sync running)
- Phase 1 complete (contracts define interface)

**Acceptance Criteria**:
- Drop 10 tasks into `Needs_Action/` with both agents active; each task processed exactly once; `Done/` contains exactly 10 records; no duplicates
- Kill cloud agent process; verify `Signals/CLOUD_AGENT_DOWN_*.md` appears on local machine within 10 minutes
- Stale task test: move a task to `In_Progress/cloud/`, kill cloud agent, verify task returns to `Needs_Action/` within the configured timeout (default 10 min) + 1 sync cycle
- Cloud agent writes heartbeat to `Updates/HEARTBEAT_*.md` every 5 minutes for a 30-minute test window; local machine detects all heartbeats
- `Dashboard.md` shows ONLINE / DEGRADED / OFFLINE for cloud agent status accurately within 10 minutes of any change

**Risks**:
- **Race condition window**: Two agents claiming the same task within the 60-second sync window; mitigate by verifying that file-move atomicity on each local filesystem prevents double-claim within each agent's own process
- **WSL2 + NTFS rename atomicity**: Windows NTFS rename is atomic but WSL2 POSIX rename over DrvFS may have different semantics; test explicitly before marking this phase complete

---

### Phase 3: Cloud Intelligence Skills

**Goal**: Add the four new Platinum Claude skills to give the cloud agent drafting and monitoring capability — transforming it from a task-claiming process into an active intelligence layer.

**Deliverables**:
- `.claude/skills/cloud-triage/SKILL.md` — classify new task files, draft response plans, write `Plans/PLAN_*.md`
- `.claude/skills/vault-health/SKILL.md` — validate vault structure, check sync.log recency, report to `Updates/VAULT_HEALTH_*.md`
- `.claude/skills/cloud-briefing-prep/SKILL.md` — gather signals, social activity, cloud uptime; write `Updates/BRIEFING_DATA_<date>.md`
- `.claude/skills/ceo-briefing/SKILL.md` updated — consume `Updates/BRIEFING_DATA_*.md` in CEO briefing assembly
- Cloud cron schedule configured: Sunday 22:00 → cloud-briefing-prep; daily → vault-health
- Each skill created using `skill-creator` skill first

**Dependencies**:
- Phase 2 complete (cloud agent running, claim-by-move working)
- Phase 1 contracts complete (cloud-agent-interface.md defines write boundary)

**Acceptance Criteria**:
- Send test email while local machine is offline; verify cloud triage produces `Plans/PLAN_*.md` within 5 minutes; verify plan syncs to local; verify approval file is created by local agent when it comes online
- Trigger `vault-health` skill manually; verify `Updates/VAULT_HEALTH_*.md` is written with correct fields
- Trigger `cloud-briefing-prep` skill; verify `Updates/BRIEFING_DATA_<date>.md` is written and consumed by `ceo-briefing` skill in next briefing run
- CEO briefing produced on schedule includes Cloud Agent Uptime section populated from cloud-prepared data
- All skills created using `skill-creator` skill (verified by SKILL.md frontmatter completeness)

**Risks**:
- **Cloud agent reasoning without local MCP**: Cloud Claude Code instance cannot call email/social/Odoo MCPs; if a skill accidentally calls an MCP, it will fail silently; mitigate by verifying cloud `.mcp.json` has zero MCP servers registered
- **Briefing data staleness**: If cloud VM is down on Sunday 22:00, `ceo-briefing` runs without cloud data; mitigate by having `ceo-briefing` fall back gracefully (mark Cloud Agent section as "data unavailable")

---

### Phase 4: Constitution Compliance

**Goal**: Build and validate the `constitution-check` skill — the formal gate that certifies the Platinum deployment meets all 15 principles.

**Deliverables**:
- `.claude/skills/constitution-check/SKILL.md` — automated 15-principle compliance scan
- `Briefings/COMPLIANCE_REPORT_<date>.md` — first passing compliance report
- `Dashboard.md` updated — Compliance Report section added (status + date + link)
- Constitution check wired into deployment verification checklist

**Dependencies**:
- Phases 0–3 complete (system fully operational — something to check)

**Acceptance Criteria**:
- Run `constitution-check`; verify report covers all 15 principles, each with PASS/FAIL/NEEDS_MANUAL_REVIEW
- Intentionally violate Principle XIII (write a mock credential to a vault .md file); re-run; verify it reports FAIL with the specific file and remediation
- Fix the violation; re-run; verify 15/15 PASS (or NEEDS_MANUAL_REVIEW for manual-only principles)
- Compliance report written to `Briefings/COMPLIANCE_REPORT_<date>.md`
- `Dashboard.md` links to the compliance report with overall status

**Risks**:
- **Automation gaps**: Some principles (I: Production First, XIV: Documentation completeness) cannot be fully automated; mitigate by documenting these as NEEDS_MANUAL_REVIEW with explicit human checklist items
- **False positives**: Automated checks may flag legitimate patterns (e.g., a test file that looks like a secret); mitigate by adding an allowlist in the check configuration

---

### Phase 5: Security Hardening, Testing & Documentation

**Goal**: Verify the security boundary, run the full test suite, and produce the architecture documentation required for Platinum tier certification.

**Deliverables**:
- Security boundary test report (cloud VM file scan output)
- Multi-agent coordination test results (100-task sample, zero duplicates verified)
- Vault sync latency test results (24-hour window, ≥ 95% of syncs ≤ 60 s)
- Disaster recovery test results (cloud VM restart mid-task, stale recovery verified)
- End-to-end approval flow test (cloud triage → sync → local approval → execution → audit log)
- `Logs/TEST_RESULTS_<date>.json` — all test results in audit-log schema
- Architecture documentation (ASCII diagram, component descriptions, 3 key decision rationales, 3 lessons learned)
- Updated `README.md` (or `docs/PLATINUM_ARCHITECTURE.md`) — deployment guide + cloud setup
- Final passing compliance report (Phases 4 gate re-verified after hardening)

**Dependencies**:
- Phases 0–4 complete

**Acceptance Criteria**:
- Security boundary test: zero execution credentials on cloud VM; all MCP servers unreachable from cloud VM
- Multi-agent test: 100 tasks, zero duplicates, zero stranded tasks, all in `Done/` within 60 minutes
- Latency test: 24-hour window, ≥ 95% of sync cycles complete within 60 s
- Disaster recovery test: cloud VM restart, stale task returned to `Needs_Action/` within 20 minutes
- End-to-end test: email → plan → approval → execution completes within 15 minutes total
- `COMPLIANCE_REPORT_*.md` shows 15/15 PASS (or NEEDS_MANUAL_REVIEW for I and XIV with human sign-off documented)
- Architecture documentation submitted as part of deliverable package

**Risks**:
- **Test environment not matching production**: Tests run against the same vault used for production; mitigate by using a separate `AI_Employee_Vault_TEST/` for coordination and latency tests to avoid corrupting production state
- **Documentation debt**: Architecture documentation is often skipped under time pressure; mitigate by making it a hard gate in the constitution-check skill (Principle XIV)

---

## Component Design

### Cloud Orchestrator (`cloud_orchestrator.py`)

The cloud orchestrator is a lightweight subset of the local `orchestrator.py`, running on the cloud VM:

**Responsibilities**:
1. Start and watchdog: `gmail_watcher.py`, `signals_watcher.py`, `heartbeat_writer.py`, `stale_task_monitor.py`
2. Cron schedule: Sunday 22:00 → `cloud-briefing-prep` skill; daily 06:00 → `vault-health` skill; Tuesday 09:00 → social post trigger
3. Detect vault sync health: if `Sync/sync.log` shows no entry in the last 10 minutes, write `Signals/SYNC_STALLED_*.md`
4. Odoo health check every 10 minutes: GET `https://localhost/web/health` (or equivalent); on non-2xx or timeout → write `Signals/SIGNAL_odoo_down_<ts>.md`; check TLS cert expiry via `ssl.get_server_certificate` → if ≤ 14 days → write `Signals/SIGNAL_cert_expiry_<ts>.md`
5. Graceful shutdown: on `Signals/SHUTDOWN_CLOUD_*.md` → clean up in-progress tasks → exit all processes

**Activation**: `AGENT_ROLE=cloud python cloud_orchestrator.py`

### Heartbeat Writer (`watchers/heartbeat_writer.py`)

Simple daemon — no BaseWatcher inheritance needed (not a perception watcher):

```
Loop:
  write Updates/HEARTBEAT_<ISO-timestamp>.md with schema fields
  delete heartbeat files older than 15 minutes (self-cleanup)
  sleep 300 seconds
```

Heartbeat files self-expire: only the last 3 heartbeats (15 min window) are kept. Local agent checks: is the most recent heartbeat file newer than 10 minutes? If not → `Needs_Action/ERROR_CLOUD_AGENT_DOWN_*.md`.

### Stale Task Monitor (`watchers/stale_task_monitor.py`)

Runs on both machines, monitoring the OTHER agent's `In_Progress/` subdirectory:

- Cloud instance monitors `In_Progress/local/` (detects local agent crashes)
- Local instance monitors `In_Progress/cloud/` (detects cloud agent crashes)
- Check interval: every 120 seconds
- Stale threshold: configurable via `STALE_TASK_TIMEOUT_SECONDS` in `.env` (default: 600)
- On stale detection: move file back to `Needs_Action/`; write `Signals/RECOVERED_TASK_<id>_*.md`
- Idempotency: track recovered task IDs in `scripts/processed_recovered.json`

### Signals Watcher (`watchers/signals_watcher.py`)

Runs on both machines:
- Polls `AI_Employee_Vault/Signals/` every 60 seconds for new `SIGNAL_*.md` files
- Routes signals by type to appropriate handlers (log, write ERROR, trigger skill, alert human)
- Marks processed signals in `scripts/processed_signals.json`
- Does not delete signals (permanent record like Rejected/)

### Vault Sync (Syncthing)

Syncthing replaces rsync as the sync mechanism. Key configuration:

**Folder-level authority mapping**:
| Vault Folder | Local Machine | Cloud VM |
|---|---|---|
| `Dashboard.md`, `Done/`, `Approved/`, `Rejected/` | Send Only | Receive Only |
| `Updates/`, `Signals/`, `In_Progress/cloud/` | Receive Only | Send Only |
| All other folders (`Needs_Action/`, `Plans/`, etc.) | Send and Receive | Send and Receive |

**Conflict strategy**: Send-Only / Receive-Only folder modes eliminate conflicts in authoritative folders by design — the Receive-Only machine cannot modify those files. For shared folders (Needs_Action/, Plans/), Syncthing uses vector clocks; conflicts are saved as `.sync-conflict-*` files and flagged in `Signals/SYNC_CONFLICT_*.md` by the audit script.

**Audit trail** (`scripts/sync/audit-sync-log.sh`):
```bash
# Polls Syncthing REST API: GET /rest/events?since=<last_id>&types=LocalChangeDetected,RemoteChangeDetected
# For each event: append structured line to Sync/sync.log
# Runs every 60 seconds via cron on both machines
```

**.stignore** contents:
```
.env
.env.*
*.session
*_session/
cookies/
__pycache__/
scripts/processed_*.json
scripts/email_outbox_queue.json
Sync/sync.lock
.git/
```

---

## Data Flow — Platinum Task Lifecycle

### Scenario A: Cloud-Triaged Task (local machine offline)

```
Step 1: DETECTION (Cloud VM)
  New email arrives
  → gmail_watcher.py (cloud) polls Gmail API
  → Creates Needs_Action/EMAIL_<id>.md in cloud vault replica
  → Updates scripts/processed_gmail.json (cloud copy)

Step 2: CLAIM (Cloud VM)
  cloud-triage skill scans Needs_Action/
  → Moves file to In_Progress/cloud/
  → Vault sync propagates the move to local (within 60 s, but local is offline)

Step 3: PLAN (Cloud VM)
  cloud-triage skill reads Company_Handbook.md (synced copy)
  → Drafts response plan
  → Writes Plans/PLAN_<id>.md
  → Writes Signals/PLAN_READY_<id>.md (optional notification)
  → Moves task from In_Progress/cloud/ to In_Progress/local/ (signals local should proceed)

Step 4: LOCAL MACHINE COMES ONLINE
  Vault sync runs
  → Local machine receives: Plans/PLAN_*.md, In_Progress/local/<task>.md

Step 5: EXECUTION PLANNING (Local Machine)
  process-needs-action skill detects task in In_Progress/local/
  → Reads cloud-prepared plan from Plans/
  → Validates plan is executable (MCP tools available)
  → Evaluates permission boundary
  → If sensitive: writes Pending_Approval/APPROVAL_*.md
  → If auto-approved: calls execute-plan directly

Step 6: HITL / EXECUTION (same as Gold tier)
  ...

Step 7: CLOSE
  Local agent moves task to Done/
  Dashboard.md updated
  Audit log written
```

### Scenario B: Both Agents Active (concurrent operation)

```
Multiple tasks arrive in Needs_Action/
  → Cloud agent scans: claims tasks it can resolve (email triage)
    → Moves to In_Progress/cloud/
  → Local agent scans: sees cloud-claimed tasks, skips them
    → Claims remaining tasks (finance, file drops, WhatsApp)
    → Moves to In_Progress/local/
  → Both process in parallel
  → Vault sync propagates all state changes bidirectionally
  → No task processed twice (claim-by-move atomicity on each machine's filesystem)
```

---

## Security Design

### Cloud VM Credentials Boundary

| Credential Type | Cloud VM | Local Machine |
|----------------|----------|---------------|
| Gmail read-only OAuth | ✅ Present (triage only) | ✅ Present |
| Gmail send permission | ❌ Not present | ✅ Present |
| WhatsApp session | ❌ Not present | ✅ Present |
| Social API tokens (send) | ❌ Not present | ✅ Present |
| Odoo DB credentials (cloud-hosted instance) | ✅ Present (draft-only MCP; stored in `/root/.env.cloud`) | ✅ Present (full MCP; `ODOO_URL` = cloud HTTPS endpoint) |
| Odoo posting/payment credentials | ❌ Not present | ✅ Present (local `odoo-mcp` only) |
| Banking credentials | ❌ Not present | ✅ Present |
| Vault sync SSH key | ✅ Present (sync only) | ✅ Present |
| `.env` file | ❌ EXCLUDED BY RSYNC | ✅ Present |

### Security Boundary Enforcement

The boundary is enforced at three independent layers:

1. **Rsync exclusion** (`scripts/sync/.stignore`): `.env`, session directories, and credential files never transmitted from local to cloud
2. **Cloud MCP restricted to draft-only** (`ODOO_DRAFT_ONLY=true` in cloud `odoo-mcp`; `.mcp.json` on cloud VM registers only `create_invoice` and `update_expense`; no email, social, payment, or `post_invoice` tools present)
3. **Constitution check** (Principle II + III automated scan, FR-074): verifies cloud `odoo-mcp` tool registry, absence of execution credentials, and audit log entries show `post_invoice` only from `executing_agent=local`

If all three layers are intact, a full cloud VM compromise can yield Odoo draft creation capability but cannot post invoices, send emails, publish social posts, or access banking.

### Dashboard.md Single-Writer Enforcement

The cloud agent's code contains an explicit guard:

```python
PROHIBITED_CLOUD_WRITES = [
    "Dashboard.md", "Done/", "Approved/", "Rejected/"
]
# Before any vault write, check path not in PROHIBITED_CLOUD_WRITES
# If violation detected: write Signals/SINGLE_WRITER_VIOLATION_*.md instead
# Do NOT write to the prohibited path
```

---

## Architecture Decision Records (ADR) Candidates

📋 **Architectural decision detected**: **Syncthing selected for vault sync** — decision made in research phase (Phase 0). Syncthing chosen over rsync-over-SSH, rclone bisync, Git, and Unison due to: folder-level Send/Receive-Only modes eliminating conflicts by policy, sub-second latency, built-in partition buffering, and scriptable REST API for automation. Document rationale? Run `/sp.adr vault-sync-mechanism`

📋 **Architectural decision detected**: **AGENT_ROLE env var vs. separate codebases for cloud/local** — using a single codebase activated by `AGENT_ROLE=cloud|local` vs. maintaining two separate repos. Tradeoffs: shared codebase means easier updates but requires discipline about conditional imports; separate codebases are cleaner but create divergence risk. Document? Run `/sp.adr cloud-local-codebase-split`

📋 **Architectural decision detected**: **In_Progress/local/ rename from Gold's In_Progress/local_agent/** — this is a breaking change to existing Gold-tier vault state if tasks are in progress during migration. Migration strategy should be documented. Document? Run `/sp.adr in-progress-folder-rename-migration`
