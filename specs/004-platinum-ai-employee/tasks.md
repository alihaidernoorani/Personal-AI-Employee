# Tasks: Platinum Tier Personal AI Employee

**Feature**: `004-platinum-ai-employee`
**Branch**: `004-platinum-ai-employee`
**Input**: `specs/004-platinum-ai-employee/plan.md`, `spec.md`, `data-model.md`, `research.md`, `contracts/`
**Baseline**: Builds on `003-gold-ai-employee` — all Gold components unchanged unless noted.

---

## Format: `[ID] [P?] [Story] Description — file/path`

- **[P]**: Parallelisable — operates on different files with no dependency on incomplete tasks
- **[US#]**: User story association (US1–US7 from spec.md)
- Exact file paths are included in every description
- All tasks are ordered so the system remains deployable after each completed task

---

## User Story Map

| Story | Priority | Title |
|-------|----------|-------|
| US1 | P1 | 24/7 Cloud-Assisted Email Triage |
| US2 | P1 | Multi-Agent Task Coordination via Claim-by-Move |
| US3 | P1 | Bidirectional Vault Synchronisation |
| US4 | P1 | Cloud/Local Security Boundary Enforcement |
| US5 | P2 | 24/7 Social Media Drafting and Scheduled Publishing |
| US6 | P2 | 15-Principle Constitution Compliance Verification |
| US7 | P3 | Automated Cloud VM Provisioning and Configuration |
| US8 | P2 | Cloud-Hosted Odoo with Draft Accounting Actions |

---

## Phase 1: Setup

**Purpose**: Non-breaking vault structure migration and environment variable updates. Gold tier remains operational throughout. Must complete before any Platinum code is written.

**Acceptance Criteria**:
- All four new vault folders exist and are tracked by git (`.gitkeep`)
- `In_Progress/local/` exists and `In_Progress/local_agent/` is removed (only if empty)
- `.env.example` documents all Platinum env vars
- `requirements.txt` includes `paramiko>=3.4` and `schedule>=1.2.0`

- [X] T001 Create AI_Employee_Vault/Updates/, AI_Employee_Vault/Signals/, AI_Employee_Vault/In_Progress/cloud/, AI_Employee_Vault/Sync/ with .gitkeep files
- [X] T002 Migrate In_Progress: verify In_Progress/local_agent/ is empty, rename to In_Progress/local/, create In_Progress/cloud/.gitkeep — in AI_Employee_Vault/In_Progress/
- [X] T003 [P] Update .env.example to add CLOUD_VM_HOST, CLOUD_VM_USER, CLOUD_VAULT_PATH, STALE_TASK_TIMEOUT_SECONDS=600, SYNCTHING_API_KEY, AGENT_ROLE=local — in .env.example
- [X] T004 [P] Update requirements.txt to add paramiko>=3.4, schedule>=1.2.0 under existing dependencies — in requirements.txt

**Checkpoint**: Vault has all four new Platinum folders. Gold tier still runs unchanged.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure required by ALL subsequent phases. The cloud boundary guard, path migrations in existing skills, and Syncthing exclusion list must exist before any cloud-side code is written.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

**Acceptance Criteria**:
- `watchers/cloud_boundary.py` exists with `safe_vault_write()` and `PROHIBITED_CLOUD_WRITE_PATHS`
- All existing skill files reference `In_Progress/local/` not `In_Progress/local_agent/`
- `scripts/sync/.stignore` contains all exclusion patterns from vault-sync-protocol.md
- `scripts/sync/audit-sync-log.sh` is executable and documented
- `orchestrator.py` reads `AGENT_ROLE` env var

- [X] T005 Create watchers/cloud_boundary.py with PROHIBITED_CLOUD_WRITE_PATHS list and safe_vault_write(path, content) function that raises PermissionError + writes Signals/SINGLE_WRITER_VIOLATION_*.md on prohibited-path attempt — per cloud-agent-interface.md
- [X] T006 [P] Create scripts/sync/ directory with scripts/sync/.stignore containing all exclusion patterns from vault-sync-protocol.md (.env, .env.*, *.session, *_session/, cookies/, scripts/processed_*.json, scripts/email_outbox_queue.json, __pycache__/, .venv/, .git/, Sync/sync.lock)
- [X] T007 [P] Create scripts/sync/audit-sync-log.sh — polls Syncthing REST API (GET /rest/events?since=<last_id>&types=LocalChangeDetected,RemoteChangeDetected every 60s), appends pipe-delimited lines to AI_Employee_Vault/Sync/sync.log per data-model.md Sync Log Entry format, stores last event ID in scripts/sync/last_event_id
- [X] T008 Update all In_Progress/local_agent/ path references to In_Progress/local/ in .claude/skills/process-needs-action/SKILL.md and .claude/skills/execute-plan/SKILL.md
- [X] T009 [P] Update orchestrator.py to read AGENT_ROLE env var (default: "local"), add AGENT_ROLE guard at module top: if AGENT_ROLE=cloud, import cloud_orchestrator and defer startup; update all In_Progress/local_agent/ references to In_Progress/local/ in orchestrator.py

**Checkpoint**: Foundation complete. Cloud boundary guard, path references, and sync exclusion list are all in place.

---

## Phase 3: User Story 3 — Bidirectional Vault Synchronisation (Priority: P1)

**Goal**: Vault changes propagate between local and cloud VM within 60 seconds in both directions. Conflict resolution is enforced by Syncthing folder authority modes.

**Independent Test**: Write `AI_Employee_Vault/Signals/TEST_SIGNAL_001.md` on local machine, start timer, poll cloud VM via SSH for the file — verify it appears within 60 seconds. Delete from cloud VM, verify deletion propagates back to local within 60 seconds.

**Acceptance Scenarios**:
1. Cloud writes `Plans/PLAN_*.md` → local machine reads it within 60s
2. Local owner moves `APPROVAL_*.md` to `Approved/` → cloud vault replica reflects move within 60s
3. Both agents write different files to `Needs_Action/` simultaneously → both files present on both machines, no data loss
4. Network partition lasting 30+ min → changes buffered; on reconnect, all changes propagate with no files lost
5. Sync conflict on shared folder → `.sync-conflict-*` file preserved, `Signals/SYNC_CONFLICT_*.md` created

- [X] T010 [US3] Create scripts/sync/setup-syncthing.sh — get local and cloud Syncthing device IDs via REST API, add each device to the other, configure 14 folder authority modes (Send-Only/Receive-Only per vault-sync-protocol.md), deploy .stignore to vault root on both machines via SSH, trigger initial full-vault sync (local→cloud), run verification: write test file to Signals/, verify appears on cloud within SLA, verify .env NOT on cloud
- [X] T011 [P] [US3] Create AI_Employee_Vault/Sync/sync-config.md documenting: sync interval (30s), excluded paths (reference .stignore), conflict resolution rules per vault-sync-protocol.md, retry policy (3 attempts, exponential backoff); this file is maintained manually by owner (FR-027)
- [X] T012 [US3] Add sync health detection to watchers/cloud_boundary.py: add check_sync_health(vault_path, max_lag_seconds=600) function that reads last line of Sync/sync.log, computes lag, writes Signals/SYNC_STALLED_<ts>.md if lag exceeds threshold
- [X] T013 [P] [US3] Create AI_Employee_Vault/Sync/sync.log with header comment line documenting the pipe-delimited format per data-model.md Sync Log Entry schema

**Checkpoint**: Vault sync scripts are ready. After running setup-syncthing.sh on a real VM, the bidirectional sync is operational.

---

## Phase 4: User Story 2 — Multi-Agent Task Coordination (Priority: P1)

**Goal**: Both agents can claim tasks concurrently without duplication. Stale tasks are automatically recovered. Signals route correctly on both machines.

**Independent Test**: Configure both cloud and local agents to run concurrently. Drop 10 task files simultaneously into `Needs_Action/`. Verify each task processed exactly once; `Done/` contains exactly 10 completed records; no duplicates; no stranded files in any `In_Progress/` subdirectory.

**Acceptance Scenarios**:
1. Cloud agent moves task to `In_Progress/cloud/` → local agent skips it on next scan
2. Cloud agent completes → moves task to `In_Progress/local/` for local execution
3. Cloud agent crashes mid-task → stale task in `In_Progress/cloud/` returned to `Needs_Action/` within configured timeout (default 10 min)
4. Both agents attempt to claim same task simultaneously → exactly one succeeds (filesystem rename atomicity)

- [X] T014 [US2] Create watchers/heartbeat_writer.py — writes Updates/HEARTBEAT_<ISO-timestamp>.md every 300s with schema: heartbeat_id, agent_id=cloud_agent, created, tasks_in_progress (count In_Progress/cloud/), last_processed_task_ref, vault_sync_last_ok (last sync.log entry timestamp), watcher_status dict; deletes heartbeat files older than 15 minutes during each write cycle; stops if AGENT_ROLE != cloud
- [X] T015 [US2] Create watchers/stale_task_monitor.py — extends BaseWatcher; polls In_Progress/<monitored_agent>/ every 120s (cloud instance monitors In_Progress/local/, local instance monitors In_Progress/cloud/); identifies files with st_mtime age > STALE_TASK_TIMEOUT_SECONDS; moves stale files back to Needs_Action/; writes Signals/SIGNAL_task_recovered_<ts>.md per signals-protocol.md schema; tracks recovered IDs in scripts/processed_recovered.json for idempotency
- [X] T016 [US2] Create watchers/signals_watcher.py — polls AI_Employee_Vault/Signals/ every 60s for new SIGNAL_*.md files; routes each by signal_type per signals-protocol.md routing table (12 signal types); writes appropriate response (Needs_Action/ error, Dashboard.md update, log entry); marks processed signal IDs in scripts/processed_signals.json; never deletes signal files
- [X] T017 [US2] Create cloud_orchestrator.py — starts and watchdogs gmail_watcher.py, signals_watcher.py, heartbeat_writer.py, stale_task_monitor.py (monitoring In_Progress/local/); validates AGENT_ROLE=cloud at startup; fails loudly if .mcp.json exists at project root; checks disk > 20% free; implements graceful shutdown on SIGNAL_shutdown_request: stop claiming, wait 5 min for in-progress tasks, move remaining In_Progress/cloud/ tasks back to Needs_Action/, write final heartbeat with watcher_status=shutting_down, exit
- [X] T018 [US2] Update orchestrator.py to add heartbeat monitor (check_cloud_agent_health function per heartbeat-protocol.md, runs every 600s): detect ONLINE/DEGRADED/OFFLINE states from newest HEARTBEAT_*.md recency; on OFFLINE write Needs_Action/ERROR_CLOUD_AGENT_DOWN_<ts>.md + Signals/SIGNAL_cloud_down_<ts>.md; add stale_task_monitor for In_Progress/cloud/ to local startup; add signals_watcher to local startup
- [X] T019 [P] [US2] Update AI_Employee_Vault/Dashboard.md to add Cloud Agent Status section with fields per heartbeat-protocol.md: Status (ONLINE/DEGRADED/OFFLINE), Last Heartbeat, Tasks in Progress (Cloud), Vault Sync Last OK, Watcher Status, Recent Updates (last 3); add In_Progress_Local and In_Progress_Cloud counters (FR-035)

**Checkpoint**: Both agents can coordinate task ownership. Kill cloud agent → heartbeat absence detected by local within 10 min. Stale tasks auto-recover within configured timeout.

---

## Phase 5: User Story 1 — 24/7 Cloud-Assisted Email Triage (Priority: P1)

**Goal**: New emails are detected and triaged by the cloud agent while the local machine is offline. Plans are ready in vault when local machine comes online.

**Independent Test**: Suspend local machine. Send test email to monitored account with subject "[PLATINUM TEST]". Unsuspend local machine 30 minutes later. Verify `Plans/PLAN_*.md` already present (created by cloud agent), `Pending_Approval/APPROVAL_*.md` exists, and owner can approve and send reply without re-triggering triage.

**Acceptance Scenarios**:
1. Local machine offline + new email arrives → cloud creates `Needs_Action/EMAIL_*.md` within 60s + `Plans/PLAN_*.md` with draft reply
2. Cloud writes plan → vault sync propagates to local → local reads plan + writes `Pending_Approval/APPROVAL_*.md` without re-triaging
3. Owner moves `APPROVAL_*.md` to `Approved/` → reply sent via Email MCP from local only; no cloud MCP call
4. Cloud agent unavailable ≤15 min → recovers and processes queued events without data loss

- [X] T020 [US1] Update watchers/gmail_watcher.py (and gmail_api_watcher.py) to import safe_vault_write from watchers/cloud_boundary.py and use it for all vault writes; ensure AGENT_ROLE=cloud mode activates the cloud Gmail watcher as the primary email poller (creates Needs_Action/EMAIL_<id>.md, does NOT call Email MCP)
- [X] T021 [US1] Create .claude/skills/cloud-triage/SKILL.md using skill-creator skill first — cloud agent reads unclaimed Needs_Action/ task files, classifies by type (email, whatsapp, finance, signal), drafts response plan using Company_Handbook.md and Business_Goals.md, writes Plans/PLAN_<task_id>_<ts>.md (full draft with MCP action spec), writes Signals/SIGNAL_plan_ready_<task_id>_<ts>.md, moves task from In_Progress/cloud/ to In_Progress/local/; MUST use safe_vault_write() for every vault write; MUST NOT reference any MCP tool; SKILL.md frontmatter must document write boundary
- [X] T022 [US1] Update .claude/skills/ceo-briefing/SKILL.md to consume Updates/BRIEFING_DATA_<date>.md when available (read most recent file by date, include Cloud Agent Uptime + Signal Summary sections); fall back gracefully with "Cloud agent data unavailable" when no BRIEFING_DATA file present within last 7 days
- [X] T023 [P] [US1] Update .claude/skills/process-needs-action/SKILL.md to detect tasks in In_Progress/local/ that have a cloud-prepared plan (check for linked Plans/PLAN_*.md reference in task file metadata); when found, read the cloud plan instead of re-triaging, validate plan references locally available MCP tools (FR-017), write Pending_Approval/APPROVAL_*.md or call execute-plan directly per permission boundary

**Checkpoint**: End-to-end cloud triage → local approval flow is functional. Cloud prepares plan, local executes after approval, audit log shows originating_agent=cloud, executing_agent=local.

---

## Phase 6: User Story 4 — Cloud/Local Security Boundary (Priority: P1)

**Goal**: Cloud VM holds zero execution credentials. Boundary is enforced at three independent layers: Syncthing mode, code guard, and constitution check. A full cloud VM compromise cannot yield execution credentials.

**Independent Test**: SSH to cloud VM. Run: `ls ~/.env 2>&1` (expect "no such file"). Run: `ls /root/AI_Employee_Vault/.env 2>&1` (expect "no such file"). Trigger full email + social workflow; `ps aux` on cloud VM — confirm no MCP server processes. Confirm all audit log entries show executing_agent=local.

**Acceptance Scenarios**:
1. Cloud VM inspected → no .env, API keys, session cookies, or execution credentials present
2. Cloud agent generates plan requiring email send → writes Plans/PLAN_*.md + Pending_Approval/APPROVAL_*.md only; does NOT call Email MCP
3. Simulated cloud VM breach → no MCP server reachable; no credentials available
4. Sync config inspected → .env, credential files, browser session dirs are on .stignore, never transmitted

- [X] T024 [US4] Add safe_vault_write() import and usage to watchers/heartbeat_writer.py, watchers/stale_task_monitor.py, watchers/signals_watcher.py — replace all direct Path.write_text() calls with safe_vault_write() calls; verify no file writes bypass the boundary guard
- [X] T025 [P] [US4] Add cloud VM startup validation to cloud_orchestrator.py: (1) assert AGENT_ROLE == "cloud" else sys.exit(1) with clear error; (2) if .mcp.json exists, parse its tool list and assert only {"create_invoice", "update_expense"} are registered — if any execution tool (post_invoice, send_email, post_twitter, etc.) is found, write Signals/SIGNAL_single_writer_violation_<ts>.md and sys.exit(1); (3) verify no email/social MCP server processes via psutil.process_iter() on startup; (4) verify ODOO_DRAFT_ONLY env var is set to "true"
- [X] T026 [P] [US4] Create scripts/sync/security-boundary-test.sh — SSH to cloud VM and verify: no .env file exists anywhere under /root/; no *.token or credential JSON files; no MCP server processes running; no .mcp.json present; outputs PASS/FAIL per check to stdout; designed to be called from CI or provision-cloud.sh post-setup verification
- [X] T027 [US4] Add cloud credential audit to .claude/skills/constitution-check/SKILL.md (Phase 8 dependency — add this item to the constitution-check task scope): Principle II check invokes security-boundary-test.sh via subprocess and parses PASS/FAIL output; Principle III check verifies cloud .mcp.json registers only {create_invoice, update_expense} and greps cloud skills/watchers to confirm no email/social/post_invoice tool calls; FR-074 checks run as part of constitution-check (Odoo HTTPS response, backup recency, post_invoice audit log entries show executing_agent=local only)

**Checkpoint**: Security boundary verified at code level. Running security-boundary-test.sh on cloud VM returns all PASS. Cloud orchestrator refuses to start if .mcp.json is present.

---

## Phase 7: User Story 5 — 24/7 Social Media Drafting (Priority: P2)

**Goal**: Cloud agent drafts scheduled social posts, syncs approvals to local, local agent publishes via Social MCP. Stale drafts (>48 hr unapproved) trigger alerts without auto-publishing.

**Independent Test**: Configure recurring social post trigger in cloud_orchestrator.py cron (or manually create Needs_Action/SOCIAL_POST_TRIGGER_*.md). Verify cloud agent creates `Plans/PLAN_*_social.md` and `Pending_Approval/APPROVAL_*_social.md`. Move approval to Approved/ on local. Verify local agent publishes via Social MCP and logs result. Verify no platform API called from cloud VM.

**Acceptance Scenarios**:
1. Social post scheduled on cloud → cloud writes draft to Plans/ + approval to Pending_Approval/; no Social MCP call from cloud
2. Approval moved to Approved/ on local → local agent publishes via Social MCP + logs result
3. Approval pending > 48 hr → cloud writes Signals/SIGNAL_stale_draft_<ts>.md; no auto-publish occurs

- [X] T028 [US5] Create .claude/skills/cloud-briefing-prep/SKILL.md using skill-creator skill first — reads: Signals/ (last 7 days, grouped by signal_type and severity), Logs/ (social post audit entries for platforms + engagement counts), Updates/VAULT_HEALTH_*.md (most recent), Updates/HEARTBEAT_*.md (uptime calculation from gap analysis); writes Updates/BRIEFING_DATA_<YYYY-MM-DD>.md with all fields per data-model.md Briefing Data schema; must use safe_vault_write() for all writes; scheduled by cloud_orchestrator.py at Sunday 22:00
- [X] T029 [US5] Add social post drafting logic to .claude/skills/cloud-triage/SKILL.md: detect SOCIAL_POST_TRIGGER_*.md task type in Needs_Action/; draft post content using Business_Goals.md OKRs + Company_Handbook.md tone guidelines; write Plans/PLAN_<id>_social.md with draft content + platform + optimal time; write Pending_Approval/APPROVAL_<id>_social.md; add stale draft check — if Pending_Approval/ contains APPROVAL_*_social.md older than 48 hr, write Signals/SIGNAL_stale_draft_<ts>.md (routes to Needs_Action/ if requires_human_action=true)
- [X] T030 [P] [US5] Update cloud_orchestrator.py cron schedule: add Tuesday 09:00 UTC → create Needs_Action/SOCIAL_POST_TRIGGER_linkedin_<ts>.md (weekly LinkedIn post trigger); Sunday 22:00 UTC → invoke cloud-briefing-prep skill; daily 06:00 UTC → invoke vault-health skill — use schedule library (already in requirements.txt)

**Checkpoint**: Cloud schedules social drafts, local publishes only after approval. No social API credentials on cloud VM.

---

## Phase 8: User Story 6 — 15-Principle Constitution Compliance (Priority: P2)

**Goal**: The constitution-check skill verifies all 15 principles. Pre-existing code quality violations must be resolved first (odoo-mcp, social-mcp, gmail_api_watcher exceed 300-line limit). A passing compliance report gates Platinum tier sign-off.

**Independent Test**: Deploy system. Run constitution-check skill. Verify report covers all 15 principles with PASS/FAIL/NEEDS_MANUAL_REVIEW status. Intentionally write a mock credential to a vault .md file. Re-run. Verify Principle II/XIII show FAIL with specific file path. Fix violation. Re-run. Verify 15/15 PASS or NEEDS_MANUAL_REVIEW.

**Acceptance Scenarios**:
1. constitution-check runs → compliance report covers all 15 principles with status per principle
2. Any principle FAIL → report includes specific violation + remediation description
3. All 15 PASS → report written to Briefings/COMPLIANCE_REPORT_<date>.md + summary in next CEO briefing
4. Principle cannot be automated → marked NEEDS_MANUAL_REVIEW with human verification checklist

### Pre-existing Code Quality Fixes (must complete before constitution-check can PASS)

- [X] T031 [US6] Split mcp-servers/odoo-mcp/server.py (636 lines, violates Principle XV) into: server.py (entry point, ≤100 lines), mcp-servers/odoo-mcp/handlers/invoice_handlers.py, mcp-servers/odoo-mcp/handlers/customer_handlers.py, mcp-servers/odoo-mcp/handlers/transaction_handlers.py — maintain identical MCP tool interface, no behavior change
- [X] T032 [P] [US6] Split mcp-servers/social-mcp/server.py (515 lines, violates Principle XV) into: server.py (entry point, ≤100 lines), mcp-servers/social-mcp/handlers/facebook_handler.py, mcp-servers/social-mcp/handlers/linkedin_handler.py, mcp-servers/social-mcp/handlers/instagram_handler.py, mcp-servers/social-mcp/handlers/twitter_handler.py — maintain identical MCP tool interface
- [X] T033 [P] [US6] Split watchers/gmail_api_watcher.py (322 lines, violates Principle XV) into: gmail_api_watcher.py (main watcher loop, ≤250 lines), watchers/gmail_api_auth.py (OAuth token refresh logic, ≤80 lines) — no behavior change

### Compliance Skills

- [X] T034 [US6] Create .claude/skills/vault-health/SKILL.md using skill-creator skill first — validate all vault folders from data-model.md Folder Authority Matrix exist; count files in In_Progress/cloud/ and In_Progress/local/ as stale_tasks_detected; read last line of Sync/sync.log and compute sync_lag_seconds; set health_status (healthy: lag<120s, degraded: lag<600s, critical: lag≥600s or missing folders); write Updates/VAULT_HEALTH_<ts>.md per data-model.md schema; runs on both agents (AGENT_ROLE-aware path resolution)
- [X] T035 [US6] Create .claude/skills/constitution-check/SKILL.md using skill-creator skill first — implement all 15 principle checks per research.md Automation Matrix (7 automated YES, 7 PARTIAL, 1 NEEDS_MANUAL_REVIEW); for each FAIL write finding with specific file path + remediation; for PASS write "—"; write Briefings/COMPLIANCE_REPORT_<date>.md per spec.md Compliance Report Schema; if any FAIL create Needs_Action/COMPLIANCE_FAIL_<date>.md; update Dashboard.md compliance section with overall status + check date + report link
- [X] T036 [P] [US6] Add Compliance Report section to AI_Employee_Vault/Dashboard.md: fields — Compliance Status (PASS/FAIL/PARTIAL/NOT_RUN), Last Check Date, Report Link (relative path to Briefings/COMPLIANCE_REPORT_*.md), Principles Pass/Fail/Manual count — written exclusively by local agent (Single Writer Rule)

**Checkpoint**: All 15 principles verified. Constitution-check produces a passing compliance report. `Briefings/COMPLIANCE_REPORT_<date>.md` exists with all 15 principles at PASS or NEEDS_MANUAL_REVIEW.

---

## Phase 9: User Story 7 — Automated Cloud VM Provisioning (Priority: P3)

**Goal**: A fresh Hetzner CX22 VM is fully operational as a cloud agent within 30 minutes of running a single provisioning script. No manual SSH commands required beyond initial credential input.

**Independent Test**: Provision a fresh cloud VM using only `scripts/provision-cloud.sh` and the quickstart guide. Verify cloud agent processes tasks and heartbeats appear in `Updates/` within 30 minutes of running the script. Verify provisioning smoke test passes.

**Acceptance Scenarios**:
1. Fresh cloud VM + provisioning script → all software installed, vault sync configured, cloud watchers started without manual intervention
2. Cloud agent running → heartbeat in Updates/ within 5 min; watcher_status all running
3. Cloud VM reprovisioned → reconnects to vault sync, recovers current vault state from local, no data loss or duplication

- [X] T037 [US7] Create scripts/provision-cloud.sh — idempotent Bash script targeting Ubuntu 24.04 LTS; steps: (1) install Python 3.13 via deadsnakes PPA, pip, git, rsync, curl, jq; (2) install Syncthing via official package repo; (3) git clone or rsync project codebase to /root/; (4) create Python venv at /root/.venv + pip install -r requirements.txt; (5) mkdir -p for all vault folders; (6) write /root/.env.cloud with AGENT_ROLE=cloud, VAULT_PATH, STALE_TASK_TIMEOUT_SECONDS=600; (7) install systemd service files (Step T038); (8) systemctl enable + start cloud-agent and syncthing; (9) run smoke test: create Needs_Action/PROVISION_SMOKE_TEST_<ts>.md, wait up to 2 min for cloud agent to claim it (In_Progress/cloud/), verify; (10) run scripts/sync/security-boundary-test.sh and fail if any check fails
- [X] T038 [P] [US7] Create scripts/systemd/cloud-agent.service and scripts/systemd/syncthing-cloud.service systemd unit files — cloud-agent.service: ExecStart=/root/.venv/bin/python /root/cloud_orchestrator.py, Restart=always, RestartSec=10, EnvironmentFile=/root/.env.cloud; syncthing-cloud.service: delegates to syncthing -home /root/.config/syncthing, Restart=always
- [X] T039 [P] [US7] Add startup health check to cloud_orchestrator.py startup sequence: verify NTP sync active (timedatectl show | grep NTPSynchronized=yes), verify disk usage < 80% (shutil.disk_usage), verify Syncthing daemon responsive (GET http://127.0.0.1:8384/rest/system/ping), write Signals/SIGNAL_startup_health_<ts>.md with severity=info (all pass) or severity=warning (any fail)
- [X] T040 [P] [US7] Update specs/004-platinum-ai-employee/quickstart.md to add Troubleshooting section: common failure patterns (cloud agent OFFLINE, vault sync stalled, .env leaked to cloud VM, stale task not recovered, constitution check failing on file-size), check commands per failure, fix commands per failure — replacing placeholder Steps 1–6 with exact commands verified against T037 implementation

**Checkpoint**: Provisioning script produces a working cloud agent on a fresh VM in under 30 minutes. No manual steps required beyond running the script.

---

## Phase 9b: User Story 8 — Cloud-Hosted Odoo with Draft Accounting Actions (Priority: P2)

**Goal**: Odoo Community runs 24/7 on the cloud VM behind HTTPS with automated backups. The cloud agent creates draft invoices and expenses via a draft-only `odoo-mcp` instance. The local agent posts invoices via its full-permission `odoo-mcp` over HTTPS. Health checks and cert expiry alerts are wired into the cloud orchestrator.

**Independent Test**: Drop `Needs_Action/ODOO_DRAFT_invoice_test.md` on cloud VM. Verify cloud agent creates a draft invoice in Odoo (cloud `odoo-mcp` call) and writes `Pending_Approval/APPROVAL_*_odoo.md` within 5 minutes. Approve on local machine. Verify local agent calls `post_invoice` on cloud Odoo and audit log shows `executing_agent=local`. Verify `https://<CLOUD_VM_HOST>/` returns 200 with valid TLS. Verify `/opt/odoo-backups/` contains a file dated today.

**Acceptance Scenarios**:
1. Cloud triage receives ODOO_DRAFT task → creates draft invoice in cloud Odoo → writes approval; no `post_invoice` from cloud
2. Owner approves → local agent posts invoice via local `odoo-mcp` over HTTPS → audit log entry `executing_agent=local`
3. Odoo HTTPS endpoint serves valid TLS; HTTP redirects to HTTPS; backup files exist with 7-day retention
4. Odoo service down → `SIGNAL_odoo_down_*.md` written; ODOO_DRAFT tasks skipped until recovery
5. Backup fails → `SIGNAL_backup_failed_*.md` written with `requires_human_action=true`

- [X] T048 [US8] Create scripts/odoo/docker-compose.yml deploying Odoo Community (odoo:17 or later) + PostgreSQL (postgres:15) on cloud VM: Odoo on port 8069 (loopback only), PostgreSQL on port 5432 (loopback only), persistent volumes for odoo-data and pg-data under /var/lib/odoo-docker/; health check: `curl -f http://localhost:8069/web/health`; document ODOO_DB, ODOO_USER, ODOO_PASSWORD env vars (stored in /root/.env.cloud, not in compose file)
- [X] T049 [US8] Create scripts/odoo/nginx.conf — nginx HTTPS reverse proxy: listen 443 ssl; ssl_certificate /etc/letsencrypt/live/<domain>/fullchain.pem; ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem; proxy_pass http://localhost:8069; include /etc/letsencrypt/options-ssl-nginx.conf; server block on port 80 returning 301 redirect to https://; document certbot install command (certbot --nginx -d <domain>) in scripts/odoo/README.md
- [X] T050 [P] [US8] Create scripts/odoo/backup-odoo.sh — bash script: (1) pg_dump --format=custom ODOO_DB > /opt/odoo-backups/odoo_$(date +%Y%m%d_%H%M%S).dump; (2) delete files older than 7 days via find /opt/odoo-backups -mtime +7 -delete; (3) on failure (exit code ≠ 0) write AI_Employee_Vault/Signals/SIGNAL_backup_failed_$(date +%s).md with severity=warning, requires_human_action=true; (4) install as daily cron in provision-cloud.sh: "5 0 * * * root /root/scripts/odoo/backup-odoo.sh >> /var/log/odoo-backup.log 2>&1"
- [X] T051 [P] [US8] Add ODOO_DRAFT_ONLY mode to mcp-servers/odoo-mcp/server.py: read env var ODOO_DRAFT_ONLY (default "false"); when "true", register only create_invoice and update_expense tools in the MCP server's tool list (other handlers exist in code but are not registered); add ODOO_DRAFT_ONLY=true to cloud VM env in provision-cloud.sh; add ODOO_URL=https://<CLOUD_VM_HOST>/jsonrpc and ODOO_DRAFT_ONLY=false to local .env.example
- [X] T052 [US8] Add Odoo health check to cloud_orchestrator.py: health_check_odoo() function runs every 600 s; (1) HTTP GET https://localhost/web/health with 10 s timeout — on non-2xx or timeout write Signals/SIGNAL_odoo_down_<ts>.md severity=warning, set ODOO_AVAILABLE=False flag, skip ODOO_DRAFT tasks; (2) check TLS cert expiry using ssl.get_server_certificate + ssl.DER_cert_to_PEM_cert + datetime comparison — if ≤ 14 days write Signals/SIGNAL_cert_expiry_<ts>.md severity=warning; if already expired severity=critical, set ODOO_AVAILABLE=False; (3) on recovery (2xx response) write Signals/SIGNAL_odoo_recovered_<ts>.md severity=info, set ODOO_AVAILABLE=True
- [X] T053 [US8] Update .claude/skills/cloud-triage/SKILL.md to handle ODOO_DRAFT_*.md task type: detect task files with type=odoo_draft; if ODOO_AVAILABLE flag is False (detected via Signals/ — last SIGNAL_odoo_down is more recent than last SIGNAL_odoo_recovered), skip task and leave in In_Progress/cloud/ with a stale timeout warning; if ODOO_AVAILABLE is True, call cloud-side odoo-mcp create_invoice or update_expense (draft); write Plans/PLAN_<id>_odoo.md with the draft record ID and amount; write Pending_Approval/APPROVAL_<id>_odoo.md; move task to In_Progress/local/
- [X] T054 [P] [US8] Update scripts/provision-cloud.sh to add Odoo deployment steps after Python env setup: (1) install docker + docker-compose-plugin via apt; (2) mkdir -p /opt/odoo-backups; (3) copy scripts/odoo/docker-compose.yml to /root/odoo/docker-compose.yml; (4) docker compose -f /root/odoo/docker-compose.yml up -d; (5) wait for health check (max 2 min); (6) install certbot + certbot-nginx; (7) copy scripts/odoo/nginx.conf to /etc/nginx/sites-available/odoo; (8) install backup cron; (9) run smoke test: verify https://localhost returns 2xx; verify backup-odoo.sh exits 0; verify cloud odoo-mcp create_invoice (draft) succeeds

**Checkpoint**: Cloud Odoo Community running behind HTTPS with daily backups. Cloud `odoo-mcp` creates draft invoices. Local `odoo-mcp` posts invoices. Health checks and cert alerts operational. `constitution-check` passes FR-074 checks.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation testing, documentation, and final compliance gate. All test results written to `Logs/` using audit log schema per FR-067.

- [ ] T041 [P] Run multi-agent coordination test per FR-060: drop 100 task files into Needs_Action/ with both agents active; verify each processed exactly once; Done/ contains exactly 100 records; no duplicates; no stranded files; write results to Logs/TEST_RESULTS_<date>.json under test_name=multi_agent_coordination
- [ ] T042 [P] Run vault sync latency test per FR-061: measure propagation time for 50 synthetic writes (25 local→cloud, 25 cloud→local) over 24-hour window; verify ≥ 95% complete within 60s; write results to Logs/TEST_RESULTS_<date>.json under test_name=vault_sync_latency
- [ ] T043 [P] Run security boundary test per FR-062: execute scripts/sync/security-boundary-test.sh against cloud VM; verify zero execution credentials, no MCP processes, no .mcp.json, no .env; write PASS/FAIL per check to Logs/TEST_RESULTS_<date>.json under test_name=security_boundary
- [ ] T044 [P] Run disaster recovery test per FR-065: simulate cloud VM restart mid-task (kill cloud_orchestrator.py while task in In_Progress/cloud/); wait configured stale-task timeout + 1 sync cycle; verify task returned to Needs_Action/; verify Signals/SIGNAL_task_recovered_*.md written; write results to Logs/TEST_RESULTS_<date>.json under test_name=disaster_recovery
- [ ] T045 Run end-to-end approval flow test per FR-064: send test email → cloud triage writes plan (≤5 min) → sync propagates (≤60s) → local writes approval → owner approves → execute-plan sends email via Email MCP → audit log entry with originating_agent=cloud, executing_agent=local, result=success; verify total elapsed time ≤ 15 min; write results to Logs/TEST_RESULTS_<date>.json under test_name=end_to_end_approval
- [ ] T046 [P] Update README.md with Platinum Architecture section: ASCII diagram (copy from plan.md architecture diagram), cloud/local responsibility table, 3 key architectural decisions (Syncthing, AGENT_ROLE env var, claim-by-move), 3 lessons learned from implementation, monthly cost reference (Hetzner CX22 ~€3.79/month), pointer to quickstart.md for setup steps
- [ ] T047 Run final constitution-check skill: verify report shows 15/15 PASS or NEEDS_MANUAL_REVIEW (zero FAIL); document manual review items for Principles I (Production First) and XIV (Documentation) with human sign-off checklist; link compliance report from Dashboard.md; confirm Briefings/COMPLIANCE_REPORT_<date>.md exists and is complete

**Checkpoint**: All acceptance criteria from spec.md SC-001 through SC-012 verified. Platinum tier is production-ready.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US3)**: Depends on Phase 2 — requires sync scripts foundation
- **Phase 4 (US2)**: Depends on Phase 2 — requires cloud_boundary.py and orchestrator updates
- **Phase 5 (US1)**: Depends on Phase 2, Phase 3, Phase 4 — requires sync operational + coordination layer
- **Phase 6 (US4)**: Depends on Phase 4, Phase 5 — security guard must cover all cloud-side code
- **Phase 7 (US5)**: Depends on Phase 5, Phase 6 — cloud triage must exist, security boundary verified
- **Phase 8 (US6)**: Depends on Phases 0–7 — constitution-check has something to check
- **Phase 9 (US7)**: Can begin in parallel with Phase 6 — provisioning script is independent of skills
- **Phase 9b (US8)**: Depends on Phase 9 — Odoo deployment is added to the provisioning script; T051 (ODOO_DRAFT_ONLY mode) must complete before Phase 8 constitution-check can pass FR-074
- **Phase 10 (Polish)**: Depends on all phases — validates the complete system

### User Story Dependencies

| User Story | Blocked By | Can Parallel With |
|---|---|---|
| US3 (Vault Sync) | Phase 2 | US2 (Phase 4) |
| US2 (Coordination) | Phase 2 | US3 (Phase 3) |
| US1 (Email Triage) | Phase 3, Phase 4 | — |
| US4 (Security) | Phase 4, Phase 5 | US5 (Phase 7) start |
| US5 (Social) | Phase 5, Phase 6 | US6 setup tasks |
| US6 (Compliance) | All previous incl. T051 | US7 (Phase 9) |
| US7 (Provisioning) | Phase 2 | Phase 6–8 |
| US8 (Cloud Odoo) | Phase 9 (T037–T040) | Phase 8 (T051 feeds constitution-check) |

### Within Each Phase

- Tasks marked [P] within a phase can run in parallel
- Tasks without [P] must complete in the listed order
- Skills must be created with `skill-creator` skill before any implementation in SKILL.md

---

## Parallel Execution Examples

### Phase 2 Parallel Batch

```
Parallel (all operate on different files):
  T006 — scripts/sync/.stignore
  T007 — scripts/sync/audit-sync-log.sh
  T009 — orchestrator.py (AGENT_ROLE + path refs)
Sequential:
  T005 — watchers/cloud_boundary.py  [complete first — others import from it]
  T008 — skill SKILL.md path updates  [after T005 confirms guard interface]
```

### Phase 4 Parallel Batch

```
Sequential dependencies:
  T005 (cloud_boundary.py) must be complete
  T014 → T015 → T016 [implement in order — each imports prior module]
  T017 (orchestrator.py update) [after T014-T016 exist]
Parallel:
  T019 (Dashboard.md schema update) [independent of code changes]
```

### Phase 8 Parallel Batch

```
Parallel (all on different files):
  T031 — odoo-mcp split
  T032 — social-mcp split
  T033 — gmail_api_watcher split
Then parallel (skills are independent):
  T034 — vault-health/SKILL.md
  T035 — constitution-check/SKILL.md
  T036 — Dashboard.md compliance section
```

---

## Implementation Strategy

### MVP First (US3 + US2 + US1 = Core P1 Stories)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T009)
3. Complete Phase 3: US3 Vault Sync (T010–T013)
4. **VALIDATE**: Run setup-syncthing.sh on real VMs; verify bidirectional sync
5. Complete Phase 4: US2 Coordination (T014–T019)
6. **VALIDATE**: Multi-agent test — 10 tasks, zero duplicates
7. Complete Phase 5: US1 Email Triage (T020–T023)
8. **VALIDATE**: End-to-end cloud email triage test
9. **STOP and DEMO** — Platinum defining capability delivered

### Incremental Delivery

- P1 delivered → US1+US2+US3+US4 complete → stable Platinum base
- P2 delivered → US5+US6 → social automation + compliance gate
- P3 delivered → US7 → automated provisioning for disaster recovery

---

## Notes

- **skill-creator first**: Every new skill (T021, T028, T034, T035) MUST be created with `skill-creator` skill before writing SKILL.md content directly
- **AGENT_ROLE guard**: Every cloud-side file must check AGENT_ROLE=cloud before activating; cloud-specific code must never run on local machine
- **safe_vault_write everywhere**: All vault writes in cloud-side code (cloud orchestrator, cloud watchers, cloud skills) must use `safe_vault_write()` from `watchers/cloud_boundary.py`
- **Commit format**: `feat(platinum): …` following Gold tier pattern
- **Test vault**: Use `AI_Employee_Vault_TEST/` for coordination and latency tests to avoid corrupting production vault state (per plan.md Phase 5 risk mitigation)
- **Single-writer rule**: Dashboard.md updated only in T019 (schema) and by local orchestrator at runtime — never by cloud code
- **Code size limit**: All new files must be ≤ 300 lines (Principle XV); cloud_orchestrator.py expected ~280 lines; split if larger
