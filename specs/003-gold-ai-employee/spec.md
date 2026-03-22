# Feature Specification: Gold Tier Personal AI Employee

**Feature Branch**: `003-gold-ai-employee`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Gold Tier Personal AI Employee — autonomous agent managing personal (Gmail, WhatsApp) and business (social media, accounting, tasks) operations with watcher-based perception, MCP action layer, HITL approval, Ralph Wiggum loop, CEO briefing, and audit logging.

---

## System Overview

The Gold Tier Personal AI Employee is a locally-hosted autonomous agent that monitors multiple communication and financial channels, reasons over incoming events, generates structured plans, and executes approved actions across personal and business domains. It operates continuously, requiring human approval only for sensitive or high-impact actions, and produces a weekly CEO briefing summarising performance against business goals.

**Primary actors:**
- **Owner** — the human who receives briefings, approves/rejects sensitive actions, and configures the vault.
- **AI Agent** — the reasoning engine that processes events and executes actions within defined boundaries.
- **Watchers** — perception scripts that poll external sources and convert events into structured task files.
- **MCP Servers** — execution layer that performs real-world actions (email, social, payments, accounting).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Inbound Email Triage and Response (Priority: P1)

A new email arrives in Gmail. The Gmail watcher detects it, creates a `Needs_Action` file. The agent reads the file, generates a `Plan.md` with a draft reply. Because the sender is a known contact and the reply is within auto-approve rules, the agent sends the reply via Email MCP. The action is logged to `Logs/`.

**Why this priority**: Email is the highest-volume daily input; automating triage and standard replies delivers immediate, measurable time savings.

**Independent Test**: Can be fully tested by sending a test email to the monitored Gmail account and verifying that a `Needs_Action` file appears, a `Plans/PLAN_*.md` is created, and a reply is sent (or queued for approval) within 5 minutes.

**Acceptance Scenarios**:

1. **Given** a new email from a known contact arrives, **When** the Gmail watcher polls within its interval, **Then** a structured `Needs_Action/EMAIL_*.md` file is created within 60 seconds.
2. **Given** a `Needs_Action/EMAIL_*.md` file exists, **When** the agent processes it, **Then** a `Plans/PLAN_*.md` with a draft reply is written.
3. **Given** the sender is a known contact and the reply is non-bulk, **When** the agent evaluates permission boundaries, **Then** the reply is sent automatically and logged.
4. **Given** the sender is unknown, **When** the agent evaluates permission boundaries, **Then** an `APPROVAL_*.md` is written to `Pending_Approval/` and no reply is sent until approved.

---

### User Story 2 — Human-in-the-Loop Approval for Sensitive Actions (Priority: P1)

The agent detects a required action that exceeds auto-approve thresholds (new contact email, payment > $100, social media post). It writes a plan and an approval file to `Pending_Approval/`. The owner reviews the file in Obsidian and moves it to `Approved/`. The agent detects the move and executes via MCP. If moved to `Rejected/`, the action is archived and never retried.

**Why this priority**: HITL is the safety gate for the entire system; without it no sensitive action can safely be automated.

**Independent Test**: Can be fully tested by dropping a simulated high-value payment task into `Needs_Action/`, verifying `APPROVAL_*.md` appears in `Pending_Approval/`, manually moving it to `Approved/`, and confirming the action is executed and logged.

**Acceptance Scenarios**:

1. **Given** a task requires a payment above $100, **When** the agent processes it, **Then** no payment is made and an `APPROVAL_*.md` appears in `Pending_Approval/`.
2. **Given** an `APPROVAL_*.md` is moved to `Approved/`, **When** the ApprovalWatcher detects the move, **Then** the action executes via MCP and the result is logged.
3. **Given** an `APPROVAL_*.md` is moved to `Rejected/`, **When** the ApprovalWatcher detects the move, **Then** the action is permanently archived and never retried.
4. **Given** a banking action fails after approval, **When** the error occurs, **Then** the system writes `ERROR_*.md` to `Needs_Action/` and does NOT auto-retry; fresh approval is required.

---

### User Story 3 — WhatsApp Keyword Monitoring (Priority: P2)

The WhatsApp watcher maintains a single persistent browser session and monitors messages for configured keywords. When a keyword match is found, it creates a `Needs_Action/WHATSAPP_*.md` file. The agent processes it according to handbook rules.

**Why this priority**: WhatsApp is a primary business communication channel; missed messages carry reputational and financial risk.

**Independent Test**: Can be fully tested by sending a keyword-matching WhatsApp message and verifying a `Needs_Action/WHATSAPP_*.md` is created within the polling interval, without a second browser session being opened.

**Acceptance Scenarios**:

1. **Given** the system starts, **When** the WhatsApp watcher initialises, **Then** exactly one browser session is opened and no additional sessions are created.
2. **Given** a WhatsApp message contains a configured keyword, **When** the watcher polls, **Then** a `Needs_Action/WHATSAPP_*.md` is created.
3. **Given** the watcher session expires, **When** reconnection occurs, **Then** the existing session is reused (not duplicated) and no messages are lost.
4. **Given** the agent determines a WhatsApp reply is needed, **When** the agent processes the task, **Then** an `APPROVAL_*.md` is written to `Pending_Approval/` before any outbound WhatsApp message is sent; no reply is sent until the owner approves.

---

### User Story 4 — Finance Watcher and Odoo Transaction Tracking (Priority: P2)

The Finance watcher detects new bank transactions from the configured source, writes them to `Bank_Transactions.md`, and creates `Needs_Action/FINANCE_*.md` files for categorisation. The agent processes these, creates or updates Odoo records via Odoo MCP, and logs results.

**Why this priority**: Financial visibility is a core Gold-tier requirement; inaccurate records undermine the CEO briefing.

**Independent Test**: Can be fully tested by injecting a mock transaction into the Finance watcher input and verifying `Bank_Transactions.md` is updated, an Odoo record is created, and the transaction appears in the next CEO briefing.

**Acceptance Scenarios**:

1. **Given** a new bank transaction is detected, **When** the Finance watcher runs, **Then** it is appended to `Bank_Transactions.md` with correct fields (date, amount, payee, reference).
2. **Given** a `Needs_Action/FINANCE_*.md` exists, **When** the agent processes it, **Then** an Odoo invoice or transaction record is created or updated via Odoo MCP.
3. **Given** Odoo MCP is unavailable, **When** the agent tries to sync, **Then** a retry is scheduled (exponential backoff) and an error file is written if all retries fail.

---

### User Story 5 — Weekly CEO Briefing (Priority: P2)

Every Sunday night the agent reads `Business_Goals.md` and `Bank_Transactions.md`, analyses performance, and writes `Briefings/YYYY-MM-DD_Monday_Briefing.md`. The briefing contains revenue vs. target, completed tasks, bottlenecks, and cost-optimisation suggestions.

**Why this priority**: The CEO briefing is the primary business-intelligence output; it demonstrates system value and drives owner decisions.

**Independent Test**: Can be fully tested by triggering the briefing skill manually and verifying a correctly structured `Briefings/*.md` is written with all mandatory sections populated.

**Acceptance Scenarios**:

1. **Given** Sunday 23:00 arrives, **When** the cron triggers the briefing skill, **Then** `Briefings/YYYY-MM-DD_Monday_Briefing.md` is created within 10 minutes.
2. **Given** the briefing runs, **When** revenue data is available, **Then** the briefing includes weekly and MTD revenue vs. target with percentage variance.
3. **Given** tasks exist in `Done/` or are overdue in `Needs_Action/`, **When** the briefing runs, **Then** completed tasks and bottlenecks (>24 h without state change) are listed.
4. **Given** `Bank_Transactions.md` contains subscription charges, **When** the briefing runs, **Then** unused or duplicate subscriptions flagged in `Business_Goals.md` appear in cost-optimisation suggestions.

---

### User Story 6 — Social Media Post Approval, Publishing, and Summary (Priority: P3)

The agent generates a LinkedIn/social post using the `linkedin-post` skill, writes a plan and approval file. The owner reviews and approves. The `execute-plan` skill publishes via Social MCP (LinkedIn, Facebook, Instagram, Twitter/X). After publishing, the agent generates a per-platform activity summary and includes it in the next CEO Briefing.

**Why this priority**: Social publishing is high-visibility but lower frequency; it requires approval and is therefore less urgent than perception/response flows.

**Independent Test**: Can be fully tested by triggering the `linkedin-post` skill, verifying `APPROVAL_*.md` is created, approving it, confirming the post appears in the Social MCP execution log, and verifying the next CEO Briefing contains a Social Media Summary section for the platform.

**Acceptance Scenarios**:

1. **Given** a social post is requested, **When** the agent generates it, **Then** `APPROVAL_*.md` is written to `Pending_Approval/` before any platform interaction.
2. **Given** the approval is moved to `Approved/`, **When** the execute-plan skill runs, **Then** the post is published to the specified platform and logged.
3. **Given** the approval is moved to `Rejected/`, **When** detected, **Then** the post is archived to `Rejected/` and no platform action is taken.
4. **Given** a post is published successfully, **When** the CEO Briefing runs, **Then** it includes a "Social Media Summary" section listing each platform, post confirmation, and available engagement data.

---

### User Story 6b — Social Media Activity Summary (Priority: P3)

After publishing on any connected social platform (LinkedIn, Facebook, Instagram, Twitter/X), the agent retrieves available activity data (post confirmation, reach estimate, or engagement snapshot where the platform API supports it) and writes a summary. This summary feeds into the weekly CEO Briefing.

**Why this priority**: The hackathon explicitly requires summary generation alongside posting for Facebook, Instagram, and Twitter/X; it closes the loop from action back to business intelligence.

**Independent Test**: Can be fully tested by confirming that after any approved social post, an audit log entry for the summary exists and the next CEO Briefing contains a populated "Social Media Summary" section.

**Acceptance Scenarios**:

1. **Given** a post is published on Facebook, Instagram, or Twitter/X, **When** the agent completes execution, **Then** it generates a summary of that post (platform, timestamp, content excerpt, and any available engagement data) and logs it as an audit entry.
2. **Given** a platform API does not support engagement retrieval, **When** the summary is generated, **Then** a post-confirmation summary (platform, timestamp, content) is written with a note that engagement data is unavailable.
3. **Given** the CEO Briefing runs, **When** any social posts occurred during the period, **Then** the briefing contains a "Social Media Summary" section populated with data from all connected platforms.

---

### User Story 7 — Ralph Wiggum Autonomous Loop (Priority: P3)

For multi-step tasks requiring persistence (e.g., invoice reconciliation, project task processing), the Ralph Wiggum loop prevents premature exit. The agent iterates until it outputs `<promise>TASK_COMPLETE</promise>` or the task file moves to `Done/`. A maximum iteration count prevents infinite loops.

**Why this priority**: Persistence loop is an enabler for complex autonomous tasks; important but not required for basic operation.

**Independent Test**: Can be fully tested by triggering a multi-step task with a known completion condition and verifying the agent does not exit before the task file reaches `Done/`, and does exit once it does.

**Acceptance Scenarios**:

1. **Given** a multi-step task is started with the Ralph loop, **When** the task is incomplete, **Then** the agent does not exit and re-injects the task prompt.
2. **Given** the agent outputs `<promise>TASK_COMPLETE</promise>`, **When** the Stop hook detects it, **Then** the loop exits cleanly.
3. **Given** the maximum iteration count is reached, **When** the task is still incomplete, **Then** the loop exits and writes `ERROR_*.md` with iteration-limit reason.

---

### Edge Cases

- What happens when a `Needs_Action` file is malformed (missing required fields)? → Agent writes `ERROR_*.md` and moves the original to `Done/` with error annotation.
- What happens when two watchers create conflicting task files for the same source event? → The claim-by-move rule ensures only the first agent to claim the file processes it; the duplicate is skipped.
- What happens when the Obsidian vault path is unmounted or unavailable? → Orchestrator watchdog detects the missing mount, pauses all watchers, alerts via `ERROR_*.md`, and retries mount check every 30 seconds.
- What happens when an approval file is edited after being moved to `Approved/`? → The system reads the file state at move-detection time; subsequent edits are ignored. The executed action matches the approved version.
- What happens when Odoo is unreachable for more than 3 retry cycles? → A `Needs_Action/ERROR_ODOO_*.md` is written; finance sync is paused; the CEO briefing notes the sync gap.
- What happens when the WhatsApp session cookie expires mid-session? → The watcher attempts a single re-authentication; if it fails, it writes `ERROR_*.md` and pauses until human resolves.
- What happens when the Gmail/Email MCP is unavailable? → Outgoing emails are queued locally; the queue is processed in order when the service is restored. No emails are lost or silently dropped.
- What happens when the Claude reasoning engine is unavailable? → All watchers continue running and depositing files into `Needs_Action/`; the queue grows until Claude resumes. No inbound events are lost.
- What happens when the Obsidian vault path is locked or inaccessible? → Watcher output is written to a configured temporary folder; files are synced into the vault when access is restored. The system does not halt.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Perception — Watchers

- **FR-001**: The system MUST include a Gmail watcher that polls for new emails at a configurable interval and creates structured `Needs_Action/EMAIL_*.md` files for each unprocessed message.
- **FR-002**: The system MUST include a WhatsApp watcher that maintains exactly one persistent browser session, monitors for configured keywords, and creates `Needs_Action/WHATSAPP_*.md` files on keyword match.
- **FR-003**: The system MUST include a filesystem watcher that monitors the `Inbox/` folder for dropped files and creates `Needs_Action/FILE_*.md` files for each new item.
- **FR-004**: The system MUST include a Finance watcher that monitors the configured bank transaction source, appends entries to `Bank_Transactions.md`, and creates `Needs_Action/FINANCE_*.md` files for unprocessed transactions.
- **FR-005**: All watchers MUST track processed IDs in persistent state files to guarantee idempotency across restarts.
- **FR-006**: No watcher MUST contain reasoning or decision logic; all logic resides in agent skills.

#### Reasoning — Agent Skills

- **FR-007**: The agent MUST use Claude Code as its reasoning engine for all task processing.
- **FR-008**: The agent MUST generate a `Plans/PLAN_*.md` file for every task before executing any action.
- **FR-009**: ALL agent functionality MUST be encapsulated in discrete agent skills under `.claude/skills/`.
- **FR-010**: The agent MUST read `Company_Handbook.md` before processing any task to apply current rules of engagement.
- **FR-011**: The agent MUST apply the claim-by-move rule: move a task file from `Needs_Action/` to `In_Progress/<agent>/` before processing; skip files already claimed.

#### Action Layer — MCP Servers

- **FR-012**: The system MUST include an Email MCP server capable of sending emails, creating drafts, and searching the inbox.
- **FR-013**: The system MUST include a Browser MCP server for automating web-based actions (WhatsApp Web, payment portals).
- **FR-014a**: The system MUST include a Social MCP server supporting post publication on LinkedIn, Facebook, Instagram, and Twitter/X.
- **FR-014b**: After publishing on any social platform, the system MUST generate an activity summary (post confirmation, content excerpt, and engagement data where the platform API supports it) and write it as an audit log entry and as input to the CEO Briefing's "Social Media Summary" section.
- **FR-015**: The system MUST include an Odoo MCP integration supporting invoice creation, transaction record creation/update, and customer lookup via JSON-RPC.
- **FR-016**: All MCP interactions MUST be logged to `Logs/YYYY-MM-DD.json` with the defined audit schema.

#### Human-in-the-Loop (HITL)

- **FR-017**: The system MUST require approval for: emails to new contacts, bulk email sends, payments to new payees, payments over $100, social media posts and replies, WhatsApp outbound messages (all replies and proactive messages), and any file operation outside the vault.
- **FR-018**: The system MUST auto-approve: emails to known contacts (non-bulk), recurring payments under $50 to known payees, read operations, file creation/move within vault, and scheduled social posts already in `Approved/`.
- **FR-019**: Approval files MUST be written to `Pending_Approval/` before any sensitive action is attempted.
- **FR-020**: Files moved to `Rejected/` MUST be archived permanently and never executed or retried.
- **FR-021**: Banking actions MUST never auto-retry after failure; each retry requires a fresh approval file.

#### Accounting — Odoo

- **FR-022**: The system MUST generate invoices in Odoo Community for billable events identified in task files.
- **FR-023**: The system MUST track all bank transactions in Odoo and reconcile them against `Bank_Transactions.md`.
- **FR-024**: The Odoo integration MUST operate against a self-hosted Odoo Community instance version 19 or higher; no SaaS dependency. The Odoo 19+ external JSON-RPC API is the required integration interface.

#### Weekly CEO Briefing

- **FR-025**: The system MUST generate a CEO briefing every Sunday night (configurable cron time) and write it to `Briefings/YYYY-MM-DD_Monday_Briefing.md`.
- **FR-026**: The briefing MUST include all seven sections: (1) weekly and MTD revenue vs. target (from `Bank_Transactions.md`), (2) list of completed tasks from `Done/`, (3) identified bottlenecks (tasks stalled > 24 h in `Needs_Action/` or `In_Progress/`), (4) cost-optimisation suggestions from subscription audit (`Business_Goals.md`), (5) upcoming deadlines from `Business_Goals.md` Active Projects, (6) Social Media Summary table listing all connected platforms with post counts and available engagement data for the period, and (7) an Executive Summary paragraph.
- **FR-027**: The briefing MUST be generated from the following five local data sources — no external API calls are required to produce it: (1) `Business_Goals.md` (targets, KPIs, subscription audit rules, Active Projects with deadlines), (2) `Bank_Transactions.md` (revenue and expense transactions), (3) `Done/` folder (completed tasks for the period), (4) `Needs_Action/` and `In_Progress/` folders (stalled task detection), and (5) `Logs/YYYY-MM-DD.json` (social media post activity for the period).

#### Ralph Wiggum Loop

- **FR-028**: The system MUST support a persistence loop that re-injects the task prompt on each iteration when the task is not yet complete. On each iteration, the agent MUST have access to the output of its previous iteration so it can reason about why the prior attempt did not complete.
- **FR-029**: The loop MUST exit when the agent outputs `<promise>TASK_COMPLETE</promise>` or when the task file is detected in `Done/`.
- **FR-030**: The loop MUST enforce a configurable maximum iteration count and write `ERROR_*.md` if the limit is reached without completion.

#### Audit Logging

- **FR-031**: The system MUST write a structured JSON log entry to `Logs/YYYY-MM-DD.json` for every action (email send, social post, payment, Odoo sync, file operation).
- **FR-032**: Log entries MUST conform to the defined audit schema (see Data Schemas).
- **FR-033**: Log files older than 90 days MUST be eligible for automated deletion (retention policy enforced by a scheduled task).
- **FR-034**: No sensitive credentials or personal tokens MUST appear in log files.

#### Error Handling

- **FR-035**: All transient errors (network timeout, rate limit) MUST be retried with exponential backoff: base 1 s, max 60 s, 3 attempts.
- **FR-036**: All authentication errors MUST pause the affected watcher/MCP, write `ERROR_*.md` to `Needs_Action/`, and require human resolution before resuming.
- **FR-037**: The orchestrator MUST include a watchdog process that detects watcher/MCP crashes and restarts them automatically (max 3 auto-restarts per hour; human alert after that).
- **FR-038**: The system MUST NEVER silently fail; every error produces a `Needs_Action/ERROR_*.md` entry.
- **FR-041**: When the Email MCP is unavailable, the system MUST queue outgoing emails locally and deliver them in order when the service is restored; no outbound emails are silently dropped.
- **FR-042**: When the Claude reasoning engine is unavailable, all watchers MUST continue running and depositing files into `Needs_Action/`; the accumulated queue MUST be processed when Claude resumes without requiring manual intervention.
- **FR-043**: When the Obsidian vault path is locked or inaccessible, watchers MUST write output to a configured temporary folder and sync those files into the vault when access is restored; the system MUST NOT halt or lose events during the outage period.

#### Dashboard

- **FR-039**: `Dashboard.md` MUST be updated after every task state transition to reflect current counts of tasks in each state (Needs_Action, In_Progress, Pending_Approval, Done, Rejected, Errors).
- **FR-040**: `Dashboard.md` MUST be written only by the Local agent (single-writer rule).

---

### Key Entities

- **Task File** (`Needs_Action/TYPE_TIMESTAMP.md`): Represents a single inbound event requiring agent action. Key attributes: type, source, raw content, created timestamp, priority.
- **Plan** (`Plans/PLAN_TIMESTAMP.md`): Agent-generated action plan for a task. Key attributes: linked task file, decision rationale, list of actions (ordered), approval requirement flag.
- **Approval File** (`Pending_Approval/APPROVAL_TIMESTAMP.md`): Human-review gate for sensitive actions. Key attributes: linked plan, action type, action parameters, risk classification, requested-by timestamp.
- **Audit Log Entry** (`Logs/YYYY-MM-DD.json` — NDJSON lines): Immutable record of every executed action. Key attributes: timestamp, action_type, actor, target, parameters, approval_status, approved_by, result.
- **CEO Briefing** (`Briefings/YYYY-MM-DD_Monday_Briefing.md`): Weekly business-intelligence report. Key attributes: period, revenue figures, task summary, bottleneck list, subscription recommendations.
- **Bank Transaction** (`Bank_Transactions.md` rows): Financial event record. Key attributes: date, amount, currency, payee, reference, category, Odoo sync status.
- **Watcher State** (`scripts/processed_*.json`): Idempotency registry for each watcher. Key attributes: source type, list of processed IDs, last-poll timestamp.

---

## Non-Functional Requirements

### Reliability

- **NFR-001**: The system MUST achieve ≥ 99% uptime for watcher processes during configured operating hours. For acceptance testing purposes, this is verified by: (a) a 60-minute continuous operation test with zero unplanned watcher crashes, and (b) confirmed watchdog auto-restart within 60 s on simulated failure. Production uptime is tracked over a rolling 7-day window via audit log entries.
- **NFR-002**: Watcher polling MUST resume within 60 seconds of an unplanned crash (watchdog restart).
- **NFR-003**: No task file MUST be processed more than once (idempotency guaranteed by watcher state files).
- **NFR-004**: Banking actions MUST have zero unintended executions; every payment requires an explicit approval file.

### Performance

- **NFR-005**: A new inbound email MUST produce a `Needs_Action` file within 60 seconds of arrival (at default polling interval).
- **NFR-006**: The CEO briefing MUST be generated and written within 10 minutes of the scheduled trigger.
- **NFR-007**: Dashboard.md MUST be updated within 30 seconds of any task state transition.

### Security

- **NFR-008**: All credentials and API tokens MUST be stored in `.env` (gitignored) or the OS keychain; never in vault markdown files.
- **NFR-009**: `DRY_RUN=true` MUST be the default configuration; live execution requires explicit opt-in (`DRY_RUN=false`).
- **NFR-010**: The system MUST enforce rate limits: maximum 10 outbound emails per hour, maximum 3 payment actions per hour.
- **NFR-011**: Credentials MUST be rotated on a documented schedule (at minimum monthly and after any suspected breach).
- **NFR-012**: All external API interactions MUST use HTTPS/TLS; no plain-text communication with external services.

### Modularity

- **NFR-013**: Every piece of agent logic MUST be encapsulated in a discrete skill; no ad-hoc reasoning outside skills.
- **NFR-014**: Each MCP server MUST be independently startable and stoppable without affecting other MCP servers.
- **NFR-015**: Adding a new watcher MUST require no changes to existing watchers or skills; only orchestrator registration is needed.

### Observability

- **NFR-016**: `Dashboard.md` MUST provide at-a-glance counts for all task states at all times.
- **NFR-017**: `Logs/YYYY-MM-DD.json` MUST be queryable (parseable NDJSON) for any 90-day lookback period.
- **NFR-018**: Any error condition MUST produce a human-readable `ERROR_*.md` in `Needs_Action/` within 30 seconds of detection.

### Local-First Architecture

- **NFR-019**: The system MUST function without continuous internet connectivity for all vault read/write and reasoning operations; only MCP action calls require network access.
- **NFR-020**: Obsidian vault MUST be the single source of truth; no external database or cloud service stores primary state.

### Documentation

- **NFR-021**: The system MUST include architecture documentation covering all components and their interactions, rationale for key design decisions, and known limitations and lessons learned. This documentation is a required deliverable alongside the working system.

---

## Data Schemas

### Needs_Action File Schema

```
---
type: email | whatsapp | file_drop | finance | action_trigger | error
source: <string>           # e.g. gmail, whatsapp, inbox, bank, system
source_id: <string>        # unique ID from source (email message ID, etc.)
created: <ISO-8601Z>
priority: high | medium | low
subject: <string>          # human-readable summary
raw_content: |
  <multiline string — the full original message or event body>
attachments: []            # list of attachment filenames if any
---

## Context
<additional context parsed by the watcher>

## Suggested Action
<optional pre-suggestion from watcher, plain text>
```

### Plan.md Schema

```
---
plan_id: PLAN_<timestamp>
task_ref: <path to source Needs_Action file>
created: <ISO-8601Z>
requires_approval: true | false
approval_category: email_new_contact | payment | social_post | bulk_email | none
---

## Objective
<one-sentence goal>

## Decision Rationale
<why this plan was chosen over alternatives>

## Actions
- [ ] Action 1: <description> | mcp: <server> | method: <method>
- [ ] Action 2: <description> | mcp: <server> | method: <method>

## Risk Assessment
<any risks identified>

## Completion Criteria
<how agent knows this task is done>
```

### Approval File Schema

```
---
approval_id: APPROVAL_<timestamp>
plan_ref: <path to Plans/PLAN_*.md>
action_type: send_email | linkedin_post | payment | odoo_sync | bulk_email
risk_class: low | medium | high | critical
requested_at: <ISO-8601Z>
status: pending | approved | rejected
is_recurring: true | false        # for payment actions — affects auto-approve eligibility
payment_amount: <decimal or null> # for payment actions — used to evaluate $50/$100 thresholds
known_payee: true | false         # for payment actions — must be true for auto-approve eligibility
---

## Action Summary
<plain-language description of what will happen if approved>

## Parameters
<key-value list of action parameters — no credentials>

## Approval Instructions
Move this file to:
- `Approved/` to execute
- `Rejected/` to cancel permanently
```

### Audit Log Entry Schema (NDJSON line)

```json
{
  "timestamp": "ISO-8601Z",
  "action_type": "email_send | linkedin_post | odoo_invoice | payment | file_move | ...",
  "actor": "claude_code | watcher_gmail | watcher_whatsapp | ...",
  "target": "<recipient, URL, or resource identifier>",
  "parameters": {},
  "approval_status": "approved | auto | pending",
  "approved_by": "human | system",
  "result": "success | failure",
  "error_message": "<string or null>"
}
```

### CEO Briefing Schema

```
---
briefing_date: YYYY-MM-DD
period_start: YYYY-MM-DD
period_end: YYYY-MM-DD
generated_at: <ISO-8601Z>
---

# Monday Briefing — <date>

## Revenue Summary
| Metric         | Target | Actual | Variance |
|----------------|--------|--------|----------|
| Weekly Revenue | $X     | $Y     | ±Z%      |
| MTD Revenue    | $X     | $Y     | ±Z%      |

## Completed This Week
- <task title> (completed <date>)

## Bottlenecks
- <task title> — stalled for <N> hours in <state>

## Cost Optimisation Suggestions
- <subscription / charge> — <recommendation>

## Upcoming Deadlines
- <item> due <date>

## Social Media Summary
| Platform  | Posts This Week | Engagement (if available) |
|-----------|-----------------|--------------------------|
| LinkedIn  | N               | <data or "N/A">          |
| Facebook  | N               | <data or "N/A">          |
| Instagram | N               | <data or "N/A">          |
| Twitter/X | N               | <data or "N/A">          |
```

---

## Assumptions

1. The owner uses Obsidian on the same machine that runs the watchers and orchestrator; vault path is consistent.
2. Gmail IMAP/OAuth2 credentials are pre-configured before system start; the Gmail watcher does not handle initial OAuth flow.
3. WhatsApp Web session QR code scanning is performed once manually; the watcher maintains the session cookie thereafter.
4. Odoo Community is already installed and reachable at a configured local URL; initial Odoo setup is out of scope.
5. `Business_Goals.md` and `Company_Handbook.md` are maintained manually by the owner; the agent reads but does not write them.
6. Social MCP credentials (LinkedIn API token, Facebook app token, etc.) are pre-configured in `.env`.
7. The Finance watcher input source (bank CSV export, open-banking API, or manual CSV drop) is configured per deployment; the spec is agnostic about the specific bank integration mechanism.
8. The system runs on a single local machine; multi-machine or cloud synchronisation is out of scope for Gold tier.
9. `Bank_Transactions.md` at vault root is the canonical Finance watcher output path in this spec. The hackathon document references `/Accounting/Current_Month.md` for the same data; both refer to the same logical artefact. The vault-root path is used throughout this spec for consistency.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of inbound emails from known contacts receive a plan within 5 minutes of arrival during operating hours.
- **SC-002**: Zero sensitive actions (payments, new-contact emails, social posts) are executed without a human-approved approval file.
- **SC-003**: The CEO briefing is generated every Sunday night with all mandatory sections populated; zero missed briefings over a 4-week period.
- **SC-004**: All bank transactions detected by the Finance watcher are reflected in Odoo within 10 minutes of detection, with a ≤ 1% discrepancy rate.
- **SC-005**: Zero duplicate task processing events occur across watcher restarts (idempotency rate = 100%).
- **SC-006**: 100% of system actions (email, social, payment, Odoo) produce a corresponding audit log entry; zero silent operations.
- **SC-007**: The orchestrator automatically recovers from watcher crashes within 60 seconds for ≥ 95% of incidents, without human intervention.
- **SC-008**: The Ralph Wiggum loop completes multi-step tasks without premature exit for ≥ 98% of triggered tasks, and never exceeds the configured maximum iteration count.
- **SC-009**: Dashboard.md accurately reflects real-time task state counts with ≤ 30 seconds latency after any state change.
- **SC-010**: WhatsApp watcher maintains a single browser session across a 24-hour operating period; zero duplicate sessions created.
- **SC-011**: Every CEO Briefing produced after a week in which social posts were published includes a populated "Social Media Summary" section covering all connected platforms; zero briefings omit this section when social activity occurred.
- **SC-012**: Architecture documentation is present as a deliverable at submission, covering all system components and their interactions, rationale for at least three key design decisions, and at least three documented lessons learned.
