# Tasks: Silver Tier Functional Assistant

**Feature**: `002-silver-ai-employee` | **Branch**: `002-silver-ai-employee`
**Input**: `specs/002-silver-ai-employee/plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`
**Scope**: 20–30 hours | **Total tasks**: 30

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US1/2/3/4]**: Maps to user story in spec.md
- Sub-bullets provide description, expected outcome, dependencies, and implementation notes

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Install dependencies, extend `.env`, scaffold new directories. No user story work until this is done.

- [X] T001 Update `requirements.txt` with `playwright>=1.40.0` and `mcp>=1.0.0`
  - **Description**: Add two new lines to `requirements.txt`. Existing deps (`watchdog`, `python-dotenv`) stay unchanged.
  - **Expected outcome**: `pip install -r requirements.txt` succeeds with no errors; `python -c "import playwright; import mcp"` exits 0.
  - **Dependencies**: None
  - **Notes**: Use `playwright>=1.40.0` and `mcp>=1.0.0` exactly as specified in research.md R-002 and R-004.

- [X] T002 [P] Update `.env.example` with Gmail and dry-run variables
  - **Description**: Add `GMAIL_EMAIL=`, `GMAIL_APP_PASSWORD=`, and ensure `DRY_RUN=true` is present. Do not touch existing vars.
  - **Expected outcome**: `.env.example` contains all Silver Tier required keys; no secrets are committed.
  - **Dependencies**: None
  - **Notes**: See research.md R-001. App Password is a 16-char string from Google Account → Security → 2FA → App passwords.

- [X] T003 [P] Create `mcp-servers/email-mcp/` directory with placeholder files
  - **Description**: Create `mcp-servers/email-mcp/__init__.py`, `mcp-servers/email-mcp/server.py` (stub), `mcp-servers/email-mcp/smtp_imap.py` (stub). Confirm directory structure matches plan.md.
  - **Expected outcome**: `ls mcp-servers/email-mcp/` shows `__init__.py`, `server.py`, `smtp_imap.py`.
  - **Dependencies**: None

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Vault folders, idempotency registries, and `Business_Goals.md` must exist before any watcher or skill can run. **All user story phases block on this.**

- [X] T004 Create new vault folders: `Pending_Approval/`, `Approved/`, `Rejected/`
  - **Description**: Create the three new vault subdirectories inside `AI_Employee_Vault/`. Each must contain a `.gitkeep` so the folder is tracked by git. Update `Dashboard.md` header to add a `## Pending Approvals` section placeholder (`_count: 0_`).
  - **Expected outcome**: `ls AI_Employee_Vault/` shows `Pending_Approval/`, `Approved/`, `Rejected/`. Dashboard.md has the new section.
  - **Dependencies**: None

- [X] T005 [P] Create idempotency registry files for Silver Tier watchers
  - **Description**: Create three new JSON registry files: `scripts/processed_gmail.json` (`{"processed": []}`), `scripts/processed_whatsapp.json` (`{"processed": []}`), `scripts/processed_approvals.json` (`{"processed": []}`). Mirror the pattern of the existing `scripts/processed_inbox.json`.
  - **Expected outcome**: All three files exist and are valid JSON; `python -c "import json; json.load(open('scripts/processed_gmail.json'))"` exits 0.
  - **Dependencies**: None

- [X] T006 [P] Create `AI_Employee_Vault/Business_Goals.md` with service and LinkedIn topic scaffolding
  - **Description**: Write `Business_Goals.md` with three sections: `## Services Offered` (list 3 placeholder services), `## OKRs / Revenue Targets` (monthly revenue goal placeholder), `## LinkedIn Post Topics` (list 5 topic prompts). This file is read by the `linkedin-post` skill.
  - **Expected outcome**: File exists at `AI_Employee_Vault/Business_Goals.md` and is readable; content has all three sections.
  - **Dependencies**: None
  - **Notes**: Placeholder values are fine. The owner will fill real data before going live.

**Checkpoint**: All Phase 2 tasks complete → user story implementation can begin.

---

## Phase 3: User Story 1 — Multi-Channel Event Capture (Priority: P1) 🎯 MVP

**Goal**: Gmail watcher and WhatsApp watcher both produce structured task files in `Needs_Action/` automatically.

**Independent Test**: Send a test email to the monitored Gmail inbox. Within 5 minutes, `Needs_Action/EMAIL_*.md` appears with valid YAML frontmatter (`type: email, source: gmail, sender, subject, body_snippet, imap_uid, received, priority, status`). Send a WhatsApp message; within 60 seconds, `Needs_Action/WA_*.md` appears with `type: whatsapp` frontmatter.

- [X] T007 [US1] Implement `GmailWatcher` in `watchers/gmail_watcher.py`
  - **Description**: Extend `BaseWatcher`. In `check_for_updates()`: open `imaplib.IMAP4_SSL("imap.gmail.com")`, login with `GMAIL_EMAIL`/`GMAIL_APP_PASSWORD` from env, `SELECT INBOX`, `SEARCH UNSEEN`, fetch `RFC822.HEADER` for each UID, parse sender/subject with `email.message_from_bytes()`. Call `create_action_file(item)` per message. Load/save UID registry to `scripts/processed_gmail.json`. Mark message as read after processing. Use `PollingObserver(timeout=300)` (5-min poll).
  - **Expected outcome**: Running `python -c "from watchers.gmail_watcher import GmailWatcher"` exits 0. On manual trigger, a new UNSEEN email becomes `Needs_Action/EMAIL_<ts>_<slug>.md` with correct YAML.
  - **Dependencies**: T001, T005
  - **Notes**: Frontmatter fields per `contracts/task-file-schema.md` type `email`. Do NOT fetch full body (`RFC822.HEADER` only to stay fast). Store `imap_uid` as string. Wrap `check_for_updates()` body in `try/except`; on non-fatal exception write `Needs_Action/ERROR_<ts>_gmail_watcher.md` and continue loop (FR-005).

- [X] T008 [P] [US1] Implement `WhatsAppWatcher` in `watchers/whatsapp_watcher.py`
  - **Description**: Extend `BaseWatcher`. In `check_for_updates()`: use `sync_playwright()` with `persistent_context("whatsapp_session/")` → navigate `https://web.whatsapp.com` → take accessibility snapshot → find unread chat badges → extract sender + message text. Hash each message (`hashlib.sha256(sender+text+timestamp)`) for idempotency registry in `scripts/processed_whatsapp.json`. Write `Needs_Action/WA_<ts>_<sender-slug>.md` per new message. Poll every 60 seconds.
  - **Expected outcome**: First run opens WhatsApp Web (QR code scan); subsequent runs detect new messages. A new WhatsApp message creates `Needs_Action/WA_*.md` within 60s.
  - **Dependencies**: T001, T005
  - **Notes**: See research.md R-002. Use accessibility snapshot (`page.accessibility.snapshot()`), not CSS selectors. Session persists after first QR scan in `whatsapp_session/` (gitignored). Watcher runs as a **persistent daemon** with internal 60s sleep loop — NOT a one-shot script. Wrap `check_for_updates()` in `try/except`; on non-fatal exception write `Needs_Action/ERROR_<ts>_whatsapp_watcher.md` and continue loop (FR-005).

- [X] T009 [US1] Install Playwright Chromium browser and create `whatsapp_session/` gitignore entry
  - **Description**: Run `.venv/bin/playwright install chromium`. Add `whatsapp_session/` to `.gitignore`. Verify `python -c "from playwright.sync_api import sync_playwright; print('ok')"` exits 0.
  - **Expected outcome**: Playwright can launch Chromium; `whatsapp_session/` is gitignored.
  - **Dependencies**: T001

- [X] T010 [US1] Add `--watcher` and `--cron` flags to `orchestrator.py`
  - **Description**: Add two `argparse` arguments: (1) `--watcher filesystem | gmail | whatsapp | approval | all` — selects which watcher(s) to start; (2) `--cron` boolean flag — when present, writes a `actor: scheduler` NDJSON entry to `Logs/YYYY-MM-DD.json` before starting watchers. Default run (no flags): starts `FilesystemWatcher` + `ApprovalWatcher` + `WhatsAppWatcher` as persistent daemons. `--watcher gmail --cron`: used by crontab for scheduled Gmail checks.
  - **Expected outcome**: `python orchestrator.py --watcher gmail --cron` starts Gmail watcher and logs `actor: scheduler`. `python orchestrator.py --watcher gmail` (no `--cron`) starts Gmail watcher with no scheduler log entry. `python orchestrator.py --help` shows both flags.
  - **Dependencies**: T007, T008

- [X] T011 [US1] Validate US1 end-to-end: email and WhatsApp task file creation
  - **Description**: Manual validation checklist. (1) Start `python orchestrator.py --watcher gmail`. Send a test email. Confirm `Needs_Action/EMAIL_*.md` appears within 5 min with correct YAML. (2) Start `python orchestrator.py --watcher whatsapp`. Scan QR. Send a WhatsApp message. Confirm `WA_*.md` appears within 60s. (3) Restart gmail watcher; confirm no duplicate task created for same email (idempotency). Record pass/fail in `AI_Employee_Vault/Logs/YYYY-MM-DD.json`.
  - **Expected outcome**: SC-001, SC-002, SC-004 from spec.md all pass.
  - **Dependencies**: T007, T008, T009, T010

**Checkpoint**: US1 complete and independently validated. Gmail and WhatsApp capture working.

---

## Phase 4: User Story 2 — Structured Plans with Approval Gates (Priority: P2)

**Goal**: `process-needs-action` skill handles email and WhatsApp tasks, writes approval files to `Pending_Approval/`. `email-mcp` MCP server sends approved emails. Full approval pipeline (ApprovalWatcher → execute-plan) operational.

**Independent Test**: Place `Needs_Action/EMAIL_test.md` (type: email). Invoke `process-needs-action`. Confirm `Plans/PLAN_*.md` and `Pending_Approval/APPROVAL_*.md` exist. Move APPROVAL_*.md to `Approved/`. Within 5s, `Needs_Action/ACTION_*.md` appears. Invoke `execute-plan`. Confirm email is sent (DRY_RUN=true → log entry) or delivered (DRY_RUN=false).

- [X] T012 [US2] Use `skill-creator` to update `process-needs-action` SKILL.md for `email` and `whatsapp` task types
  - **Description**: Invoke the `skill-creator` skill (per CLAUDE.md rule) and update `.claude/skills/process-needs-action/SKILL.md` to handle two new task types. For `type: email`: draft a reply based on Handbook comms rules, create `Plans/PLAN_<ts>_EMAIL_<slug>.md` with Summary/Analysis/Actions sections, write `Pending_Approval/APPROVAL_<ts>_email_<slug>.md` with `action: send_email, parameters: {to, subject, body, reply_to_uid}`. For `type: whatsapp`: summarise message context, create plan with `status: complete` (no outbound action in Silver). All other types unchanged from Bronze.
  - **Expected outcome**: Updated SKILL.md passes skill-creator validation. Running the skill on an `EMAIL_*.md` task produces both a Plan and an Approval file.
  - **Dependencies**: T004, T006
  - **Notes**: The approval file schema is in `contracts/approval-request-schema.md`. The skill must NOT send email directly — only write the approval file.

- [X] T013 [P] [US2] Implement `smtp_imap.py` helpers in `mcp-servers/email-mcp/smtp_imap.py`
  - **Description**: Implement three functions: `send_email(to, subject, body, reply_to_message_id=None) -> dict` using `smtplib.SMTP_SSL("smtp.gmail.com", 465)`; `draft_reply(message_id, draft_body) -> dict` using `imaplib` APPEND to Drafts; `search_inbox(query, max_results=10) -> list` using `imaplib SEARCH`. All read `GMAIL_EMAIL` and `GMAIL_APP_PASSWORD` from env. Returns `{status, message_id}` or `[{uid, from, subject, snippet}]`.
  - **Expected outcome**: `python -c "from mcp_servers.email_mcp.smtp_imap import send_email"` exits 0. With `DRY_RUN=true`, `send_email()` logs the action without connecting to SMTP.
  - **Dependencies**: T003
  - **Notes**: Gate all actual SMTP/IMAP calls behind `if os.getenv("DRY_RUN","true").lower() != "false": return {"status": "dry_run", ...}`.

- [X] T014 [US2] Implement `email-mcp` MCP server in `mcp-servers/email-mcp/server.py`
  - **Description**: Write a Python MCP server using the `mcp` SDK with stdio transport. Register three tools: `send_email`, `draft_reply`, `search_inbox` — each delegating to `smtp_imap.py`. Every call appends a NDJSON log entry to `AI_Employee_Vault/Logs/YYYY-MM-DD.json` with `action_type, actor: email-mcp, target, parameters, approval_status, result`.
  - **Expected outcome**: `python mcp-servers/email-mcp/server.py` starts and accepts MCP tool calls over stdio. Claude can call `send_email` from within a skill session.
  - **Dependencies**: T013
  - **Notes**: See plan.md Module 7 for the full MCP registration JSON block. Stdio transport means no network port needed.

- [X] T015 [US2] Register `email-mcp` in `~/.config/claude-code/mcp.json`
  - **Description**: Append or create the `email-mcp` entry in `~/.config/claude-code/mcp.json` using the exact JSON from plan.md Module 7. Use absolute path to `server.py`. Pass `GMAIL_EMAIL` and `GMAIL_APP_PASSWORD` as env vars (reference from shell env, not hardcoded values).
  - **Expected outcome**: `claude mcp list` shows `email-mcp`. Claude can call `send_email` tool in a session.
  - **Dependencies**: T014

- [X] T016 [P] [US2] Implement `ApprovalWatcher` in `watchers/approval_watcher.py`
  - **Description**: Extend `BaseWatcher`. Poll `AI_Employee_Vault/Approved/` every 5 seconds using `PollingObserver(timeout=5)`. For each new `APPROVAL_*.md` file not in `scripts/processed_approvals.json`: read YAML frontmatter, write `Needs_Action/ACTION_<ts>_<slug>.md` with `type: action_trigger, action_type, approval_file, action_params`. Save filename to registry. Also poll `Rejected/` — log rejected approvals to `Logs/` and do NOT create action files.
  - **Expected outcome**: Moving an `APPROVAL_*.md` to `Approved/` causes `Needs_Action/ACTION_*.md` to appear within 5 seconds.
  - **Dependencies**: T004, T005
  - **Notes**: Frontmatter schema for `action_trigger` type is in `contracts/task-file-schema.md`.

- [X] T017 [US2] Use `skill-creator` to create `execute-plan` SKILL.md in `.claude/skills/execute-plan/SKILL.md`
  - **Description**: Invoke `skill-creator` and create the `execute-plan` skill. Workflow: (1) find all `type: action_trigger` files in `Needs_Action/`; (2) for each: read `approval_file` path and `action_type`; (3) if `action_type: send_email` → call `email-mcp` `send_email` tool with `action_params`; (4) if `action_type: linkedin_post` → call `browsing-with-playwright` to post on LinkedIn; (5) on success: move `ACTION_*.md` → `Done/`, update linked `PLAN_*.md` status to `executed`, move `APPROVAL_*.md` to `Done/`, append log; (6) on failure (after 3 retries, 5s backoff): write `Needs_Action/ERROR_*.md`, restore `APPROVAL_*.md` to `Pending_Approval/`.
  - **Expected outcome**: Running execute-plan on an `ACTION_*.md` file (action_type: send_email, DRY_RUN=true) logs the action to Logs/ and moves files to Done/. On failure after 3 retries: `Plans/PLAN_*.md` status reverts to `awaiting_approval`, `ERROR_*.md` is written, `APPROVAL_*.md` returns to `Pending_Approval/`.
  - **Dependencies**: T015, T016

- [X] T018 [US2] Extend `orchestrator.py` to launch `ApprovalWatcher` by default
  - **Description**: Update `orchestrator.py` so that running without `--watcher` flag (or with `--watcher all`) always starts `ApprovalWatcher` alongside `FilesystemWatcher`. `--watcher approval` starts only the ApprovalWatcher. Update startup log message to list all active watchers.
  - **Expected outcome**: `python orchestrator.py` starts both `FilesystemWatcher` and `ApprovalWatcher`. Log shows both watcher names.
  - **Dependencies**: T010, T016

- [X] T019 [US2] Validate US2 end-to-end: email approval pipeline
  - **Description**: Manual validation checklist. (1) Place a test `EMAIL_task.md` in `Needs_Action/`. (2) Invoke `process-needs-action` → confirm `Plans/PLAN_*.md` and `Pending_Approval/APPROVAL_*.md` created. (3) Start orchestrator → move APPROVAL_*.md to `Approved/` → confirm `ACTION_*.md` in `Needs_Action/` within 5s. (4) Invoke `execute-plan` → confirm DRY_RUN log entry in `Logs/` and files moved to `Done/`. (5) Check `Dashboard.md` updated.
  - **Expected outcome**: SC-003 (plans created), SC-006 (no action before approval) verified. FR-016, FR-017 pass.
  - **Dependencies**: T012, T017, T018

**Checkpoint**: US2 complete. Full email planning → approval → execution pipeline working.

---

## Phase 5: User Story 3 — LinkedIn Lead-Generation Post (Priority: P2)

**Goal**: `linkedin-post` skill generates a post from `Business_Goals.md`, writes to `Pending_Approval/`, and on approval publishes via Playwright MCP (or dry-run logs).

**Independent Test**: Invoke `linkedin-post` skill. Within 2 minutes, `Plans/PLAN_*_linkedin.md` and `Pending_Approval/APPROVAL_*_linkedin.md` exist. Move the approval file to `Approved/`. Orchestrator creates `ACTION_*.md`. Invoke `execute-plan` → `DRY_RUN=true` logs post content to `Logs/` with `approval_status: dry_run`. No real post published.

- [X] T020 [US3] Populate `AI_Employee_Vault/Business_Goals.md` with real or representative content
  - **Description**: Replace placeholder content in `Business_Goals.md` (created in T006) with at least 2 real (or realistic) services, one revenue OKR, and 5 specific LinkedIn post topic ideas relevant to the business. This is the data source for the `linkedin-post` skill.
  - **Expected outcome**: File has substantive content in all three sections. The `linkedin-post` skill can generate a post purely from this file without asking clarifying questions.
  - **Dependencies**: T006

- [X] T021 [US3] Use `skill-creator` to create `linkedin-post` SKILL.md in `.claude/skills/linkedin-post/SKILL.md`
  - **Description**: Invoke `skill-creator` and create the `linkedin-post` skill. Workflow: (1) read `AI_Employee_Vault/Business_Goals.md` for services and topics; (2) read `AI_Employee_Vault/Company_Handbook.md` for brand voice; (3) generate a 100–300 word post with: value proposition, specific service/product mention from Business_Goals, call-to-action; (4) write `Plans/PLAN_<ts>_linkedin.md` with full post draft and `status: awaiting_approval`; (5) write `Pending_Approval/APPROVAL_<ts>_linkedin.md` with `action: linkedin_post, parameters: {post_content}`; (6) update `Dashboard.md` pending approvals count.
  - **Expected outcome**: Running the skill produces both Plan and Approval files. Post is 100–300 words, contains a CTA, and references a service from Business_Goals.md.
  - **Dependencies**: T004, T006, T020
  - **Notes**: Post format guidance per FR-010. Skill must NOT call any MCP tool — writing approval file is the boundary.

- [X] T022 [US3] Validate US3 end-to-end: LinkedIn post approval and dry-run publication
  - **Description**: Manual validation checklist. (1) Invoke `linkedin-post` skill → verify `Plans/PLAN_*_linkedin.md` (100–300 words, has CTA) and `Pending_Approval/APPROVAL_*_linkedin.md` created. (2) Move APPROVAL_*_linkedin.md to `Approved/` → confirm `ACTION_*_linkedin.md` in `Needs_Action/` within 5s. (3) Invoke `execute-plan` with `DRY_RUN=true` → confirm Logs/ entry with `action_type: linkedin_post, approval_status: dry_run` and files moved to `Done/`.
  - **Expected outcome**: SC-005 (LinkedIn post drafted → approved → logged) passes. FR-010, FR-011, FR-012 verified.
  - **Dependencies**: T017, T018, T021

**Checkpoint**: US3 complete. LinkedIn post generation and dry-run approval pipeline working.

---

## Phase 6: User Story 4 — Scheduler Runs Tasks Automatically (Priority: P3)

**Goal**: System-cron entries run watchers and skills on schedule without manual invocation. Each run produces a log entry with `actor: scheduler`.

**Independent Test**: Add a cron entry that runs `python orchestrator.py --watcher gmail` every 5 minutes. Wait for next trigger. Confirm a new `Logs/YYYY-MM-DD.json` entry appears with `actor: scheduler`.

- [X] T023 [US4] Create `scripts/install-cron.sh` cron generator script
  - **Description**: Write a bash script that reads `VAULT_PATH` and `PROJECT_DIR` from `.env`, then generates and installs three crontab entries: (1) `*/5 * * * *` gmail watcher with `--watcher gmail --cron`; (2) `0 8 * * 1` linkedin-post skill via `claude --print`; (3) `0 9 * * *` process-needs-action skill via `claude --print`. WhatsApp watcher is NOT in crontab — it runs as a persistent daemon started by `orchestrator.py`. Script must NOT duplicate entries if run twice. Add WSL2 note to script header: `sudo service cron start` required per session.
  - **Expected outcome**: Running `bash scripts/install-cron.sh` installs all 3 entries. `crontab -l` shows them. Running again does not duplicate. No WhatsApp cron entry present.
  - **Dependencies**: T010

- [X] T024 [US4] Wire `--cron` flag to `actor: scheduler` log entry in `orchestrator.py`
  - **Description**: When `orchestrator.py` is started with the `--cron` flag, append a NDJSON log entry to `Logs/YYYY-MM-DD.json` with `action_type: watcher_start, actor: scheduler, result: started, timestamp: ISO-8601Z` before starting any watcher. Manual runs (without `--cron`) do NOT write this entry.
  - **Expected outcome**: `python orchestrator.py --watcher gmail --cron` creates a Logs/ entry with `actor: scheduler`. `python orchestrator.py --watcher gmail` (no `--cron`) does NOT create a scheduler entry.
  - **Dependencies**: T010
  - **Notes**: FR-020 requirement. Detection is now unambiguous — `--cron` flag is the sole signal, not `--watcher` presence (resolves I2).

- [X] T025 [US4] Validate US4: confirm cron produces scheduler log entries
  - **Description**: Manual validation checklist. (1) Run `bash scripts/install-cron.sh`. (2) `sudo service cron start`. (3) Wait for next `*/5` trigger. (4) Confirm `Logs/YYYY-MM-DD.json` contains entry with `actor: scheduler`. (5) Confirm no crash in cron log (`/var/log/syslog`).
  - **Expected outcome**: SC-007 (3 consecutive cron cycles produce logs) verified.
  - **Dependencies**: T023, T024

**Checkpoint**: US4 complete. Fully autonomous scheduling operational.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Dashboard accuracy, documentation, security check, and end-to-end validation.

- [X] T026 Update `AI_Employee_Vault/Dashboard.md` with Silver Tier sections
  - **Description**: Extend `Dashboard.md` to include the new `## Pending Approvals` section (count of files in `Pending_Approval/` + list of filenames), `## Recent Rejections` (last 3 `Rejected/` items), and update `## System Status` watcher list to include `gmail_watcher`, `whatsapp_watcher`, `approval_watcher`. Update the `process-needs-action` skill SKILL.md step that writes Dashboard to populate these new sections.
  - **Expected outcome**: After running `process-needs-action` or `linkedin-post`, Dashboard.md shows accurate pending approval count and watcher statuses.
  - **Dependencies**: T012, T021

- [X] T027 [P] Run full end-to-end acceptance flow from `plan.md` (10 steps)
  - **Description**: Execute all 10 steps from plan.md's "End-to-End Acceptance Flow" section. Record pass/fail for each step. Fix any failures. Steps: (1) start orchestrator; (2) SC-001 email capture; (3) SC-002 WhatsApp capture; (4) process-needs-action → plans + approval files; (5) approve email → execute-plan → send; (6) linkedin-post → approve → dry-run; (7) Dashboard updated; (8) Logs entries present; (9) restart watcher → no duplicate tasks; (10) no credentials in `.md` files.
  - **Expected outcome**: All 10 steps pass. SC-001 through SC-008 all satisfied.
  - **Dependencies**: T011, T019, T022, T025

- [X] T028 [P] Security check: verify no credentials in vault or committed files
  - **Description**: Grep all `AI_Employee_Vault/` `.md` files, `watchers/`, `mcp-servers/`, and `scripts/` for patterns: `password`, `token`, `secret`, `api_key`, `GMAIL_APP_PASSWORD` with actual values. Verify `whatsapp_session/` is in `.gitignore`. Verify `.env` is in `.gitignore`. Confirm `DRY_RUN=true` is the default in `.env.example`.
  - **Expected outcome**: SC-008 passes. Zero credential leaks in any tracked file.
  - **Dependencies**: None

- [X] T029 Update `README.md` with Silver Tier quickstart section
  - **Description**: Add a `## Silver Tier` section to `README.md` with: prerequisites (Gmail App Password, WhatsApp Web access), 6-step quickstart (install deps, configure `.env`, install playwright, run `install-cron.sh`, start orchestrator, invoke skills), and link to `specs/002-silver-ai-employee/quickstart.md`.
  - **Expected outcome**: A new developer can follow README.md Silver Tier section to get the system running in under 30 minutes.
  - **Dependencies**: T027

- [X] T030 Commit all Silver Tier artifacts with `feat(silver):` commit message
  - **Description**: Stage all new and modified files for Silver Tier. Commit with message: `feat(silver): implement Silver Tier multi-channel assistant with Gmail/WhatsApp watchers, email-mcp, LinkedIn post skill, and HITL approval pipeline`. Verify commit includes: `watchers/gmail_watcher.py`, `watchers/whatsapp_watcher.py`, `watchers/approval_watcher.py`, `mcp-servers/email-mcp/`, `.claude/skills/linkedin-post/`, `.claude/skills/execute-plan/`, updated `process-needs-action` SKILL.md, `scripts/install-cron.sh`, vault folder `.gitkeep` files, `specs/002-silver-ai-employee/tasks.md`.
  - **Expected outcome**: `git log --oneline -1` shows `feat(silver):` commit. `git status` is clean.
  - **Dependencies**: T027, T028, T029

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ← BLOCKS all user stories
    │
    ├──▶ Phase 3 (US1 — P1) — Gmail + WhatsApp watchers
    │        │
    │        ▼
    ├──▶ Phase 4 (US2 — P2) — Planning + email-mcp + approval pipeline
    │        │
    │        ▼
    ├──▶ Phase 5 (US3 — P2) — LinkedIn post skill
    │        │
    │        ▼
    └──▶ Phase 6 (US4 — P3) — Scheduling
             │
             ▼
         Phase 7 (Polish) — validation, docs, commit
```

### User Story Dependencies

| Story | Depends On | Can Parallelise With |
|-------|-----------|---------------------|
| US1 (Gmail+WhatsApp) | Phase 2 complete | — |
| US2 (Plans+Email) | US1 (needs task file types) | US3 (different files) |
| US3 (LinkedIn) | Phase 2 complete | US2 (independent MCP path) |
| US4 (Scheduling) | US1 + US2 (skills must exist) | — |

### Within Each Phase

- T007 and T008 are **parallel** (different watcher files, independent).
- T013 and T016 are **parallel** (different files: smtp_imap.py vs approval_watcher.py).
- T027 and T028 are **parallel** (independent checks).

---

## Parallel Execution Examples

### US1 — Run in parallel after Phase 2 completes:
```
Task T007: Implement GmailWatcher in watchers/gmail_watcher.py
Task T008: Implement WhatsAppWatcher in watchers/whatsapp_watcher.py
Task T009: Install Playwright Chromium + gitignore
```

### US2 — Run in parallel:
```
Task T013: Implement smtp_imap.py helpers
Task T016: Implement ApprovalWatcher in watchers/approval_watcher.py
```

### Phase 7 — Run in parallel:
```
Task T027: Full end-to-end acceptance flow
Task T028: Security credential check
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — ~6 hours)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T006)
3. Complete Phase 3: US1 (T007–T011)
4. **STOP and VALIDATE**: Gmail and WhatsApp task capture working independently
5. Demo: new email → task file appears automatically

### Incremental Delivery

| Milestone | Tasks | Deliverable |
|-----------|-------|-------------|
| M1 — Event Capture | T001–T011 | Gmail + WhatsApp watchers → Needs_Action/ |
| M2 — Planning + Email | T012–T019 | Plans + approval files + email-mcp |
| M3 — LinkedIn | T020–T022 | LinkedIn post → dry-run published |
| M4 — Autonomous | T023–T025 | Cron runs everything without manual triggers |
| M5 — Done | T026–T030 | Dashboard, docs, commit |

---

## Notes

- `[P]` tasks = different files, no incomplete task dependencies — safe to run in parallel
- `[US#]` label maps every task to its spec.md user story for traceability
- Always invoke `skill-creator` before creating or updating any SKILL.md (CLAUDE.md rule)
- `DRY_RUN=true` is the default — all external actions log-only during development
- `PollingObserver(timeout=N)` required on all vault watchers — no inotify on WSL2 NTFS
- Commit after each phase with `feat(silver):` prefix
- Validate each user story independently at its checkpoint before proceeding
