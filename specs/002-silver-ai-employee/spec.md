# Feature Specification: Silver Tier Functional Assistant

**Feature Branch**: `002-silver-ai-employee`
**Created**: 2026-03-13
**Status**: Draft
**Input**: User description: "Create a Silver Tier Functional Assistant built on top of the Bronze Tier Obsidian automation system."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Multi-Channel Event Capture (Priority: P1)

A business owner has Gmail and WhatsApp generating work throughout the day. Without Silver Tier, they must manually check each channel. With Silver Tier, every new email and WhatsApp message is automatically detected and converted into a structured task in `Needs_Action/` — no manual checking required.

**Why this priority**: The entire system is worthless if events from the outside world don't reach the vault. This perception layer feeds everything else and must work reliably before any downstream processing can be tested.

**Independent Test**: Start both the Gmail watcher and WhatsApp watcher. Send a test email and a test WhatsApp message. Within 5 minutes (email) and 60 seconds (WhatsApp), two `.md` task files appear in `Needs_Action/` with valid YAML frontmatter (type, source, sender, received timestamp, priority, status).

**Acceptance Scenarios**:

1. **Given** the Gmail watcher is running, **When** a new email arrives in the monitored inbox, **Then** a task `.md` file appears in `Needs_Action/` within 5 minutes containing the sender, subject, and body summary.
2. **Given** the WhatsApp watcher is running, **When** a new WhatsApp message is received, **Then** a task `.md` file appears in `Needs_Action/` within 60 seconds containing the sender and message text.
3. **Given** a message was already processed, **When** either watcher restarts, **Then** no duplicate task file is created for that same message.
4. **Given** a watcher encounters a non-fatal error (e.g. network timeout), **Then** an `ERROR_*.md` file is created in `Needs_Action/` and the watcher continues running without crashing.

---

### User Story 2 — Claude Creates Structured Plans with Approval Gates (Priority: P2)

The business owner invokes Claude to process the task queue. Claude reads each task, reasons about it against `Company_Handbook.md` rules, and produces a structured `Plans/PLAN_*.md`. For tasks requiring external action (sending an email reply), the plan is marked `Awaiting Approval` so the owner reviews it before anything is sent.

**Why this priority**: Planning is the core AI value-add. Without structured plans with approval gates, the system is just a file aggregator. Approval gates keep the owner in control of all outbound actions.

**Independent Test**: Place a test email task in `Needs_Action/` (type: email, priority: high). Invoke `process-needs-action`. Confirm `Plans/PLAN_*.md` exists with Summary, Analysis, and Actions sections, and the reply action is marked `Awaiting Approval`.

**Acceptance Scenarios**:

1. **Given** a task of type `email` in `Needs_Action/`, **When** the planning skill runs, **Then** a plan is created in `Plans/` with a drafted reply and an `Awaiting Approval` status marker.
2. **Given** a task of type `whatsapp` in `Needs_Action/`, **When** the planning skill runs, **Then** a plan is created with a drafted reply and an `Awaiting Approval` marker.
3. **Given** a task of type `file_drop` in `Needs_Action/`, **When** the planning skill runs, **Then** a plan is created with a summary and safe actions only (no approval required).
4. **Given** a plan is marked `Awaiting Approval` and an `APPROVAL_*.md` is in `Pending_Approval/`, **When** the owner moves that file to `Approved/`, **Then** the orchestrator detects the move and triggers execution via the MCP server.

---

### User Story 3 — LinkedIn Lead-Generation Post Published (Priority: P2)

The business owner wants a consistent LinkedIn presence without writing posts manually. On a weekly schedule (or on demand), Claude generates a professional LinkedIn post designed to attract sales leads, and publishes it after the owner approves it.

**Why this priority**: LinkedIn automation demonstrates the full MCP + HITL approval pipeline end-to-end and is the flagship Silver Tier output. Shares P2 with email planning since both depend on the same approval pipeline.

**Independent Test**: Invoke the `linkedin-post` skill. Within 2 minutes, `Plans/PLAN_*_linkedin.md` appears with a drafted post and `Awaiting Approval`, and `Pending_Approval/APPROVAL_*_linkedin.md` is created. Move that file to `Approved/`. Confirm the post is published (or dry-run logged if `DRY_RUN=true`).

**Acceptance Scenarios**:

1. **Given** the LinkedIn post skill is invoked, **When** it runs, **Then** a plan is created in `Plans/` with a 100–300 word post, a service/product mention, and a call-to-action.
2. **Given** a LinkedIn `APPROVAL_*_linkedin.md` is in `Pending_Approval/`, **When** the owner moves it to `Approved/`, **Then** the executor detects it and publishes the post via the MCP server (or logs as dry-run).
3. **Given** `DRY_RUN=true`, **When** a LinkedIn post is approved, **Then** the post content is written to `Logs/YYYY-MM-DD.json` with `approval_status: dry_run` and no real publish occurs.
4. **Given** the weekly schedule is configured, **When** the scheduled trigger fires (Monday 8 AM), **Then** the LinkedIn post skill runs automatically without manual invocation.

---

### User Story 4 — Scheduler Runs Tasks Automatically (Priority: P3)

The business owner wants the system to operate hands-off on a daily/weekly cadence. A cron schedule runs watchers and the LinkedIn post generator automatically so no manual invocation is required day-to-day.

**Why this priority**: Scheduling is valuable but the system works without it (skills can be invoked manually). It is the autonomy layer that completes the Silver Tier experience.

**Independent Test**: Configure a cron entry for the Gmail watcher (every 5 minutes). Wait for the next trigger. Confirm a log entry appears in `Logs/YYYY-MM-DD.json` with `actor: scheduler` without any manual action.

**Acceptance Scenarios**:

1. **Given** a cron entry is configured, **When** the trigger fires, **Then** the scheduled watcher or skill runs and produces a `Logs/` entry with `actor: scheduler`.
2. **Given** the LinkedIn cron is configured for Monday 8 AM, **When** that time arrives, **Then** a LinkedIn post plan is created in `Plans/` automatically.
3. **Given** the daily task processing cron is configured (9 AM), **When** it fires, **Then** all pending items in `Needs_Action/` are processed and plans are created.

---

### Edge Cases

- What happens when Gmail OAuth tokens expire? → Watcher creates `ERROR_*.md` and pauses; owner is notified via Dashboard.
- What happens when a LinkedIn post is approved but the MCP server is unreachable? → Action is retried up to 3 times with exponential backoff; on final failure an `ERROR_*.md` is created and the plan reverts to `Awaiting Approval`.
- What happens when two watchers detect events simultaneously? → Each creates an independent task file; no data is lost or merged.
- What happens when a plan sits `Awaiting Approval` for more than 48 hours? → Dashboard highlights it as stale; no automatic rejection or execution.
- What happens when `DRY_RUN=true` and an action is approved? → Action is logged but not executed; plan moves to `Done/` with a `dry_run` note.

---

## Requirements *(mandatory)*

### Functional Requirements

**Watchers**

- **FR-001**: System MUST include a Gmail watcher that polls the inbox at a configurable interval (default: every 5 minutes) and converts each new unread email into a task `.md` file in `Needs_Action/`.
- **FR-002**: System MUST include a WhatsApp watcher that monitors incoming messages and converts each new message into a task `.md` file in `Needs_Action/`.
- **FR-003**: Each watcher task file MUST contain YAML frontmatter with: `type`, `source`, `sender`, `subject_or_content`, `received` (ISO-8601 UTC), `priority`, `status: pending`.
- **FR-004**: Each watcher MUST maintain a persistent registry of processed message IDs to prevent duplicate task creation on restart.
- **FR-005**: Each watcher MUST create an `ERROR_*.md` in `Needs_Action/` and continue running when a non-fatal error occurs; fatal errors must be logged before exit.

**Planning & Reasoning Loop**

- **FR-006**: The planning skill MUST read `Company_Handbook.md` before processing any task.
- **FR-007**: The planning skill MUST create a `Plans/PLAN_<timestamp>_<stem>.md` for every task, containing: Summary, Analysis, Actions (with `[ ]` task checkboxes), and Notes. The approval gate is handled exclusively by `APPROVAL_*.md` file movement to `Approved/` — not by checkbox editing.
- **FR-008**: Any action involving outbound external communication (email reply, LinkedIn post, WhatsApp reply) MUST be gated with a human approval step: the skill writes an `APPROVAL_*.md` file to `Pending_Approval/` and MUST NOT execute the action until a human moves that file to `Approved/`.
- **FR-009**: Safe internal actions (summaries, dashboard updates, file moves) MAY execute without approval.

**LinkedIn Automation**

- **FR-010**: The LinkedIn post skill MUST generate a post of 100–300 words containing a value proposition, a specific service/product mention drawn from `Business_Goals.md`, and a call-to-action.
- **FR-011**: The LinkedIn post skill MUST place the drafted post in `Plans/` with `Awaiting Approval` status before any publish action is taken.
- **FR-012**: On approval, the MCP server MUST publish the post to the configured LinkedIn account (or log it as dry-run if `DRY_RUN=true`).

**MCP Server**

- **FR-013**: At least one MCP server MUST be operational and callable by Claude during plan execution.
- **FR-014**: The MCP server MUST support at minimum one of: send email reply, publish LinkedIn post, or trigger an external API request.
- **FR-015**: Every MCP server call MUST be logged to `Logs/YYYY-MM-DD.json` with action type, target, parameters, approval status, and result.

**Human-in-the-Loop Approval**

- **FR-016**: The orchestrator (or an approval-watcher skill) MUST detect when an `APPROVAL_*.md` file is moved into `Approved/` and trigger execution of the corresponding action.
- **FR-017**: On successful MCP execution, the plan MUST be moved to `Done/DONE_*.md`.
- **FR-018**: On MCP execution failure, an `ERROR_*.md` MUST be created and the plan MUST revert to `Awaiting Approval` status.

**Scheduling**

- **FR-019**: The system MUST provide a ready-to-use cron configuration covering: Gmail watcher (every 5 min), LinkedIn post skill (Monday 8 AM weekly), daily task processing (daily 9 AM). The WhatsApp watcher runs as a persistent daemon started by the orchestrator — not via cron — to satisfy the ≤60s detection requirement (SC-002).
- **FR-020**: Every scheduled run MUST write a log entry to `Logs/YYYY-MM-DD.json` with `actor: scheduler`.

**Agent Skills**

- **FR-021**: All AI capabilities MUST be implemented as named Agent Skills in `.claude/skills/<skill-name>/SKILL.md`, created via the `skill-creator` skill.
- **FR-022**: Each skill MUST declare in its frontmatter: name, description (purpose + inputs + outputs).

**Dashboard**

- **FR-023**: `Dashboard.md` MUST display: pending task count, plans awaiting approval count, completed today count, and active watcher status after every skill run.

### Key Entities

- **Task**: A `.md` file in `Needs_Action/` representing a single incoming event. Has type, source, sender, content, priority, and status.
- **Plan**: A `.md` file in `Plans/` representing Claude's structured response to a task. Has source reference, approval status, action checkboxes, and execution history.
- **Watcher**: A background process monitoring one external channel, producing Task files idempotently.
- **Agent Skill**: A named SKILL.md in `.claude/skills/` that Claude executes to accomplish a specific capability.
- **MCP Server**: An external-action executor that Claude calls via tool use to interact with outside systems.
- **Audit Log Entry**: A single-line JSON record in `Logs/YYYY-MM-DD.json` covering every action, actor, target, and result.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new Gmail email is converted into a task file in `Needs_Action/` within 5 minutes of arrival, with no manual intervention.
- **SC-002**: A new WhatsApp message is converted into a task file in `Needs_Action/` within 60 seconds, with no manual intervention.
- **SC-003**: The planning skill processes 10 queued tasks and creates 10 corresponding plan files in under 3 minutes.
- **SC-004**: Zero duplicate task files are created when a watcher restarts and re-encounters already-processed messages (idempotency rate: 100%).
- **SC-005**: A LinkedIn post is drafted, approved, and published (or dry-run logged) in a single end-to-end flow without any manual code execution.
- **SC-006**: 100% of outbound-communication actions (email replies, LinkedIn posts) wait for an `APPROVAL_*.md` file to be moved to `Approved/` before execution — no action fires without human approval.
- **SC-007**: The cron schedule runs at least 3 consecutive cycles without manual intervention, each cycle producing a `Logs/` entry with `actor: scheduler`.
- **SC-008**: No credentials, API keys, or tokens appear in any committed `.md` file, source file, or vault file.

---

## Assumptions

- The owner has a Gmail account accessible via OAuth2 App Password or Gmail API credentials stored in `.env` (not in the vault).
- WhatsApp access uses the WhatsApp Business API or browser automation; exact method is an implementation decision.
- LinkedIn publishing uses the LinkedIn API or browser automation; the spec does not mandate which.
- `DRY_RUN=true` is the default — no real emails or posts are sent unless explicitly set to `false` in `.env`.
- The system runs on a single machine (WSL2/Linux); no cloud deployment is in scope for Silver Tier.
- Post topics and promoted services are defined in `AI_Employee_Vault/Business_Goals.md`, which the LinkedIn skill reads before generating content.
- Scheduling uses system cron (`crontab -e`); Windows Task Scheduler is an acceptable alternative for WSL2 users.
- The `skill-creator` skill is always invoked when creating or updating any Agent Skill.

---

## Out of Scope

- Outbound WhatsApp message sending (receive/detect only for Silver; sending is Gold+)
- Email thread summarisation or full conversation history (single-message processing only)
- LinkedIn comment monitoring or automated replies
- Payment processing or financial MCP integrations
- Multi-agent concurrency (one Claude instance only)
- Microservices, distributed systems, or external databases
- Mobile or web UI (Obsidian vault is the only interface)
