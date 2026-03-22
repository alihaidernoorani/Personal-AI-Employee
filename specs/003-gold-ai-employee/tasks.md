# Tasks: Gold Tier Personal AI Employee

**Input**: Design documents from `/specs/003-gold-ai-employee/`
**Branch**: `003-gold-ai-employee` | **Date**: 2026-03-22
**Spec**: spec.md | **Plan**: plan.md | **Data model**: data-model.md | **Contracts**: contracts/

**Legend**: `[P]` = parallelizable | `[US#]` = user story | `🔐` = credential checkpoint | `🧯` = dry-run required | `🧪` = test gate (DO NOT proceed if fails)

**⚠️ Build-vs-verify**: Tasks marked `[VERIFY]` confirm existing Silver tier components work. Tasks marked `[BUILD]` are new Gold tier additions.

**Total tasks**: 79 (T001–T076 + T010b + T012b + updates to T073/T074/T065) | Last updated: 2026-03-22 (sp.analyze remediation pass)

---

## Phase 1: Setup & Environment Verification

**Purpose**: Confirm the Gold tier environment is ready. Most infrastructure exists from Silver; this phase ensures it's correct before building anything new.

**Independent Test**: `DRY_RUN=true python orchestrator.py --status` exits 0 with all Silver watchers listed.

- [X] T001 [VERIFY] Confirm Python 3.13+ is active in `.venv` and `requirements.txt` is installed
  > **Inputs**: `.venv/`, `requirements.txt` | **Outputs**: confirmed version + installed packages list
  > **Deps**: none | **Done when**: `python --version` ≥ 3.13 and `pip list` shows watchdog, playwright, mcp, requests, schedule
  > **Test**: `python -c "import watchdog, playwright, mcp, requests, schedule; print('OK')"`
  > **Dry run**: N/A

- [X] T002 [VERIFY] Confirm vault folder structure exists and all required folders are present in `AI_Employee_Vault/`
  > **Inputs**: `VAULT_PATH` from `.env` | **Outputs**: all required folders present
  > **Deps**: T001 | **Done when**: Inbox, Needs_Action, In_Progress/local_agent, Plans, Pending_Approval, Approved, Rejected, Done, Briefings, Accounting, Logs all exist; `Accounting/Current_Month.md` exists (see M4 fix below — created by T010b)
  > **Test**: `ls $VAULT_PATH` shows all folders
  > **Dry run**: N/A

- [X] T003 [P] [VERIFY] Confirm `.mcp.json` at project root loads all existing MCP servers (email-mcp, playwright)
  > **Inputs**: `.mcp.json`, `mcp-servers/email-mcp/server.py` | **Outputs**: Claude Code can call email-mcp tools
  > **Deps**: T001 | **Done when**: `.mcp.json` contains `email-mcp` and `playwright` entries; `python mcp-servers/email-mcp/server.py` starts without error; Claude Code session shows both MCP servers in its tool list
  > **Test**: Read `.mcp.json` and verify both server entries exist with correct command/args; then `claude "Use email-mcp search_inbox query: test"` returns a result or empty list (not an auth/connection error)
  > **Dry run**: N/A

- [X] T004 [P] [VERIFY] Confirm Claude Code can read from and write to the vault (file system access test)
  > **Inputs**: `VAULT_PATH` | **Outputs**: Claude writes and reads a test file successfully
  > **Deps**: T001, T002 | **Done when**: Claude creates `Needs_Action/TEST_setup.md`, reads it back, moves it to Done/
  > **Test**: `claude "Write a file called Needs_Action/TEST_setup.md with content 'setup ok', then move it to Done/"` — verify Done/TEST_setup.md exists
  > **Dry run**: N/A

- [X] T005 [VERIFY] Confirm `DRY_RUN=true` is set in `.env` before any further phase
  > **Inputs**: `.env` | **Outputs**: confirmed DRY_RUN=true
  > **Deps**: none | **Done when**: `grep DRY_RUN .env` shows `DRY_RUN=true`
  > **Test**: Manual check
  > **Dry run**: N/A — this IS the dry-run gate

🧪 **Phase 1 Gate**: T001–T005 must all pass. If any fails, resolve before proceeding.

---

## 🔐 Checkpoint 1: Base Credentials

**⛔ STOP — Human action required before Phase 2.**

Copy `.env.example` to `.env` and fill in all values. Placeholders are acceptable for services not yet configured (e.g., Odoo, social media tokens) but the following MUST be set now:

- [ ] T006 [HUMAN] Create `.env` from `.env.example` and populate: `VAULT_PATH`, `VAULT_TEMP_PATH`, `WHATSAPP_SESSION_PATH`, `GMAIL_CREDENTIALS_PATH` (can point to a placeholder file for now)
  > **Inputs**: `.env.example` | **Outputs**: `.env` with all base keys present (values can be placeholder for later checkpoints)
  > **Deps**: T001–T005 passed | **Done when**: `.env` exists; `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('VAULT_PATH'))"` returns a non-None path
  > **Test**: Run `python orchestrator.py --status` — should start without crashing (watchers may warn about credentials, that is acceptable)
  > **Dry run**: N/A — credential setup

✅ **Checkpoint 1 cleared** — proceed to Phase 2.

---

## Phase 2: Watchers

**Purpose**: Verify all existing Silver-tier watchers and build the missing Finance watcher.

**User Stories covered**: US3 (WhatsApp), US4 (Finance), foundational for US1 (Gmail)

**Independent Test**: Drop a file into `Inbox/`, send a keyword WhatsApp (if session active), and wait; verify `Needs_Action/` contains a `FILE_*.md` within 30 seconds and `WHATSAPP_*.md` within 60 seconds.

- [X] T007 [P] [VERIFY] [US1] Verify `watchers/gmail_watcher.py` produces `Needs_Action/EMAIL_*.md` using mock IMAP data
  > **Inputs**: `watchers/gmail_watcher.py`, `scripts/processed_gmail.json` | **Outputs**: `Needs_Action/EMAIL_<id>.md`
  > **Deps**: T006 | **Done when**: GmailWatcher runs one poll cycle without crashing; on new unread email, `EMAIL_*.md` appears in `Needs_Action/` within **60 s** (per NFR-005); ID added to `processed_gmail.json`
  > **Test**: Send a test email to the monitored account; record arrival timestamp; measure time until `EMAIL_*.md` appears; assert elapsed time ≤ 60 s
  > **Dry run**: Set `GMAIL_CREDENTIALS_PATH` to a mock credentials file; verify watcher logs polling attempt and handles auth error gracefully

- [X] T008 [P] [VERIFY] [US3] Verify `watchers/whatsapp_watcher.py` starts exactly one browser session and no second session opens on restart
  > **Inputs**: `watchers/whatsapp_watcher.py`, `WHATSAPP_SESSION_PATH` | **Outputs**: single Playwright browser PID; `Needs_Action/WHATSAPP_*.md` on keyword match
  > **Deps**: T006 | **Done when**: PID file written; second instantiation of watcher detects existing PID and reuses session; keyword-matching message creates `WHATSAPP_*.md`
  > **Test**: Start watcher → record PID → restart watcher → verify same session path used, no new QR scan prompted, PID file updated
  > **Dry run**: Use `HEADLESS=true`; send a test keyword message from a secondary number

- [X] T009 [P] [VERIFY] Verify `watchers/filesystem_watcher.py` creates `Needs_Action/FILE_*.md` within 30 s of a file drop into `Inbox/`
  > **Inputs**: `watchers/filesystem_watcher.py`, `AI_Employee_Vault/Inbox/` | **Outputs**: `Needs_Action/FILE_<filename>_<timestamp>.md`
  > **Deps**: T006 | **Done when**: Drop `test.pdf` into Inbox/; `FILE_test.pdf_*.md` appears in Needs_Action/ within 30 s
  > **Test**: `cp test.pdf $VAULT_PATH/Inbox/` → wait 30 s → `ls $VAULT_PATH/Needs_Action/FILE_*`
  > **Dry run**: Use a zero-byte test file; verify metadata-only creation

- [X] T010 [BUILD] [US4] Build `watchers/finance_watcher.py` extending `BaseWatcher` to read bank transactions and append to `Bank_Transactions.md`
  > **Inputs**: `watchers/base_watcher.py`, `BANK_CSV_PATH` or `BANK_API_TOKEN` from `.env`, `Bank_Transactions.md` | **Outputs**: new rows appended to `Bank_Transactions.md`; `Needs_Action/FINANCE_<txn_id>.md` per new transaction; `scripts/processed_finance.json` updated
  > **Deps**: T009 | **Done when**: `check_for_updates()` returns new transactions; `create_action_file()` writes valid FINANCE_*.md with correct frontmatter (type, source, source_id, amount, payee, reference, date); processed IDs persisted to `processed_finance.json`
  > **Test**: Add a mock transaction row to the CSV source; run one poll cycle; verify `FINANCE_*.md` appears and `Bank_Transactions.md` has new row
  > **Dry run**: Set `BANK_CSV_PATH` to a mock CSV with 3 sample transactions; run watcher; verify 3 FINANCE_*.md files created and 3 rows appended to `Bank_Transactions.md`

- [X] T011 [BUILD] [US4] Create `scripts/processed_finance.json` initial state file (`{"source_type": "finance", "processed_ids": [], "last_poll": null}`)
  > **Inputs**: none | **Outputs**: `scripts/processed_finance.json`
  > **Deps**: T010 | **Done when**: File exists and is valid JSON; finance_watcher reads it on startup without error
  > **Test**: `python -c "import json; print(json.load(open('scripts/processed_finance.json')))"` — returns valid structure
  > **Dry run**: N/A

- [X] T010b [BUILD] [US4] Create `AI_Employee_Vault/Accounting/Current_Month.md` as a secondary append target mirroring `Bank_Transactions.md`; update `finance_watcher.py` to append new transaction rows to both files
  > **Inputs**: `watchers/finance_watcher.py`, `AI_Employee_Vault/Accounting/` folder | **Outputs**: `Accounting/Current_Month.md` exists; every new transaction row appended to both `Bank_Transactions.md` and `Accounting/Current_Month.md`
  > **Deps**: T010 | **Done when**: `Accounting/Current_Month.md` exists with correct header; after a mock transaction poll cycle, the same row appears in both files; the hackathon document's `/Accounting/Current_Month.md` reference is satisfied
  > **Test**: Run finance watcher with mock CSV; verify `diff <(tail -1 Bank_Transactions.md) <(tail -1 Accounting/Current_Month.md)` returns identical rows
  > **Dry run**: Use mock CSV; verify both files updated; no real bank connection

- [X] T012 [BUILD] Register `finance_watcher.py` in `orchestrator.py` watcher dispatch (add to `--watcher` choices and default launch set)
  > **Inputs**: `orchestrator.py`, `watchers/finance_watcher.py` | **Outputs**: finance watcher starts as daemon thread when orchestrator runs
  > **Deps**: T010, T011 | **Done when**: `python orchestrator.py --status` lists finance watcher; `python orchestrator.py --watcher finance` starts it without crashing
  > **Test**: `python orchestrator.py --watcher finance` → wait 10 s → verify no crash; `tail -f $VAULT_PATH/Logs/$(date +%Y-%m-%d).json` shows finance watcher startup log
  > **Dry run**: `DRY_RUN=true python orchestrator.py --watcher finance` with mock CSV

- [X] T012b [VERIFY] Confirm no watcher contains reasoning or decision logic (FR-006): grep all watcher files for Claude MCP calls, decision branching based on content analysis, or skill invocations
  > **Inputs**: `watchers/*.py` | **Outputs**: confirmed zero reasoning logic in any watcher
  > **Deps**: T012 | **Done when**: `grep -rn "claude\|skill\|reason\|decide\|analyze_content" watchers/` returns no matches in core watcher logic (excluding comments and import names); all watchers only write structured `.md` files to `Needs_Action/` without interpreting content
  > **Test**: Read each watcher file; confirm logic is limited to: poll source → check processed IDs → extract metadata → write frontmatter → update state file. No content interpretation.
  > **Dry run**: N/A

🧪 **Phase 2 Gate**: T007–T012 and T012b must all pass. Finance watcher must produce FINANCE_*.md from mock data; all watchers confirmed reasoning-free before proceeding.

---

## 🔐 Checkpoint 2: Gmail Credentials

**⛔ STOP — Human action required.**

- [ ] T013 [HUMAN] Set up Gmail OAuth2 credentials and configure `GMAIL_CREDENTIALS_PATH` in `.env`
  > **Inputs**: Google Cloud Console OAuth2 credentials JSON | **Outputs**: `GMAIL_CREDENTIALS_PATH` pointing to valid credentials; Gmail watcher polls successfully
  > **Deps**: T007 | **Done when**: `python watchers/gmail_watcher.py` runs one real poll cycle; no `AUTH_FAILED` errors; at least one email retrieved (or empty inbox logged)
  > **Test**: Drop a test email to the monitored account; within 120 s verify `Needs_Action/EMAIL_*.md` appears
  > **Dry run**: N/A — credential setup

✅ **Checkpoint 2 cleared** — proceed to Phase 3.

---

## Phase 3: Orchestrator Extensions

**Purpose**: Add watchdog process, cron scheduler, and vault health check to `orchestrator.py`. These are cross-cutting Gold-tier additions not present in Silver.

**User Stories covered**: Foundational for all stories (reliability NFRs)

**Independent Test**: Kill the gmail_watcher process; verify orchestrator restarts it within 60 seconds and logs a restart entry.

- [X] T014 [BUILD] Add watchdog loop to `orchestrator.py`: monitor watcher process liveness every 60 s; auto-restart up to 3 times/hour per process; write `Needs_Action/ERROR_WATCHDOG_<process>_<timestamp>.md` and log alert after threshold
  > **Inputs**: `orchestrator.py`, running watcher PID list | **Outputs**: auto-restarted process; `ERROR_WATCHDOG_*.md` when threshold exceeded
  > **Deps**: T012 | **Done when**: Watchdog detects dead process within 60 s; restarts it; hourly counter resets at :00; after 3 restarts writes ERROR file and stops auto-restarting
  > **Test**: Kill `gmail_watcher` subprocess → wait 65 s → verify process restarted (new PID) and audit log shows `actor: watchdog`
  > **Dry run**: `DRY_RUN=true` — watchdog can simulate kill/restart cycle without real process termination

- [X] T015 [BUILD] Add `schedule` library cron jobs to `orchestrator.py`: Sunday 23:00 → run `ceo-briefing` skill; daily 08:00 → run `process-needs-action` skill; every 90 days → delete `Logs/` files older than 90 days
  > **Inputs**: `orchestrator.py`, `schedule` library | **Outputs**: scheduled job registry; ceo-briefing triggered Sunday 23:00; log cleanup runs on schedule
  > **Deps**: T014 | **Done when**: `schedule.jobs` list shows 3 jobs; advancing mock time to Sunday 23:00 fires ceo-briefing invocation; daily sweep logs `actor: scheduler`
  > **Test**: Temporarily change ceo-briefing cron to 1 minute from now; start orchestrator; verify briefing skill is invoked within 65 s; restore to Sunday 23:00
  > **Dry run**: Set `DRY_RUN=true`; verify scheduler fires but briefing skill detects dry-run and does not write a real briefing

- [X] T016 [BUILD] Add vault health check to `orchestrator.py`: check `VAULT_PATH` mount every 5 minutes; if inaccessible, pause all watchers, write error to `VAULT_TEMP_PATH/ERROR_VAULT_UNAVAILABLE.md`, retry every 30 s; resume watchers on restoration
  > **Inputs**: `orchestrator.py`, `VAULT_PATH`, `VAULT_TEMP_PATH` | **Outputs**: watchers paused on vault loss; `ERROR_VAULT_UNAVAILABLE.md` in temp folder; watchers resumed on restoration
  > **Deps**: T015 | **Done when**: Simulating vault unavailability (e.g., rename vault folder temporarily) triggers watcher pause within 5 min; temp error file written; vault restored → watchers resume automatically
  > **Test**: `mv $VAULT_PATH $VAULT_PATH.bak` → wait 6 min → verify watchers paused; `mv $VAULT_PATH.bak $VAULT_PATH` → wait 35 s → verify watchers resumed
  > **Dry run**: `DRY_RUN=true` — vault check still runs; simulate by setting `VAULT_PATH` to an invalid path temporarily

- [X] T017 [BUILD] Configure `VAULT_TEMP_PATH` in `.env` and add temp-to-vault sync logic: on vault restoration, copy all files from `VAULT_TEMP_PATH/` into the correct vault subfolders
  > **Inputs**: `VAULT_TEMP_PATH` env var, temp folder with pending watcher output | **Outputs**: temp files synced into vault on restoration; temp folder cleared after sync
  > **Deps**: T016 | **Done when**: Drop a file to Inbox/ while vault is "unavailable" (temp path active); after vault restored, `Needs_Action/FILE_*.md` appears with temp file content
  > **Test**: Simulate vault unavailability; drop a file; restore vault; verify sync within 60 s
  > **Dry run**: Use a test vault path and temp path with no real data

🧪 **Phase 3 Gate**: T014–T017 must pass. Watchdog must demonstrably restart a killed watcher before proceeding.

---

## Phase 4: MCP Servers

**Purpose**: Extend the existing Email MCP for graceful degradation; build Social MCP and Odoo MCP from scratch.

**User Stories covered**: US1 (email), US4 (Odoo), US6/US6b (social)

**Independent Test (per MCP)**: Each MCP tool called with `DRY_RUN=true` returns `{ "dry_run": true, "would_have": "..." }` without performing any real action.

### 4a — Email MCP Extensions

- [X] T018 [BUILD] [US1] Add `queue_email` tool to `mcp-servers/email-mcp/server.py`: accepts `{to, subject, body}`, appends to `scripts/email_outbox_queue.json`, returns `{queued: true, queue_position: N}`
  > **Inputs**: `mcp-servers/email-mcp/server.py`, `scripts/email_outbox_queue.json` | **Outputs**: entry added to queue file
  > **Deps**: T003 | **Done when**: Tool registered; calling it appends a JSON object to the queue file; subsequent calls increment queue_position correctly
  > **Test**: `claude "Use email-mcp to queue_email to test@example.com subject Test body Hello"` → verify `email_outbox_queue.json` has 1 entry
  > **Dry run**: `DRY_RUN=true` — queue_email still writes to queue (queue is local, not a live send)

- [X] T019 [BUILD] [US1] Add `flush_queue` tool to `mcp-servers/email-mcp/server.py`: reads `scripts/email_outbox_queue.json`, sends each queued email via SMTP in order, returns `{sent: N, failed: M}`; clears sent entries
  > **Inputs**: `scripts/email_outbox_queue.json`, SMTP credentials | **Outputs**: queued emails sent; sent entries removed from queue; `{sent, failed}` summary
  > **Deps**: T018 | **Done when**: Queue with 2 entries → flush_queue sends 2 emails (DRY_RUN logs "would send"); queue is empty after successful flush; failed entries remain with error annotation
  > **Test**: queue_email × 2 → flush_queue (DRY_RUN=true) → verify queue cleared and log shows 2 dry-run entries
  > **Dry run**: `DRY_RUN=true` — logs intended sends without SMTP connection; returns `{sent: 0, failed: 0, dry_run: true, would_have_sent: 2}`

- [X] T020 [BUILD] Create `scripts/email_outbox_queue.json` with initial empty state: `[]`
  > **Inputs**: none | **Outputs**: `scripts/email_outbox_queue.json`
  > **Deps**: T018 | **Done when**: File exists; `queue_email` appends to it; `flush_queue` reads it without error
  > **Test**: `python -c "import json; print(json.load(open('scripts/email_outbox_queue.json')))"` returns `[]`
  > **Dry run**: N/A

### 4b — Social MCP (New Build)

- [X] T021 [BUILD] [US6] Create `mcp-servers/social-mcp/server.py` with MCP stdio transport scaffold and approval_id enforcement (all post_* tools reject calls without valid approval_id)
  > **Inputs**: `mcp>=1.0.0`, `contracts/social-mcp.md` | **Outputs**: `mcp-servers/social-mcp/server.py` with tool registry and approval gate
  > **Deps**: T003 | **Done when**: Server starts without error; calling any post_* tool without approval_id returns `{error: "APPROVAL_REQUIRED", retryable: false}`; all platform API base URLs use `https://` (verify: no `http://` URLs in server code — NFR-012)
  > **Test**: `python mcp-servers/social-mcp/server.py` starts; tool call without approval_id returns correct error; `grep "http://" mcp-servers/social-mcp/server.py` returns no matches
  > **Dry run**: All tools check `DRY_RUN` env var; if true, return `{dry_run: true, would_have: "post to <platform>"}`

- [X] T022 [P] [BUILD] [US6] Add `post_linkedin` tool to `mcp-servers/social-mcp/server.py` using LinkedIn Marketing API
  > **Inputs**: `LINKEDIN_ACCESS_TOKEN` from `.env`, `content`, `visibility?`, `approval_id` | **Outputs**: `{post_id, url, timestamp}` on success; `{error, platform: "linkedin", retryable}` on failure
  > **Deps**: T021 | **Done when**: DRY_RUN=true call returns dry-run response; live call (Checkpoint 3) posts to LinkedIn and returns post_id
  > **Test (dry)**: `DRY_RUN=true` with valid approval_id → `{dry_run: true}`
  > **Dry run**: Return `{dry_run: true, would_have: "post to linkedin: <content[:50]>"}`

- [X] T023 [P] [BUILD] [US6] Add `post_facebook` tool to `mcp-servers/social-mcp/server.py` using Facebook Graph API
  > **Inputs**: `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `content`, `approval_id` | **Outputs**: `{post_id, url, timestamp}`
  > **Deps**: T021 | **Done when**: DRY_RUN=true returns dry-run response; error on missing page token handled gracefully
  > **Test (dry)**: Same as T022 for Facebook
  > **Dry run**: Return `{dry_run: true, would_have: "post to facebook: <content[:50]>"}`

- [X] T024 [P] [BUILD] [US6] Add `post_instagram` tool to `mcp-servers/social-mcp/server.py` using Instagram Graph API
  > **Inputs**: `INSTAGRAM_ACCESS_TOKEN`, `caption`, `image_url?`, `approval_id` | **Outputs**: `{post_id, url, timestamp}`
  > **Deps**: T021 | **Done when**: DRY_RUN=true returns dry-run response
  > **Test (dry)**: Same as T022 for Instagram
  > **Dry run**: Return `{dry_run: true, would_have: "post to instagram: <caption[:50]>"}`

- [X] T025 [P] [BUILD] [US6] Add `post_twitter` tool to `mcp-servers/social-mcp/server.py` using Twitter API v2
  > **Inputs**: `TWITTER_BEARER_TOKEN`, `content` (max 280 chars enforced), `approval_id` | **Outputs**: `{tweet_id, url, timestamp}`
  > **Deps**: T021 | **Done when**: Content >280 chars returns validation error; DRY_RUN=true returns dry-run response
  > **Test (dry)**: Test with 281-char content → validation error; 280-char content DRY_RUN=true → dry-run response
  > **Dry run**: Return `{dry_run: true, would_have: "tweet: <content[:50]>"}`

- [X] T026 [BUILD] [US6b] Add `get_post_summary` tool to `mcp-servers/social-mcp/server.py`: retrieves engagement data from platform API; returns `{platform, post_id, timestamp, content_excerpt, engagement: {...} | null}`
  > **Inputs**: `platform`, `post_id` | **Outputs**: engagement data or graceful null with note
  > **Deps**: T022–T025 | **Done when**: Returns correct structure for each platform; when platform doesn't support engagement, returns `{engagement: null, note: "..."}` (not an error)
  > **Test**: Call with a known post_id (from a prior DRY_RUN test post or mock ID) → verify structure matches contract
  > **Dry run**: Return mock engagement data: `{dry_run: true, engagement: {likes: 0, shares: 0, views: 0}}`

- [X] T027 [BUILD] Register `social-mcp` in `.mcp.json` at project root
  > **Inputs**: `.mcp.json`, `mcp-servers/social-mcp/server.py` | **Outputs**: social-mcp entry in `.mcp.json`
  > **Deps**: T026 | **Done when**: `.mcp.json` contains a `social-mcp` entry with `command: "python"` and `args: ["mcp-servers/social-mcp/server.py"]`; `python mcp-servers/social-mcp/server.py` starts without error; `claude "Use social-mcp post_linkedin with DRY_RUN"` returns dry-run response
  > **Test**: Read `.mcp.json`; verify social-mcp entry exists with correct args; then invoke dry-run post call
  > **Dry run**: N/A

🧪 **Phase 4a+4b Gate**: Email MCP queue tools work; Social MCP dry-run calls return correct responses for all 5 tools. Proceed to Checkpoint 3.

---

## 🔐 Checkpoint 3: External API Credentials

**⛔ STOP — Human action required.**

- [ ] T028 [HUMAN] Populate social media API tokens in `.env`: `LINKEDIN_ACCESS_TOKEN`, `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `INSTAGRAM_ACCESS_TOKEN`, `TWITTER_BEARER_TOKEN`
  > **Done when**: Each token is non-empty; `DRY_RUN=false` test call to `post_linkedin` succeeds (posts to a test page or sandbox)
  > **Test**: `claude "Use social-mcp post_linkedin content 'Test post — AI Employee setup verification' approval_id TEST"` with `DRY_RUN=false` → verify post appears on LinkedIn

✅ **Checkpoint 3 cleared** — proceed to Odoo MCP build (Phase 4c) and Agent Skills (Phase 5).

---

### 4c — Odoo MCP (New Build)

- [X] T029 [BUILD] [US4] Create `mcp-servers/odoo-mcp/server.py` with MCP stdio transport scaffold, Odoo 19+ JSON-RPC session authentication (`/web/session/authenticate`), and auto-reauth on session expiry
  > **Inputs**: `mcp>=1.0.0`, `requests`, `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` | **Outputs**: authenticated Odoo session; `{uid}` stored in server process
  > **Deps**: T027 | **Done when**: Server starts and authenticates against Odoo 19+ instance; on `session.invalid` error, re-authenticates once automatically; all credentials read from `.env` only; `ODOO_URL` must begin with `https://` (verify NFR-012 — no plaintext Odoo connections); `grep "http://" mcp-servers/odoo-mcp/server.py` returns no hardcoded plaintext URL
  > **Test (dry)**: With valid ODOO credentials (Checkpoint 4), server starts and logs `"Odoo session established uid=<N>"`; verify `ODOO_URL` value begins with `https://`
  > **Dry run**: When `DRY_RUN=true`, skip real authentication; return mock uid=1

- [X] T030 [P] [BUILD] [US4] Add `get_customer` tool to `mcp-servers/odoo-mcp/server.py`
  > **Inputs**: `name?`, `email?` (at least one required) | **Outputs**: `[{id, name, email}]`
  > **Deps**: T029 | **Done when**: Tool registered; with valid Odoo credentials returns customer list; no-match returns empty list (not error)
  > **Test (dry)**: DRY_RUN=true → `{dry_run: true, would_have: "search customers by name=<name>"}`
  > **Dry run**: Return mock customer: `{dry_run: true, customers: [{id: "1", name: "Test Customer", email: "test@example.com"}]}`

- [X] T031 [P] [BUILD] [US4] Add `create_invoice` tool to `mcp-servers/odoo-mcp/server.py` (creates draft, does not post)
  > **Inputs**: `customer_id`, `line_items[]`, `due_date` | **Outputs**: `{invoice_id, status: "draft"}`
  > **Deps**: T029 | **Done when**: Creates draft invoice in Odoo; does not set state to "posted"; dry-run returns mock invoice_id
  > **Test (dry)**: DRY_RUN=true → `{dry_run: true, invoice_id: "MOCK_001", status: "draft"}`
  > **Dry run**: Return mock draft invoice

- [X] T032 [P] [BUILD] [US4] Add `post_invoice` tool (marks invoice as posted — irreversible; requires `approval_id` parameter)
  > **Inputs**: `invoice_id`, `approval_id` | **Outputs**: `{invoice_id, state: "posted"}`
  > **Deps**: T031 | **Done when**: Tool rejects calls without approval_id; with approval_id and DRY_RUN=true returns mock posted state; counts against payment rate limit (3/hour)
  > **Test**: Call without approval_id → `{error: "APPROVAL_REQUIRED", retryable: false}`
  > **Dry run**: `{dry_run: true, invoice_id: "MOCK_001", state: "posted"}`

- [X] T033 [P] [BUILD] [US4] Add `create_transaction`, `sync_transaction`, and `list_invoices` tools to `mcp-servers/odoo-mcp/server.py`
  > **Inputs**: per contracts/odoo-mcp.md | **Outputs**: per contracts/odoo-mcp.md
  > **Deps**: T029 | **Done when**: All three tools registered; dry-run returns correct mock structures per contract
  > **Test (dry)**: Each tool called with DRY_RUN=true returns matching mock response
  > **Dry run**: Per-tool mock responses as defined in contracts/odoo-mcp.md

- [X] T034 [BUILD] Register `odoo-mcp` in `.mcp.json` at project root
  > **Inputs**: `.mcp.json` | **Outputs**: odoo-mcp entry in `.mcp.json`
  > **Deps**: T033 | **Done when**: `.mcp.json` contains an `odoo-mcp` entry with `command: "python"` and `args: ["mcp-servers/odoo-mcp/server.py"]`; `python mcp-servers/odoo-mcp/server.py` starts and attempts authentication (or returns mock uid=1 in DRY_RUN)
  > **Test**: Read `.mcp.json`; verify odoo-mcp entry exists; start server manually and confirm startup log
  > **Dry run**: N/A

🧪 **Phase 4c Gate**: All Odoo MCP tools respond correctly with `DRY_RUN=true`. Proceed to Checkpoint 4 for live credentials.

---

## Phase 5: Agent Skills Verification & CEO Briefing Build

**Purpose**: Verify all existing Silver-tier skills work correctly, then build the missing `ceo-briefing` skill.

**User Stories covered**: US1 (process-needs-action), US2 (HITL), US5 (CEO briefing), US7 (reasoning-loop)

### Verify Existing Skills

- [ ] T035 [P] [VERIFY] [US1] Verify `process-needs-action` skill: drop a test `EMAIL_*.md` into `Needs_Action/`; verify `Plans/PLAN_*.md` created and task moved to `Done/`
  > **Inputs**: `Needs_Action/EMAIL_test.md` (manually created) | **Outputs**: `Plans/PLAN_*.md`, task in `Done/`, `Dashboard.md` updated, audit log entry
  > **Deps**: T004 | **Done when**: Skill runs without error; plan file exists; source task is in Done/; Dashboard.md counts reflect change
  > **Test**: `claude "Run the process-needs-action skill"` after dropping test file
  > **Dry run**: `DRY_RUN=true` — skill writes plan but does not send any emails

- [ ] T036 [P] [VERIFY] [US2] Verify HITL flow: drop a `FINANCE_test.md` (payment type); verify `APPROVAL_*.md` created in `Pending_Approval/`; move to `Approved/`; verify `execute-plan` executes (DRY_RUN)
  > **Inputs**: `Needs_Action/FINANCE_test.md` with payment action | **Outputs**: `Pending_Approval/APPROVAL_*.md` → moves to `Done/` after approval
  > **Deps**: T035 | **Done when**: No payment MCP call made until approval file moved to Approved/; after move, execute-plan runs (DRY_RUN), logs entry, moves task to Done/
  > **Test**: Manual file-move approval → verify execute-plan log entry shows `dry_run: true`
  > **Dry run**: `DRY_RUN=true` throughout

- [ ] T037 [P] [VERIFY] [US7] Verify `reasoning-loop` skill: run `/ralph-loop "Process Needs_Action and output TASK_COMPLETE"` → verify loop starts, runs, outputs `<promise>TASK_COMPLETE</promise>`, and stop hook allows exit
  > **Inputs**: `scripts/ralph_loop.py`, `scripts/check_loop_complete.py`, `.claude/settings.json` | **Outputs**: loop completes within 2 iterations; Claude exits after TASK_COMPLETE
  > **Deps**: T004 | **Done when**: Stop hook is registered in `.claude/settings.json`; loop driver detects completion token; Claude exits cleanly
  > **Test**: `python scripts/ralph_loop.py "Output <promise>TASK_COMPLETE</promise> immediately" --max-iterations 3` — verify exits after 1 iteration
  > **Dry run**: N/A — loop itself is not an external action

- [ ] T038 [VERIFY] Confirm `scripts/check_loop_complete.py` is registered in `.claude/settings.json` as a Stop hook
  > **Inputs**: `.claude/settings.json` | **Outputs**: confirmed hook entry
  > **Deps**: T037 | **Done when**: `grep "check_loop_complete" .claude/settings.json` returns match; if missing, add per quickstart.md Section 5
  > **Test**: Grep check
  > **Dry run**: N/A

### Build CEO Briefing Skill

- [X] T039 [BUILD] [US5] Create `.claude/skills/ceo-briefing/SKILL.md` using the skill-creator skill
  > **Inputs**: `spec.md` FR-025–027, `contracts/`, `data-model.md` CEO Briefing schema, `Business_Goals.md` format, `Bank_Transactions.md` format | **Outputs**: `.claude/skills/ceo-briefing/SKILL.md` with complete skill definition
  > **Deps**: T035 | **Done when**: SKILL.md exists; frontmatter complete; skill reads `Business_Goals.md` + `Bank_Transactions.md` + `Done/` folder + `Needs_Action/` for stalled tasks; writes `Briefings/YYYY-MM-DD_Monday_Briefing.md` with all required sections
  > **Test**: `claude "Use the skill-creator skill to create the ceo-briefing skill"` then `claude "Run the ceo-briefing skill"` with mock data → verify `Briefings/*.md` created with correct sections
  > **Dry run**: `DRY_RUN=true` — briefing still writes the file (it's a local write, not an external action) but does not trigger any MCP calls

- [X] T040 [BUILD] [US5] Create mock `Business_Goals.md` and `Bank_Transactions.md` with realistic sample data for CEO briefing tests
  > **Inputs**: spec.md CEO Briefing schema, hackathon document Business_Goals template | **Outputs**: `AI_Employee_Vault/Business_Goals.md` (targets, KPIs, subscription audit rules), `AI_Employee_Vault/Bank_Transactions.md` (8–10 sample transactions including 1 subscription, 1 client payment, 1 late fee)
  > **Deps**: T039 | **Done when**: Both files exist with valid frontmatter and content; ceo-briefing skill reads them without parsing errors
  > **Test**: `claude "Run the ceo-briefing skill"` — briefing mentions mock revenue figure and at least one subscription in cost optimisation
  > **Dry run**: N/A — local file creation

- [ ] T041 [BUILD] [US5] Verify CEO Briefing output contains ALL required sections: Executive Summary, Revenue Summary (table), Completed This Week, Bottlenecks, Cost Optimisation Suggestions, Upcoming Deadlines, Social Media Summary
  > **Inputs**: `Briefings/YYYY-MM-DD_Monday_Briefing.md` | **Outputs**: validation checklist
  > **Deps**: T040 | **Done when**: Each section heading exists in generated briefing; Revenue Summary table has weekly + MTD rows; Social Media Summary table present (even if with "No posts this week" values)
  > **Test**: `grep -c "## " $VAULT_PATH/Briefings/*.md` returns ≥ 7; spot-check each section
  > **Dry run**: N/A

🧪 **Phase 5 Gate**: All skill verifications pass; CEO briefing generated with all sections from mock data. If any skill test fails, fix before proceeding.

---

## 🔐 Checkpoint 4: Odoo Credentials

**⛔ STOP — Human action required.**

- [ ] T042 [HUMAN] Verify Odoo Community 19+ is installed and reachable; populate `.env` with `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`
  > **Done when**: `curl $ODOO_URL/web/session/authenticate` returns a valid JSON response; `python mcp-servers/odoo-mcp/server.py` starts and logs authenticated session
  > **Test (dry)**: `DRY_RUN=false claude "Use odoo-mcp get_customer name='Test'"` → returns empty list or test customer (not an auth error)

✅ **Checkpoint 4 cleared** — proceed to Phase 6.

---

## Phase 6: Odoo Integration (Live)

**Purpose**: Validate the full Finance Watcher → FINANCE_*.md → Odoo MCP transaction sync pipeline end-to-end. Requires Checkpoint 4 to be cleared.

**User Story covered**: US4

**Independent Test**: Inject a mock transaction into the bank CSV; within 10 minutes it should appear in `Bank_Transactions.md`, an Odoo transaction record should be created, and the next CEO briefing should include this transaction in the Revenue Summary.

- [ ] T043 [US4] Run Odoo invoice creation dry run: `claude "Use odoo-mcp create_invoice for customer_id=1 with line_items=[{description: 'Test Service', quantity: 1, unit_price: 100}] due_date=2026-04-01"` with `DRY_RUN=true`
  > **Inputs**: Odoo MCP, DRY_RUN=true | **Outputs**: `{dry_run: true, invoice_id: "MOCK_001", status: "draft"}`
  > **Deps**: T034, T042 | **Done when**: Dry-run response received; no invoice created in Odoo
  > **Test**: Verify Odoo invoice list is unchanged after dry run
  > **Dry run**: This task IS the dry run

- [ ] T044 [US4] Run Odoo invoice creation live: create a real draft invoice in Odoo; verify draft state (not posted)
  > **Inputs**: `DRY_RUN=false`, Odoo MCP `create_invoice` | **Outputs**: real invoice_id in Odoo with state "draft"
  > **Deps**: T043 | **Done when**: Invoice appears in Odoo UI with draft state; invoice_id returned in MCP response
  > **Test**: Log into Odoo → Accounting → Invoices → verify draft invoice exists with correct line items
  > **Dry run**: T043 was the dry run

- [ ] T045 [US4] Test full transaction sync pipeline: inject mock transaction to bank CSV → finance watcher creates FINANCE_*.md → process-needs-action creates plan → execute-plan calls `odoo-mcp create_transaction` → verify Odoo record created
  > **Inputs**: mock bank CSV entry, `DRY_RUN=false` (controlled test) | **Outputs**: Odoo transaction record; `Bank_Transactions.md` updated; task in Done/; audit log entry
  > **Deps**: T044 | **Done when**: All 5 steps complete without error; Odoo shows new transaction; audit log shows `action_type: odoo_sync`, `result: success`
  > **Test**: End-to-end manual trace through all vault folders after pipeline completes
  > **Dry run**: Run T043 first with DRY_RUN=true to confirm path; then run live

- [ ] T046 [US4] Verify CEO briefing includes Odoo transaction data: run ceo-briefing skill after T045; verify Revenue Summary reflects transaction amount
  > **Inputs**: `Briefings/` folder | **Outputs**: briefing with transaction reflected in Revenue Summary
  > **Deps**: T045 | **Done when**: Briefing Revenue Summary shows correct weekly revenue including the test transaction
  > **Test**: `grep "Test transaction" $VAULT_PATH/Briefings/*.md` or check Revenue row
  > **Dry run**: N/A

🧪 **Phase 6 Gate**: Transaction sync pipeline runs end-to-end without error; Odoo record created; briefing reflects transaction.

---

## Phase 7: Social Automation

**Purpose**: Validate the full social post → approval → publish → summary pipeline for all four platforms.

**User Stories covered**: US6, US6b

**Independent Test**: Trigger `linkedin-post` skill; verify `APPROVAL_*.md` created; approve it; verify `post_linkedin` called (DRY_RUN) and `get_post_summary` called; verify next CEO briefing contains Social Media Summary.

- [ ] T047 [US6] Dry-run full LinkedIn post pipeline: `claude "Run the linkedin-post skill"` → verify `APPROVAL_*.md` in `Pending_Approval/` with `DRY_RUN=true`
  > **Inputs**: `Business_Goals.md`, `Company_Handbook.md` | **Outputs**: `Plans/PLAN_LINKEDIN_*.md`, `Pending_Approval/APPROVAL_LINKEDIN_*.md`
  > **Deps**: T027, T039 | **Done when**: Both files created; no MCP call made; approval file has `action_type: social_post`
  > **Test**: `ls $VAULT_PATH/Pending_Approval/APPROVAL_LINKEDIN_*`
  > **Dry run**: This task IS the dry-run step

- [X] T048 [US6] Update `execute-plan` skill to handle `social_post` action type: call `social-mcp post_<platform>` with content and approval_id; then call `get_post_summary`; log both as audit entries
  > **Inputs**: `.claude/skills/execute-plan/SKILL.md`, social-mcp contract | **Outputs**: updated execute-plan skill that handles social_post; post published; summary retrieved and logged
  > **Deps**: T047 | **Done when**: execute-plan processes `action_type: social_post`; calls correct `post_<platform>` tool; immediately calls `get_post_summary`; writes audit entries for both; moves task to Done/
  > **Test**: Approve T047 APPROVAL file → verify execute-plan invokes post_linkedin (DRY_RUN=true) and get_post_summary (mock) → Done/ has task; Logs/ has two entries (post + summary)
  > **Dry run**: `DRY_RUN=true` — post_linkedin returns dry-run response; get_post_summary returns mock engagement

- [ ] T049 [US6] Live LinkedIn post test: with `DRY_RUN=false`, post one real lead-generation post to LinkedIn; verify post appears and summary is logged
  > **Inputs**: Valid LINKEDIN_ACCESS_TOKEN | **Outputs**: real LinkedIn post; `{post_id, url}` in audit log; summary entry with engagement data (or null)
  > **Deps**: T048 | **Done when**: Post visible on LinkedIn profile; audit log has `action_type: linkedin_post result: success`; `get_post_summary` entry present
  > **Test**: Check LinkedIn profile manually; verify Logs/ entry
  > **Dry run**: T047–T048 were the dry runs

- [ ] T050 [P] [US6] Dry-run Facebook post flow with `DRY_RUN=true`; verify `post_facebook` dry-run response and summary call
  > **Deps**: T048 | **Done when**: dry-run response received; no real post
  > **Test**: Same pattern as T047–T048 but for Facebook
  > **Dry run**: This task IS the dry run

- [ ] T051 [P] [US6] Dry-run Instagram post flow with `DRY_RUN=true`
  > **Deps**: T048 | **Done when**: dry-run response received
  > **Test**: Same pattern for Instagram
  > **Dry run**: This task IS the dry run

- [ ] T052 [P] [US6] Dry-run Twitter/X post flow with `DRY_RUN=true`; verify 280-char enforcement
  > **Deps**: T048 | **Done when**: dry-run response; 281-char content returns validation error
  > **Test**: Post 281-char content → verify error; post 280-char content DRY_RUN=true → dry-run response
  > **Dry run**: This task IS the dry run

- [ ] T053 [US6b] Verify Social Media Summary appears in CEO briefing: run ceo-briefing skill after T049 live post; verify Social Media Summary table is populated for LinkedIn
  > **Inputs**: `Briefings/`, post audit log | **Outputs**: briefing with LinkedIn row in Social Media Summary
  > **Deps**: T049 | **Done when**: Briefing's Social Media Summary table shows LinkedIn row with post count ≥ 1 and engagement data or "N/A"
  > **Test**: `grep "LinkedIn" $VAULT_PATH/Briefings/*.md`
  > **Dry run**: N/A

🧪 **Phase 7 Gate**: LinkedIn live post succeeds; all other platform dry runs pass; Social Media Summary appears in briefing.

---

## Phase 8: CEO Briefing (Scheduled + Full Data)

**Purpose**: Wire the CEO briefing to the orchestrator's Sunday 23:00 cron; validate with full mock data representing a realistic business week.

**User Story covered**: US5

- [ ] T054 [US5] Run ceo-briefing skill with full realistic mock data: 5 completed tasks in Done/, 2 stalled tasks in Needs_Action/ (>24 h old), 1 subscription charge in Bank_Transactions.md, 1 real Odoo transaction from Phase 6
  > **Inputs**: populated vault with realistic data | **Outputs**: `Briefings/YYYY-MM-DD_Monday_Briefing.md` with all 7 sections populated
  > **Deps**: T046, T053 | **Done when**: All 7 briefing sections present; Bottlenecks section lists the 2 stalled tasks; Cost Optimisation flags the subscription; Social Media Summary shows LinkedIn post
  > **Test**: `wc -l $VAULT_PATH/Briefings/*.md` > 50 lines; spot-check each section; verify no "N/A" in Revenue row (mock data has transactions)
  > **Dry run**: N/A — briefing is a local write

- [ ] T055 [US5] Verify clean briefing (no anomalies): empty Done/, no stalled tasks, no suspicious subscriptions → briefing still generates with "No issues identified" notes
  > **Inputs**: clean vault state | **Outputs**: briefing file with all sections, clean-state notes
  > **Deps**: T054 | **Done when**: Briefing file created; sections say "No completed tasks this week" etc.; briefing is NOT empty or skipped
  > **Test**: Run briefing on clean vault; verify file exists with correct date and all headings
  > **Dry run**: N/A

- [ ] T056 [US5] Trigger orchestrator cron for briefing: temporarily set briefing schedule to 1 minute from now; verify orchestrator fires ceo-briefing skill; restore to Sunday 23:00
  > **Inputs**: `orchestrator.py` schedule, `schedule` library | **Outputs**: briefing auto-generated without manual trigger
  > **Deps**: T055 | **Done when**: Orchestrator fires ceo-briefing without manual `claude` command; briefing file created at expected path
  > **Test**: Set schedule to `schedule.every(1).minutes.do(run_ceo_briefing)` temporarily; wait 65 s; verify briefing created; restore to `schedule.every().sunday.at("23:00").do(...)`
  > **Dry run**: `DRY_RUN=true` for cron-triggered run

🧪 **Phase 8 Gate**: CEO briefing generates correctly from realistic data and from clean state; cron trigger verified.

---

## Phase 9: Ralph Wiggum Loop Integration

**Purpose**: Verify the Ralph loop (already built) integrates correctly with the new Gold tier skills — specifically the multi-step Odoo reconciliation flow.

**User Story covered**: US7

- [ ] T057 [US7] Verify stop hook surfaces prior iteration output: run a deliberately incomplete multi-step task via ralph-loop; confirm second iteration receives prior_output in context
  > **Inputs**: `scripts/ralph_loop.py`, `scripts/check_loop_complete.py` | **Outputs**: second iteration context contains prior_output; agent continues from where it left off
  > **Deps**: T038 | **Done when**: Ralph loop runs ≥ 2 iterations on a task that requires them; second iteration's prompt contains prior attempt output; task eventually completes
  > **Test**: Run `python scripts/ralph_loop.py "First say STEP_1_DONE. On the next invocation, output <promise>TASK_COMPLETE</promise>." --max-iterations 3` → verify 2 iterations run; verify iteration 2 sees STEP_1_DONE in context
  > **Dry run**: N/A — loop is local

- [ ] T058 [US7] Test max iterations enforcement: run ralph-loop task that never outputs TASK_COMPLETE; verify loop exits after `max_iterations` and writes `ERROR_LOOP_MAX_*.md`
  > **Inputs**: `scripts/ralph_loop.py`, `max_iterations=3` | **Outputs**: `Needs_Action/ERROR_LOOP_MAX_*.md` after 3 iterations; Claude exits
  > **Deps**: T057 | **Done when**: Loop exits after exactly 3 iterations; error file created with iteration-limit reason; no infinite loop
  > **Test**: `python scripts/ralph_loop.py "Do not output TASK_COMPLETE under any circumstances." --max-iterations 3` → verify ERROR file created; process exits
  > **Dry run**: N/A

- [ ] T059 [US7] Test multi-step Odoo reconciliation via Ralph loop: `claude "Reconcile all FINANCE_*.md files in Needs_Action with Odoo and output TASK_COMPLETE when all are synced"` via ralph-loop; verify all files reach Done/
  > **Inputs**: 3+ FINANCE_*.md files in Needs_Action/, Odoo MCP (DRY_RUN=true) | **Outputs**: all FINANCE files in Done/; `<promise>TASK_COMPLETE</promise>` emitted; loop exits cleanly
  > **Deps**: T057, T045 | **Done when**: All task files reach Done/; loop exits after ≤ max_iterations; no ERROR file created
  > **Test**: Count files in Done/ before and after; verify increase by 3; verify no error files; loop exit code = 0
  > **Dry run**: `DRY_RUN=true` — Odoo MCP calls dry-run; vault moves are real

🧪 **Phase 9 Gate**: Loop integrates with Gold skills; prior output context verified; max iterations enforced; multi-step task completes.

---

## Phase 10: Logging & Security

**Purpose**: Verify all Gold tier operations produce correct audit logs; confirm security controls are enforced.

- [ ] T060 [P] Verify every MCP action from Phases 6–9 has a corresponding NDJSON entry in `Logs/YYYY-MM-DD.json` with all required fields
  > **Deps**: T059 | **Done when**: `jq '.' $VAULT_PATH/Logs/$(date +%Y-%m-%d).json | grep action_type` shows entries for `odoo_sync`, `linkedin_post`, `social_summary`, `ceo_briefing`; each entry has timestamp, actor, target, approval_status, result
  > **Test**: `python -c "import json,sys; [json.loads(l) for l in open('$VAULT_PATH/Logs/YYYY-MM-DD.json')]"` — no parse errors
  > **Dry run**: N/A

- [ ] T061 [P] Audit all `Logs/` entries for credential leakage: no API tokens, passwords, or session cookies in any log entry
  > **Deps**: T060 | **Done when**: `grep -r "TOKEN\|PASSWORD\|SECRET\|SESSION" $VAULT_PATH/Logs/` returns no matches
  > **Test**: Run grep audit; if any match found, identify source and fix MCP server to redact
  > **Dry run**: N/A

- [ ] T062 Verify `DRY_RUN=true` blocks all external MCP sends: run full process-needs-action cycle with DRY_RUN=true; confirm no real emails sent, no real posts published, no real Odoo records created
  > **Deps**: T060 | **Done when**: Audit log shows all actions with `"dry_run": true`; no new records in Odoo; no emails in sent folder; no LinkedIn posts
  > **Test**: Check Gmail sent folder + Odoo invoice list + LinkedIn profile after DRY_RUN=true cycle
  > **Dry run**: This task IS the dry-run validation

- [ ] T063 Verify rate limit enforcement: send 11 emails via email-mcp in DRY_RUN=true mode; verify 11th call returns `RATE_LIMIT_EXCEEDED`
  > **Deps**: T060 | **Done when**: 10 successful calls; 11th returns `{error: "RATE_LIMIT_EXCEEDED", retryable: false}`
  > **Test**: Script 11 sequential send_email dry-run calls; verify error on 11th
  > **Dry run**: DRY_RUN=true throughout (no real emails sent)

- [ ] T064 Verify payment rate limit: attempt 4 `post_invoice` calls (DRY_RUN=true); verify 4th returns `RATE_LIMIT_EXCEEDED`
  > **Deps**: T060 | **Done when**: 3 successful calls (with valid approval_ids); 4th returns rate limit error
  > **Test**: Script 4 sequential post_invoice calls; verify error on 4th
  > **Dry run**: DRY_RUN=true throughout

- [ ] T065 Verify Dashboard.md single-writer rule and update latency: confirm no skill other than process-needs-action writes to Dashboard.md; verify Dashboard updates within 30 s of a state transition (NFR-007)
  > **Deps**: T039 | **Done when**: (a) Only process-needs-action SKILL.md contains Dashboard.md write instructions; all other skills read or do not touch it. (b) Timing test: trigger a state transition (drop a task into Needs_Action/ and run process-needs-action); record `Dashboard.md` mtime before and after; assert elapsed time ≤ 30 s
  > **Test**: `grep -r "Dashboard.md" .claude/skills/` — only process-needs-action references a write; then: record timestamp → run process-needs-action → `stat -c %Y $VAULT_PATH/Dashboard.md` → assert within 30 s of trigger
  > **Dry run**: N/A

🧪 **Phase 10 Gate**: Audit logs complete; no credential leakage; DRY_RUN blocks verified; rate limits enforced.

---

## Phase 11: Error Handling & Graceful Degradation

**Purpose**: Simulate each failure mode from the spec and verify the system handles it correctly without data loss.

- [ ] T066 Test email queue (FR-041): disable email-mcp (stop the process); trigger an email send via execute-plan; verify email queued in `scripts/email_outbox_queue.json`; re-enable email-mcp; verify `flush_queue` sends queued email
  > **Deps**: T019, T020 | **Done when**: Email queued when MCP down; delivered when MCP restored; no email lost; audit log shows `queued` then `sent`
  > **Test**: `pkill -f email-mcp` → trigger send → check queue → restart email-mcp → `claude "Use email-mcp to flush_queue"` → verify queue empty
  > **Dry run**: DRY_RUN=true throughout (flush_queue dry run logs "would send 1 email")

- [ ] T067 Test watchers continue without Claude (FR-042): stop Claude process; trigger a Gmail email and a file drop; wait 2 minutes; restart Claude; verify both `Needs_Action/EMAIL_*.md` and `Needs_Action/FILE_*.md` exist and get processed
  > **Deps**: T007, T009 | **Done when**: Events captured while Claude is offline; queue processed automatically on Claude restart; no events lost
  > **Test**: Stop claude → trigger events → wait → restart → run process-needs-action → verify Done/ has both tasks
  > **Dry run**: DRY_RUN=true for Claude processing after restart

- [ ] T068 Test temp folder fallback (FR-043): set `VAULT_PATH` to a temporarily unavailable path; drop a file to `Inbox/`; verify output written to `VAULT_TEMP_PATH`; restore vault path; verify file synced to correct vault location
  > **Deps**: T017 | **Done when**: No data lost during vault unavailability; FILE_*.md synced to Needs_Action/ on restoration
  > **Test**: `mv $VAULT_PATH $VAULT_PATH.bak` → drop file → wait → `mv $VAULT_PATH.bak $VAULT_PATH` → wait 65 s → verify FILE_*.md in Needs_Action/
  > **Dry run**: N/A — this test IS the simulation

- [ ] T069 Test watchdog auto-restart (FR-037): kill `gmail_watcher` subprocess; verify orchestrator restarts it within 60 seconds; verify audit log entry `actor: watchdog`; kill 3× in one hour; verify ERROR_WATCHDOG_*.md written on 4th kill
  > **Deps**: T014 | **Done when**: First 3 kills result in auto-restart within 60 s; 4th kill writes error file and stops auto-restart
  > **Test**: `kill $(cat /tmp/gmail_watcher.pid)` × 4 in quick succession; watch orchestrator log; check Needs_Action/ for ERROR_WATCHDOG_*.md
  > **Dry run**: N/A — process kill test

- [ ] T070 Test transient retry (FR-035): configure mock Odoo endpoint to fail 2× then succeed; run `create_transaction`; verify 3 attempts made with exponential backoff; verify success on 3rd attempt
  > **Deps**: T033 | **Done when**: Odoo MCP retries with 1 s, 2 s delays; succeeds on 3rd attempt; audit log shows `result: success`; no ERROR_*.md written
  > **Test**: Mock server returning 503 twice then 200; run transaction sync; verify timing between attempts (≥ 1 s, ≥ 2 s)
  > **Dry run**: N/A — retry test uses mock server

- [ ] T071 Test banking no-retry (FR-021): fail an approved `post_invoice` call once; verify ERROR_BANK_*.md written; verify no auto-retry; require fresh APPROVAL_*.md to retry
  > **Deps**: T032 | **Done when**: Failed post_invoice writes `ERROR_BANK_*.md`; no automatic retry attempt; original approval file is not reused; new approval required
  > **Test**: Mock Odoo returning 500 on post_invoice; verify error file; attempt to rerun using same approval_id → system rejects (approval already consumed)
  > **Dry run**: N/A

- [ ] T072 Test WhatsApp session expiry (FR-002): invalidate the session cookie; verify watcher attempts one re-auth; on failure writes `ERROR_WHATSAPP_SESSION.md` and pauses; does not open a second browser session
  > **Deps**: T008 | **Done when**: Single re-auth attempt logged; ERROR file written on failure; only 1 browser process at all times; watcher state = paused
  > **Test**: Delete session cookies file; wait for watcher poll cycle; verify single re-auth attempt in log; verify ERROR file; verify `ps aux | grep playwright` shows ≤ 1 process
  > **Dry run**: N/A

🧪 **Phase 11 Gate**: All 7 failure scenarios handled correctly without data loss. Proceed to Final Validation.

---

## Final Validation: End-to-End System Test

**Purpose**: Run the complete Gold tier system under realistic conditions, first fully in DRY_RUN mode, then with a controlled live test.

- [ ] T073 Full system DRY_RUN smoke test: start orchestrator with all watchers; trigger events on all 4 channels (email, WhatsApp keyword, file drop, mock bank transaction); run `process-needs-action` and `execute-plan` on all resulting tasks; verify all end in `Done/` with audit entries; `DRY_RUN=true` throughout; also inject one malformed task file to verify FR-038 (silent-fail prevention)
  > **Deps**: All Phase 1–11 tasks complete | **Done when**: (1) 4 tasks created → 4 tasks reach Done/; all audit log entries present; Dashboard.md shows 0 in Needs_Action, 4 in Done; no unexpected ERROR_*.md files. (2) Malformed task file (missing required frontmatter fields) produces `Needs_Action/ERROR_*.md` within 30 s — system never silently swallows the error (FR-038)
  > **Test**: Run full cycle; check Done/ count = 4; check Logs/ for all 4 action types; check Dashboard.md. Then drop a task file with empty/invalid YAML frontmatter; wait 30 s; verify `Needs_Action/ERROR_*.md` exists with error description
  > **Dry run**: This task IS the dry-run validation

- [ ] T074 1-hour always-on DRY_RUN stability test: start orchestrator; leave running for 60 minutes; verify watcher stability and watchdog behaviour (NFR-001 acceptance test)
  > **Deps**: T073 | **Done when**: All watcher processes alive after 60 min (PIDs unchanged); any simulated watcher kill is recovered within 60 s by watchdog (NFR-002); no unprocessed items remain in Needs_Action/ for >5 min without a Claude cycle; Dashboard.md mtime has updated at least once during the run
  > **Test**: Record watcher PIDs at t=0; at t=30 min, kill one watcher and verify it restarts within 60 s; at t=60 min verify all PIDs are alive (either original or post-restart); check Logs/ for watchdog restart entry; verify Dashboard.md was updated
  > **Dry run**: DRY_RUN=true throughout

- [ ] T075 Controlled live execution: with `DRY_RUN=false`, send 1 real email to known contact; verify auto-reply sent and logged; approve 1 pending Odoo invoice (from Phase 6 draft); verify invoice posted; trigger ceo-briefing manually; verify briefing covers both live events
  > **Deps**: T074 | **Done when**: Email reply received by known contact; invoice status in Odoo = "posted"; CEO briefing includes both events; all actions in Logs/ with `result: success`
  > **Test**: Check Gmail sent folder; check Odoo invoice status; read Briefings/*.md
  > **Dry run**: T073–T074 were the dry runs

- [X] T076 Architecture Documentation (NFR-021): write `ARCHITECTURE.md` at repo root covering: all system components and interactions, rationale for 3+ key design decisions (MCP stdio transport, Python for all MCPs, file-based email queue), known limitations and lessons learned
  > **Deps**: T075 | **Done when**: `ARCHITECTURE.md` exists; covers all components in plan.md; ≥ 3 design rationale sections; ≥ 3 lessons learned; linked from README
  > **Test**: Read ARCHITECTURE.md; verify all components from plan.md architecture diagram are mentioned
  > **Dry run**: N/A

🧪 **Final Gate**: T073–T076 all pass. System is Gold tier complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** (T001–T005): No dependencies — start immediately
- **Checkpoint 1** (T006): Depends on Phase 1 gate ✅
- **Phase 2** (T007–T012, T010b, T012b): Depends on Checkpoint 1; T010b depends on T010; T012b depends on T012
- **Checkpoint 2** (T013): Depends on T007 (Gmail watcher verified)
- **Phase 3** (T014–T017): Depends on Phase 2 gate
- **Phase 4a** (T018–T020): Can start in parallel with Phase 3 (different files)
- **Phase 4b** (T021–T027): Depends on Phase 3 complete (needs orchestrator stable)
- **Checkpoint 3** (T028): Depends on Phase 4b gate
- **Phase 4c** (T029–T034): Can start in parallel with Phase 5 skills verification
- **Phase 5** (T035–T041): Depends on Phase 4a complete; T039–T041 (CEO briefing) also depend on T034
- **Checkpoint 4** (T042): Depends on T034 (odoo-mcp registered)
- **Phase 6** (T043–T046): Depends on Checkpoint 4
- **Phase 7** (T047–T053): Depends on Checkpoint 3 + T039 (ceo-briefing skill exists)
- **Phase 8** (T054–T056): Depends on Phase 6 + Phase 7
- **Phase 9** (T057–T059): Depends on Phase 6 (Odoo tasks for reconciliation test)
- **Phase 10** (T060–T065): Depends on Phases 6–9
- **Phase 11** (T066–T072): Depends on Phase 10
- **Final Validation** (T073–T076): Depends on all Phase 11 gates

### User Story Completion Order

| User Story | Primary Phases | Unblocked After |
|---|---|---|
| US1 — Email Triage (P1) | Phase 2 (T007), Phase 5 (T035) | Checkpoint 2 |
| US2 — HITL Approval (P1) | Phase 3, Phase 5 (T036) | Phase 2 gate |
| US3 — WhatsApp (P2) | Phase 2 (T008) | Checkpoint 1 |
| US4 — Finance + Odoo (P2) | Phase 2 (T010–T012), Phase 4c (T029–T034), Phase 6 | Checkpoint 4 |
| US5 — CEO Briefing (P2) | Phase 5 (T039–T041), Phase 8 | Phase 6 + Phase 7 |
| US6/US6b — Social (P3) | Phase 4b (T021–T027), Phase 7 | Checkpoint 3 |
| US7 — Ralph Loop (P3) | Phase 9 (T057–T059) | Phase 6 |

### Parallel Opportunities

```
After Phase 1 gate:
  [P] T007 (Gmail verify) + T008 (WhatsApp verify) + T009 (Filesystem verify)
  [P] T003 (MCP verify) + T004 (Claude vault test)

After Checkpoint 1:
  Phase 3 (Orchestrator) ← can run in parallel with Phase 4a (Email MCP extensions)

After Phase 3 gate:
  [P] T022 post_linkedin + T023 post_facebook + T024 post_instagram + T025 post_twitter
  [P] T030 get_customer + T031 create_invoice + T032 post_invoice + T033 create_transaction

After Checkpoint 3:
  Phase 4c (Odoo MCP build) ← can run in parallel with Phase 5 skill verification
```

---

## Implementation Strategy

### MVP Scope (US1 + US2 only)

1. Complete Phase 1 (T001–T005)
2. Checkpoint 1 (T006)
3. Phase 2: T007 only (Gmail watcher verify)
4. Phase 3: T014 only (watchdog)
5. Phase 4a: T018–T020 (email queue)
6. Phase 5: T035–T036 (process-needs-action + HITL verify)
7. **STOP**: Validate email triage + approval flow end-to-end
8. Demo: Email → Needs_Action → Plan → Approval → execute-plan → Done

### Full Gold Delivery

Complete all phases in dependency order. Estimated task count: **76 tasks** across 11 phases + 4 checkpoints + final validation.

---

## Notes

- `[P]` tasks in the same phase have no shared file dependencies and can run in parallel
- `[VERIFY]` tasks confirm existing Silver components — fix before proceeding if they fail
- `[BUILD]` tasks are new Gold tier additions
- Every phase ends with a 🧪 gate — do NOT proceed if the gate fails
- Every 🔐 checkpoint requires human action — the system cannot continue autonomously
- `DRY_RUN=true` is mandatory for all MCP calls until the Final Validation phase
- Architecture documentation (T076) must be written before declaring Gold tier complete
