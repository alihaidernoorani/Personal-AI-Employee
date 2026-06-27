# Feature Specification: Platinum Tier Personal AI Employee

**Feature Branch**: `004-platinum-ai-employee`
**Created**: 2026-06-27
**Status**: Draft
**Baseline**: Extends `003-gold-ai-employee` (spec.md). All Gold-tier requirements are inherited unless explicitly superseded here.
**Input**: Generate a complete technical specification for a Platinum Tier Personal AI Employee covering functional requirements, non-functional requirements, system architecture, folder structure, Claude Skills, MCP servers, watchers, vault design, security model, approval workflow, cloud/local responsibilities, deployment architecture, and testing strategy.

---

## System Overview

The Platinum Tier Personal AI Employee is a distributed, 24/7 autonomous agent that splits reasoning and execution across two compute environments:

- **Cloud Agent** (remote VM): runs continuously, handles triage, drafting, scheduling, and background monitoring. It writes exclusively to its designated vault folders and never executes irreversible actions.
- **Local Agent** (owner's machine): holds all credentials and execution authority. It reads cloud-prepared plans, presents them for approval, executes approved actions via MCP, and is the sole writer of authoritative vault state.

The two agents communicate exclusively through markdown files in a synchronised Obsidian vault. No direct network communication between agents is permitted. The vault is the only shared bus.

**Platinum gate criteria (from constitution §Hackathon Tier Compliance)**:
- Cloud VM (24/7) operational
- Cloud/Local agent split enforced with documented responsibility boundaries
- Bidirectional vault synchronisation with latency SLA
- All 15 constitution principles explicitly verified by a compliance-check skill

**Primary actors**:
- **Owner** — the human who approves sensitive actions, reviews briefings, and maintains vault configuration files.
- **Cloud Agent** — the 24/7 reasoning engine running on the cloud VM; triage and drafting only.
- **Local Agent** — the execution engine running on the owner's machine; all final actions, all credentials.
- **Watchers** — perception scripts running on both environments (cloud: Gmail, filesystem signal; local: WhatsApp, Finance, Approval).
- **MCP Servers** — execution adapters (Email, Social, Odoo, Browser) running exclusively on the local machine.
- **Vault Sync Process** — the background process that propagates vault changes bidirectionally between local and cloud.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — 24/7 Cloud-Assisted Email Triage (Priority: P1)

A new email arrives at 3 AM while the owner's machine is asleep. The cloud agent's Gmail watcher detects it, creates a triage task, drafts a response plan, and writes the plan to the vault. At 8 AM, when the local machine comes online and vault sync runs, the local agent reads the cloud-prepared plan, presents an approval file, and — after the owner approves — sends the reply via Email MCP. The owner wakes to find actionable drafts waiting, not a raw inbox.

**Why this priority**: This is the defining capability that separates Platinum from Gold. Gold requires the local machine to be running for triage; Platinum removes that constraint entirely. Without 24/7 cloud triage the entire Platinum value proposition collapses.

**Independent Test**: Suspend the local machine. Send a test email to the monitored account. Unsuspend the local machine 30 minutes later. Verify that `Plans/PLAN_*.md` is already present (created by the cloud agent), `Pending_Approval/APPROVAL_*.md` exists, and the owner can approve and send the reply without re-triggering triage.

**Acceptance Scenarios**:

1. **Given** the local machine is offline, **When** a new email arrives, **Then** the cloud agent creates `Needs_Action/EMAIL_*.md` within 60 seconds and subsequently writes `Plans/PLAN_*.md` with a draft reply.
2. **Given** the cloud agent has written a plan, **When** vault sync propagates to the local machine, **Then** the local agent reads the plan and writes `Pending_Approval/APPROVAL_*.md` without re-triaging.
3. **Given** `APPROVAL_*.md` is moved to `Approved/` by the owner, **When** the local Approval Watcher detects the move, **Then** the reply is sent via Email MCP and logged; no cloud MCP call is made.
4. **Given** the cloud agent is unavailable for up to 15 minutes, **When** it recovers, **Then** any events that occurred during the outage are processed from the local watcher queue without data loss.

---

### User Story 2 — Multi-Agent Task Coordination via Claim-by-Move (Priority: P1)

Both the cloud and local agents are active simultaneously. A new task file appears in `Needs_Action/`. The cloud agent claims it first by moving it to `In_Progress/cloud/`. The local agent, on its next poll, detects the file is already claimed and skips it. When the cloud agent completes processing, it moves the task to `Done/`. Neither agent ever processes the same task twice.

**Why this priority**: Without multi-agent coordination the shared vault becomes a race condition. Duplicate processing corrupts state, sends duplicate emails, and creates double payments. This is the coordination primitive that makes the whole distributed system safe.

**Independent Test**: Configure both agents to run concurrently. Drop 10 task files simultaneously into `Needs_Action/`. Verify each task is processed exactly once (either by cloud or local), and that `Done/` contains exactly 10 completed records with no duplicates and no files stranded in `Needs_Action/`.

**Acceptance Scenarios**:

1. **Given** a task file exists in `Needs_Action/`, **When** the cloud agent moves it to `In_Progress/cloud/`, **Then** the local agent skips that file on its next scan.
2. **Given** a task file exists in `In_Progress/cloud/`, **When** the cloud agent completes processing, **Then** it moves the file to `Done/` (via the local agent's execution, after approval if required).
3. **Given** the cloud agent crashes mid-task, **When** the cloud agent restarts, **Then** tasks stranded in `In_Progress/cloud/` for more than a configurable timeout (default: 10 minutes) are returned to `Needs_Action/` for reprocessing.
4. **Given** both agents attempt to claim the same task simultaneously, **When** both execute the move operation, **Then** exactly one succeeds and the other observes the task already moved; no task is processed twice.

---

### User Story 3 — Bidirectional Vault Synchronisation (Priority: P1)

The cloud agent writes a plan to `Plans/PLAN_*.md`. Within 60 seconds, that file is visible on the local machine. Conversely, the owner approves an action by moving `APPROVAL_*.md` to `Approved/` on the local machine; within 60 seconds, the cloud agent can see the approval in its vault replica. Both machines always have a consistent view of shared vault state.

**Why this priority**: Vault sync is the communication backbone. Without it the cloud/local split is just two isolated systems. Every other Platinum capability depends on sync working reliably and within SLA.

**Independent Test**: On the local machine, write a test file to `Signals/TEST_SIGNAL.md`. Start a timer. On the cloud VM, poll for the file. Verify it appears within 60 seconds. Then delete the file from the cloud VM and verify the deletion propagates back to the local machine within 60 seconds.

**Acceptance Scenarios**:

1. **Given** the cloud agent writes to `Plans/PLAN_*.md`, **When** sync runs, **Then** the file is readable on the local machine within 60 seconds.
2. **Given** the local owner moves `APPROVAL_*.md` to `Approved/`, **When** sync runs, **Then** the cloud agent's vault replica reflects the move within 60 seconds.
3. **Given** both agents write to different files in the same folder simultaneously, **When** sync resolves, **Then** both files are present on both machines with no data loss.
4. **Given** sync is interrupted (network partition), **When** connectivity is restored, **Then** all changes accumulated during the outage are propagated in order, with no files lost or corrupted.
5. **Given** a sync conflict occurs (same file modified on both sides), **When** resolution runs, **Then** the local machine's version wins for authoritative folders (`Dashboard.md`, `Approved/`, `Rejected/`, `Done/`); the cloud version wins for cloud-owned folders (`Updates/`, `Signals/`, `Plans/`).

---

### User Story 4 — Cloud/Local Security Boundary Enforcement (Priority: P1)

The cloud VM never receives credentials for email, banking, Odoo, or social media. When the cloud agent determines an action is needed, it writes a signal to `Signals/` or a plan to `Plans/`. The local agent reads the signal, applies its locally-held credentials to execute the action, and logs the result. The cloud VM can be fully compromised without exposing any execution credentials.

**Why this priority**: The cloud boundary is the primary security guarantee of the Platinum architecture. If credentials leak to the cloud, the entire system's security model collapses. This must be verifiable by inspection, not just by trust.

**Independent Test**: Review the cloud VM's file system and running processes. Verify no `.env` file, API token, session cookie, or credential of any kind exists on the cloud VM. Trigger a full email + social + payment workflow and confirm all MCP calls originate from the local machine process list.

**Acceptance Scenarios**:

1. **Given** the cloud agent is configured, **When** its configuration is inspected, **Then** no `.env` file, API keys, session cookies, or execution credentials are present on the cloud VM.
2. **Given** the cloud agent generates a plan requiring an email send, **When** it writes the plan, **Then** it writes a `Plans/PLAN_*.md` and a `Pending_Approval/APPROVAL_*.md`; it does NOT call Email MCP.
3. **Given** a simulated cloud VM breach scenario (attacker has root on cloud VM), **When** the attacker attempts to execute an email, payment, or social post, **Then** no MCP server is reachable from the cloud VM; no credentials are available.
4. **Given** vault sync is configured, **When** the sync mechanism is inspected, **Then** the `.env` file, `watchers/` credential files, and browser session directories are on the sync exclude list and are never transmitted.

---

### User Story 5 — 24/7 Social Media Drafting and Scheduled Publishing (Priority: P2)

The cloud agent drafts a LinkedIn post at an optimal time (e.g., Tuesday 9 AM), writes the draft to `Plans/` and the approval to `Pending_Approval/`. Vault sync delivers these to the local machine. The owner reviews and approves during their morning routine. The local agent publishes via Social MCP at the approved time. The cloud agent monitors engagement data and prepares a summary for the next CEO briefing.

**Why this priority**: Social media consistency at optimal times is a business differentiator. Manual posting at 3 AM is not viable; cloud-assisted drafting with local approval makes it possible.

**Independent Test**: Configure a recurring social post schedule. Trigger a cloud-initiated draft. Verify `Plans/PLAN_*_social.md` and `Pending_Approval/APPROVAL_*_social.md` are created by the cloud agent, synced to local, approved by the owner, and executed by the local agent — all without any manual invocation beyond the approval step.

**Acceptance Scenarios**:

1. **Given** a social post is scheduled on the cloud, **When** the trigger fires, **Then** the cloud agent writes the draft to `Plans/` and the approval to `Pending_Approval/`; no platform API is called from the cloud.
2. **Given** the approval is moved to `Approved/` on the local machine, **When** vault sync propagates and the local Approval Watcher detects it, **Then** the local agent publishes via Social MCP and logs the result.
3. **Given** the scheduled time has passed but the owner has not approved the post, **When** the cloud agent next runs, **Then** it marks the draft as stale and writes a `Signals/STALE_DRAFT_*.md` alert; no auto-publish occurs.

---

### User Story 6 — 15-Principle Constitution Compliance Verification (Priority: P2)

Before any Platinum deployment is declared production-ready, the `constitution-check` skill runs and validates the system against all 15 principles defined in `.specify/memory/constitution.md`. It produces a compliance report listing each principle, its pass/fail status, and — for failures — the specific gap and remediation path. No tier is declared complete until this report shows 15/15 passing.

**Why this priority**: The constitution defines the quality bar for the entire system. Without a machine-checkable compliance gate, compliance is aspirational rather than verified. This is the formal sign-off mechanism for the Platinum tier.

**Independent Test**: Deploy the system, intentionally violate one principle (e.g., write a credential to a vault markdown file), run the `constitution-check` skill, and verify it reports that violation as a failure. Fix the violation, re-run, and verify 15/15 pass.

**Acceptance Scenarios**:

1. **Given** the system is deployed, **When** the `constitution-check` skill runs, **Then** it produces a compliance report covering all 15 principles, each with status PASS or FAIL.
2. **Given** any principle is FAIL, **When** the report is generated, **Then** it includes the specific violation and a remediation description.
3. **Given** all 15 principles pass, **When** the report is generated, **Then** it is written to `Briefings/COMPLIANCE_REPORT_<date>.md` and a summary is included in the next CEO briefing.
4. **Given** a principle check cannot be evaluated automatically, **When** the skill runs, **Then** it marks the principle as NEEDS_MANUAL_REVIEW with instructions for human verification.

---

### User Story 7 — Automated Cloud VM Provisioning and Configuration (Priority: P3)

A new team member (or a disaster recovery scenario) needs to stand up a fresh Platinum deployment. Running the provisioning script on the cloud VM installs all required dependencies, configures the vault sync connection, sets up the cloud agent's scheduled tasks, and starts the cloud watchers — all without manual SSH commands beyond initial credential input.

**Why this priority**: Repeatability and disaster recovery are marks of a production-grade system. Manual setup is a reliability risk and a documentation debt. Automated provisioning is the Platinum tier's deployment standard.

**Independent Test**: Provision a fresh cloud VM from scratch using only the provisioning script and the deployment guide. Verify the cloud agent is operational and processing tasks within 30 minutes of running the script.

**Acceptance Scenarios**:

1. **Given** a fresh cloud VM, **When** the provisioning script runs, **Then** all required software is installed, vault sync is configured, and the cloud watchers start without manual intervention.
2. **Given** the cloud agent is running, **When** its health endpoint is queried, **Then** it returns a status confirming all watchers are active and vault sync is operational.
3. **Given** the cloud VM is reprovisioned, **When** it reconnects to the vault sync, **Then** it recovers the current vault state from the local machine without data loss or duplication.

---

### User Story 8 — Cloud-Hosted Odoo with Draft Accounting Actions (Priority: P2)

The cloud VM hosts Odoo Community 24/7, accessible via HTTPS with automated daily backups. The cloud agent creates draft invoices and expenses in Odoo (via a cloud-side `odoo-mcp` in draft-only mode) without human intervention. Draft records are written to the vault as approval tasks; when the owner approves on the local machine, the local agent posts the invoice via its full-permission `odoo-mcp` connecting to cloud Odoo over HTTPS. The cloud agent monitors Odoo service health and alerts on outages or backup failures.

**Why this priority**: Deploying Odoo on the cloud VM is an explicit Platinum requirement. It makes accounting operations available 24/7 without the local machine being online, while the local approval gate preserves the no-autonomous-execution invariant for irreversible financial actions.

**Independent Test**: Suspend the local machine. Drop a `Needs_Action/ODOO_DRAFT_invoice_test.md` task on the cloud VM. Verify the cloud agent creates a draft invoice in cloud Odoo within 5 minutes (visible at `https://<cloud-vm>/web#action=account.action_move_in_invoice_type`) and writes `Pending_Approval/APPROVAL_*_odoo.md`. Unsuspend the local machine; after vault sync, approve the file. Verify the local agent calls `post_invoice` via local `odoo-mcp` and the invoice status changes to `posted`. Verify cloud VM serves HTTPS and `/opt/odoo-backups/` contains a backup file dated today.

**Acceptance Scenarios**:

1. **Given** the cloud agent receives an `ODOO_DRAFT_*.md` task, **When** `cloud-triage` processes it, **Then** a draft invoice or expense is created in cloud Odoo via cloud-side `odoo-mcp`, `Plans/PLAN_*_odoo.md` is written, and `Pending_Approval/APPROVAL_*_odoo.md` is written; no `post_invoice` call is made from the cloud VM.
2. **Given** the owner moves `APPROVAL_*_odoo.md` to `Approved/` on the local machine, **When** the local Approval Watcher detects the move, **Then** the local agent calls `post_invoice` on cloud Odoo via local-side `odoo-mcp` (connecting over HTTPS) and logs the result with `executing_agent=local`.
3. **Given** the cloud VM is provisioned, **When** its Odoo service is inspected, **Then** it serves HTTPS on port 443 with a valid TLS certificate, port 80 redirects to HTTPS, and `/opt/odoo-backups/` contains at least one backup file per day with ≥ 7-day retention.
4. **Given** the cloud agent's health check runs, **When** the Odoo HTTPS endpoint does not respond within 10 seconds, **Then** a `Signals/SIGNAL_odoo_down_<ts>.md` is written with `severity=warning`; the cloud agent skips `ODOO_DRAFT_*` tasks until the service recovers; the local agent is unaffected and can still post invoices via HTTPS if Odoo recovers.
5. **Given** a daily backup cron job runs, **When** the `pg_dump` fails, **Then** a `Signals/SIGNAL_backup_failed_<ts>.md` is written with `severity=warning` and `requires_human_action=true`.

---

### Edge Cases

- **Cloud agent claims a task, then cloud VM loses power**: The `In_Progress/cloud/` task file is stranded. A local watchdog detects tasks stalled in `In_Progress/cloud/` beyond the configured timeout (default: 10 minutes) and returns them to `Needs_Action/`, writing a `Signals/RECOVERED_TASK_*.md` alert.
- **Vault sync conflict on the same file**: Local machine wins for Dashboard.md, Approved/, Rejected/, Done/. Cloud VM wins for Updates/, Signals/, Plans/. All other conflicts produce a `Signals/SYNC_CONFLICT_*.md` for human review — no silent overwrite.
- **Network partition lasting more than 30 minutes**: Both agents continue operating independently. Cloud queues writes to a local buffer. Local queues writes similarly. When connectivity resumes, changes are merged in timestamp order. No events are lost.
- **Cloud VM runs out of disk space**: Vault sync detects write failure and writes a `Signals/DISK_ALERT_*.md`. Cloud agent pauses vault writes (not reads) until the alert is resolved. Local agent continues unaffected.
- **Owner moves an approval file on both machines before sync completes**: The first file-move timestamp wins. The second machine's move is detected as a conflict; the duplicate is archived to `Rejected/DUPLICATE_*.md` with a conflict note.
- **Constitution check reveals a violation introduced by a recent change**: The check writes a `Needs_Action/COMPLIANCE_FAIL_*.md` with the failing principle and the offending component. No automated rollback occurs; human review is required.
- **Cloud agent generates a plan for an action that requires local-only credentials**: The plan references the required MCP tool but contains no credentials. The local agent validates the plan is executable before writing the approval file. If the required MCP is misconfigured locally, the local agent writes `Needs_Action/ERROR_*.md`.
- **Vault sync excludes a file the cloud agent needs**: Cloud agent detects a missing expected file (e.g., `Company_Handbook.md`), writes `Signals/MISSING_VAULT_FILE_*.md`, and pauses tasks that depend on the missing file until the owner resolves the sync-exclude configuration.
- **Both agents attempt to write Dashboard.md simultaneously**: The Single Writer Rule (Principle VII) is enforced by the local agent exclusively writing Dashboard.md. The cloud agent never writes to Dashboard.md under any circumstances. If a cloud agent write to Dashboard.md is detected, it is treated as a configuration error and generates a `Signals/SINGLE_WRITER_VIOLATION_*.md` alert.
- **Cloud Odoo service is down when a draft task arrives**: The cloud agent's health check detects the outage and writes `Signals/SIGNAL_odoo_down_<ts>.md`. All `ODOO_DRAFT_*` tasks remain in `Needs_Action/` unclaimed until Odoo recovers. The local agent's posting capability (via HTTPS to cloud Odoo) is also blocked while Odoo is down; if a posting approval is received during the outage, the local agent writes `Needs_Action/ERROR_odoo_unavailable_*.md` and retries with exponential backoff (max 3 attempts).
- **TLS certificate expires on cloud Odoo**: The cloud agent's health check detects certificate expiry within 14 days and writes `Signals/SIGNAL_cert_expiry_<ts>.md` with `severity=warning`. If the certificate is already expired, `severity=critical` and all Odoo tasks are suspended.

---

## Requirements *(mandatory)*

### Cloud Agent Responsibilities

- **FR-001**: The cloud agent MUST run continuously (24/7) on a remote VM and process new vault tasks without requiring the local machine to be online.
- **FR-002**: The cloud agent MUST claim tasks from `Needs_Action/` using the claim-by-move rule: move the file to `In_Progress/cloud/` before processing.
- **FR-003**: The cloud agent MUST write exclusively to these vault locations: `Plans/`, `Updates/`, `Signals/`, `Needs_Action/` (new task creation only, not modification of claimed tasks), and `In_Progress/cloud/`.
- **FR-004**: The cloud agent MUST NEVER write to `Dashboard.md`, `Done/`, `Approved/`, `Rejected/`, or any MCP execution log.
- **FR-005**: The cloud agent MUST NEVER call any MCP server that executes a final, irreversible action (email send, social post, payment, Odoo invoice post). The sole permitted cloud MCP call is cloud-side `odoo-mcp` in draft-only mode (see FR-068–FR-074); posting, payment, and all other execution operations remain local-only.
- **FR-006**: The cloud agent MUST detect tasks stranded in `In_Progress/cloud/` beyond the configured stale-task timeout and return them to `Needs_Action/` with a recovery signal.
- **FR-007**: The cloud agent MUST include a Gmail watcher that polls for new emails and creates structured `Needs_Action/EMAIL_*.md` files, using the same idempotency mechanism as the local Gmail watcher.
- **FR-008**: The cloud agent MUST include a filesystem watcher monitoring `Signals/` for alert files written by the local agent, enabling the cloud to respond to local events.
- **FR-009**: The cloud agent's scheduled tasks (social post drafting, briefing data preparation) MUST be configurable via a cron-compatible schedule without code changes.
- **FR-010**: The cloud agent MUST write a heartbeat entry to `Updates/HEARTBEAT_*.md` every 5 minutes to indicate it is alive; absence of a heartbeat for 10 minutes MUST trigger a `Signals/CLOUD_AGENT_DOWN_*.md` alert on the local machine.

### Local Agent Responsibilities

- **FR-011**: The local agent MUST be the exclusive executor of all MCP calls that produce irreversible results: email send, social post, payment, Odoo invoice post, WhatsApp send.
- **FR-012**: The local agent MUST be the exclusive writer of `Dashboard.md`.
- **FR-013**: The local agent MUST be the exclusive mover of files into `Done/`, `Approved/`, and `Rejected/` (except for human-initiated moves to `Approved/` and `Rejected/`).
- **FR-014**: The local agent MUST read `Updates/`, `Signals/`, and `Plans/` from the cloud agent and act on their contents according to the same skill logic used for locally-generated tasks.
- **FR-015**: The local agent MUST run Email, Social, and Browser MCP servers exclusively on the local machine. The `odoo-mcp` is deployed on both machines: cloud VM in draft-only mode (FR-072) and local machine in full mode. No execution MCP server (email send, social post, payment) MUST be accessible from the cloud VM.
- **FR-016**: The local agent MUST include all watchers from the Gold tier (WhatsApp, Finance, Approval, Filesystem) that require local credentials or browser sessions.
- **FR-017**: The local agent MUST validate that cloud-prepared plans reference only locally-available MCP tools before writing approval files; plans referencing unavailable tools MUST produce `Needs_Action/ERROR_*.md`.
- **FR-018**: The local agent MUST monitor `In_Progress/cloud/` for stale tasks (beyond configurable timeout) and return them to `Needs_Action/` with a recovery signal.
- **FR-019**: The local agent MUST detect the cloud agent's heartbeat absence and write `Needs_Action/ERROR_CLOUD_AGENT_DOWN_*.md` if no heartbeat has appeared within 10 minutes.
- **FR-020**: The local agent MUST update `Dashboard.md` to reflect cloud agent status (ONLINE, DEGRADED, OFFLINE) based on heartbeat data.

### Vault Synchronisation

- **FR-021**: The system MUST implement bidirectional vault synchronisation between the local machine and cloud VM with a maximum end-to-end propagation latency of 60 seconds under normal network conditions.
- **FR-022**: The sync mechanism MUST exclude the following from cloud transmission: `.env` files, browser session directories, WhatsApp session data, OS credential store references, and any file matching the secrets exclusion list defined in `sync-config.md`.
- **FR-023**: The sync mechanism MUST produce an audit trail entry in `Sync/sync.log` for every sync operation, recording: timestamp, direction, files changed, bytes transferred, and any conflicts detected.
- **FR-024**: The sync mechanism MUST implement conflict resolution with these rules:
  - **Local wins** (authoritative): `Dashboard.md`, `Done/`, `Approved/`, `Rejected/`
  - **Cloud wins** (authoritative): `Updates/`, `Signals/`
  - **Conflict alert**: all other files — write `Signals/SYNC_CONFLICT_*.md` for human resolution.
- **FR-025**: The sync mechanism MUST buffer writes locally during network partitions and apply them when connectivity is restored, maintaining file ordering by creation timestamp.
- **FR-026**: The sync mechanism MUST verify file integrity (checksum) after each transfer; a failed checksum MUST trigger a re-transfer and write `Signals/SYNC_INTEGRITY_FAIL_*.md`.
- **FR-027**: The sync configuration file (`sync-config.md` in vault root, readable by both agents) MUST document: sync interval, excluded paths, conflict resolution rules, and retry policy. This file MUST be maintained manually by the owner and treated as immutable by both agents.
- **FR-028**: The sync process MUST be independently startable and stoppable without affecting watcher processes or agent operations.
- **FR-029**: When the cloud VM is first provisioned, the sync initialisation MUST perform a full vault copy from local to cloud, establishing the cloud as a consistent replica before the cloud agent starts processing tasks.
- **FR-030**: The sync process MUST enforce a mutual-exclusion lock (`Sync/sync.lock`) preventing concurrent sync operations from corrupting the vault.

### Multi-Agent Coordination

- **FR-031**: Both agents MUST implement the claim-by-move rule using their respective `In_Progress/` subdirectories (`In_Progress/local/`, `In_Progress/cloud/`).
- **FR-032**: Both agents MUST skip any task file found in `In_Progress/cloud/` or `In_Progress/local/` on their task scan — claimed tasks are not re-claimed.
- **FR-033**: A task stalled in `In_Progress/<agent>/` beyond the configurable timeout (default: 10 minutes) MUST be returned to `Needs_Action/` by the monitoring agent (either cloud or local); a `Signals/RECOVERED_TASK_*.md` entry MUST be written.
- **FR-034**: When the cloud agent completes drafting a plan for a task, it MUST update the task file's metadata (add a `plan_ref` field) and move the task to `In_Progress/local/` to signal that the local agent should proceed to execution planning.
- **FR-035**: Dashboard.md MUST include two separate counters: `In_Progress_Local: N` and `In_Progress_Cloud: N`, reflecting real-time ownership distribution.

### 15-Principle Constitution Compliance

- **FR-036**: The system MUST include a `constitution-check` skill that validates each of the 15 constitution principles by inspecting vault structure, skill files, configuration, and watcher code.
- **FR-037**: The compliance report MUST list each principle by number and name, its status (PASS / FAIL / NEEDS_MANUAL_REVIEW), and — for non-PASS — a specific finding and remediation path.
- **FR-038**: The `constitution-check` skill MUST be runnable on demand and MUST be run as part of any tier-completion gate check.
- **FR-039**: A compliance report with any FAIL status MUST create a `Needs_Action/COMPLIANCE_FAIL_*.md` task for the local agent to process.
- **FR-040**: A fully passing compliance report (15/15 PASS or NEEDS_MANUAL_REVIEW with human sign-off) MUST be written to `Briefings/COMPLIANCE_REPORT_<date>.md` and linked in the next CEO briefing's Executive Summary section.

### Deployment Architecture

- **FR-041**: The cloud VM MUST run a supported Linux distribution with the minimum required runtime environment documented in the deployment guide.
- **FR-042**: All cloud VM dependencies (agent runtime, watchers, vault sync process) MUST be installable via a single provisioning script that completes without interactive prompts (after initial credential input).
- **FR-043**: The provisioning script MUST validate its own success by running a smoke test: creating a synthetic `Needs_Action/` task, verifying it is claimed by the cloud agent within 2 minutes, and verifying the plan propagates to local via sync.
- **FR-044**: The cloud VM MUST have its system clock synchronised (NTP or equivalent); clock skew greater than 1 second between cloud and local MUST trigger a `Signals/CLOCK_SKEW_ALERT_*.md`.
- **FR-045**: The cloud agent MUST support graceful shutdown (all in-progress tasks moved back to `Needs_Action/` before process exit) triggered by a `Signals/SHUTDOWN_CLOUD_*.md` signal file written by the local agent.
- **FR-046**: The deployment MUST document: minimum VM specifications (CPU, RAM, storage), required open ports, expected monthly cost range, and disaster recovery procedure.
- **FR-047**: Credentials on the cloud VM MUST be limited to: vault sync authentication token, Gmail API read-only OAuth token (no send), cloud VM SSH key, and Odoo database credentials for the cloud-hosted Odoo instance (accessed via cloud-side `odoo-mcp` in draft-only mode). No email send, social media, payment, banking, or WhatsApp credentials MUST be present on the cloud VM.

### Cloud Odoo Deployment

- **FR-068**: The cloud VM MUST host a running Odoo Community instance; the service MUST be accessible via HTTPS on port 443 with a valid TLS certificate; HTTP traffic on port 80 MUST redirect to HTTPS.
- **FR-069**: The TLS certificate on cloud Odoo MUST be automatically renewed (Let's Encrypt or equivalent); certificate expiry within 14 days MUST trigger `Signals/SIGNAL_cert_expiry_<ts>.md` with `severity=warning`; an already-expired certificate MUST trigger `severity=critical` and suspend all Odoo tasks.
- **FR-070**: The cloud VM MUST run automated daily Odoo database backups using `pg_dump`; backups MUST be retained for a minimum of 7 days under `/opt/odoo-backups/`; a failed backup MUST write `Signals/SIGNAL_backup_failed_<ts>.md` with `requires_human_action=true`.
- **FR-071**: The cloud agent MUST include an Odoo health check in its startup sequence and in the `vault-health` skill: verify the Odoo HTTPS endpoint responds within 10 seconds; on failure write `Signals/SIGNAL_odoo_down_<ts>.md` with `severity=warning` and skip all `ODOO_DRAFT_*` tasks until recovery is confirmed.
- **FR-072**: The cloud VM MUST host a cloud-side `odoo-mcp` instance configured in **draft-only mode**: only `create_invoice` (status=draft) and `update_expense` (status=draft) operations are exposed in the cloud instance's tool registry; `post_invoice`, `create_transaction`, and `sync_transaction` MUST NOT be registered as available tools in the cloud-side `odoo-mcp`.
- **FR-073**: The local agent's `odoo-mcp` instance MUST connect to the cloud Odoo instance via HTTPS and retains all tool operations including `post_invoice`, `create_transaction`, and `sync_transaction`; it is the only component permitted to call these posting operations.
- **FR-074**: The `constitution-check` skill MUST verify cloud Odoo compliance: (a) the cloud Odoo HTTPS endpoint responds; (b) backup files exist in `/opt/odoo-backups/` with at least one file dated within the last 25 hours; (c) the cloud `odoo-mcp` tool registry does not expose `post_invoice`, `create_transaction`, or `sync_transaction`; (d) the operational audit log contains no `post_invoice` entries with `actor` matching a cloud agent identity.
- **FR-053** (amended): `cloud-triage` skill — runs on the cloud agent; reads new task files, classifies them, drafts a response plan, and writes `Plans/` and `Signals/` entries. MAY call cloud-side `odoo-mcp` for draft-only operations (`create_invoice`, `update_expense` in draft status); MUST NOT call any execution MCP (email send, social post, payment, `post_invoice`).

### Vault Folder Structure (Platinum additions)

The following folders are added to the Gold-tier vault structure:

- **FR-048**: `Updates/` — cloud agent writes status and progress entries; local agent reads only.
- **FR-049**: `Signals/` — bidirectional signal channel; either agent may write alert files; both agents read and respond.
- **FR-050**: `In_Progress/cloud/` — tasks currently owned by the cloud agent.
- **FR-051**: `In_Progress/local/` — tasks currently owned by the local agent (replaces the flat `In_Progress/<agent>/` from Gold).
- **FR-052**: `Sync/` — sync metadata (sync.lock, sync.log); managed exclusively by the sync process, not by agents.

### Claude Skills (Platinum additions to Gold)

- **FR-053**: `cloud-triage` skill — runs on the cloud agent; reads new task files, classifies them, drafts a response plan, and writes `Plans/` and `Signals/` entries. MUST NOT call any execution MCP.
- **FR-054**: `vault-health` skill — runs on both agents; validates vault folder structure integrity, detects stale tasks, verifies sync.log recency, and writes a health summary to `Updates/VAULT_HEALTH_*.md`.
- **FR-055**: `constitution-check` skill — runs on the local agent; performs principle-by-principle compliance validation and writes the compliance report.
- **FR-056**: `cloud-briefing-prep` skill — runs on the cloud agent; gathers signals, social activity data, and performance metrics from the vault and writes a structured `Updates/BRIEFING_DATA_<date>.md`; the local `ceo-briefing` skill reads this to assemble the final CEO briefing.
- **FR-057**: All existing Gold-tier skills (`process-needs-action`, `ceo-briefing`, `linkedin-post`, `facebook-post`, `instagram-post`, `twitter-post`, `execute-plan`, `finance-triage`, `odoo-integration`, `whatsapp-reply`, `email-queue-manager`) MUST continue operating without modification on the local agent.
- **FR-058**: Each new Platinum skill MUST be created or updated using the `skill-creator` skill before implementation begins.

### Testing Strategy

- **FR-059**: The test suite MUST include a **local smoke test** for each watcher: simulate an inbound event, verify the correct `Needs_Action/` file is created within SLA, and verify idempotency on re-run.
- **FR-060**: The test suite MUST include a **multi-agent coordination test**: run both agents simultaneously, drop 10 tasks into `Needs_Action/`, and verify each task is processed exactly once with no duplicates and no stranded files.
- **FR-061**: The test suite MUST include a **vault sync latency test**: measure propagation time for a synthetic write from cloud to local and local to cloud; verify both directions complete within 60 seconds.
- **FR-062**: The test suite MUST include a **security boundary test**: inspect the cloud VM file system and process list, verifying zero execution credentials are present.
- **FR-063**: The test suite MUST include a **single-writer test**: attempt a simulated cloud agent write to `Dashboard.md`; verify the write is blocked or the resulting conflict alert is generated.
- **FR-064**: The test suite MUST include an **end-to-end approval flow test** spanning cloud and local: cloud creates plan → sync → local creates approval → owner approves → local executes → audit log entry verified.
- **FR-065**: The test suite MUST include a **disaster recovery test**: simulate cloud VM restart mid-task; verify the stale-task recovery mechanism returns the task to `Needs_Action/` within the configured timeout.
- **FR-066**: The test suite MUST include a **constitution compliance test**: deploy the system, run `constitution-check`, verify all 15 principles report PASS or NEEDS_MANUAL_REVIEW; intentionally violate one principle and verify it appears as FAIL in the report.
- **FR-067**: All test results MUST be written to `Logs/TEST_RESULTS_<date>.json` using the same audit log schema as operational logs.

### MCP Servers

Email, Social, and Browser MCP servers remain on the local machine, unchanged from Gold. The `odoo-mcp` server is extended for Platinum with a dual-mode deployment:

- **Cloud VM (draft-only)**: A cloud-side `odoo-mcp` instance connects to the locally-hosted cloud Odoo via `http://localhost:8069`. It exposes only `create_invoice` (draft) and `update_expense` (draft) in its tool registry. `post_invoice`, `create_transaction`, and `sync_transaction` are absent from this instance.
- **Local machine (full)**: The existing local-side `odoo-mcp` connects to cloud Odoo via `https://<CLOUD_VM_HOST>/jsonrpc` and retains all operations. It is the only component permitted to post invoices or execute financial transactions.

No other MCP servers are added in Platinum. Email, Social, and Browser MCP servers remain local-only; the cloud agent never calls them.

### Watchers

| Watcher | Runs On | Purpose |
|---------|---------|---------|
| Gmail Watcher | Cloud VM (primary), Local (fallback) | Detect new emails 24/7 |
| Filesystem Watcher (`Inbox/`) | Local | File drop detection |
| Filesystem Watcher (`Signals/`) | Both | Cross-agent signal detection |
| WhatsApp Watcher | Local | Browser session maintained locally |
| Finance Watcher | Local | Bank transaction detection (credentials local-only) |
| Approval Watcher | Local | Detect `Approved/` and `Rejected/` moves |
| Heartbeat Monitor | Local | Detect cloud agent heartbeat absence |
| Stale Task Monitor | Both | Detect `In_Progress/` timeouts |
| Odoo Health Check | Cloud VM | Verify Odoo HTTPS endpoint + TLS expiry + backup recency; write `SIGNAL_odoo_down_*.md` or `SIGNAL_cert_expiry_*.md` on failure |

---

### Key Entities

All Gold-tier entities are inherited. Platinum adds:

- **Cloud Signal** (`Signals/TYPE_TIMESTAMP.md`): Alert or trigger written by either agent. Key attributes: signal_type, originating_agent, created, severity, message, requires_human_action (boolean).
- **Agent Update** (`Updates/TYPE_TIMESTAMP.md`): Status report written by the cloud agent. Key attributes: update_type (heartbeat, plan_complete, briefing_data, vault_health), created, summary, linked_plan (optional).
- **Sync Log Entry** (`Sync/sync.log`): Append-only record of each sync operation. Key attributes: timestamp, direction (local→cloud | cloud→local), files_changed, bytes_transferred, conflicts_detected, duration_ms.
- **Compliance Report** (`Briefings/COMPLIANCE_REPORT_<date>.md`): Output of the `constitution-check` skill. Key attributes: check_date, overall_status, principle_results (list of 15 items each with number, name, status, finding, remediation).
- **Briefing Data** (`Updates/BRIEFING_DATA_<date>.md`): Cloud-prepared structured data for the CEO briefing. Key attributes: period, signal_summary, social_activity, vault_health_snapshot, cloud_agent_uptime.
- **Heartbeat** (`Updates/HEARTBEAT_<timestamp>.md`): Cloud agent liveness signal. Key attributes: agent_id, timestamp, tasks_in_progress, last_processed_task_ref.

---

## Non-Functional Requirements

### Reliability

- **NFR-001** (inherited): Watcher processes achieve ≥ 99% uptime during configured operating hours.
- **NFR-002**: The cloud agent MUST achieve ≥ 99.5% uptime over any rolling 7-day window, measured by heartbeat presence.
- **NFR-003**: Stale tasks in `In_Progress/<agent>/` MUST be detected and returned to `Needs_Action/` within 2× the configured stale-task timeout (maximum: 20 minutes at default settings).
- **NFR-004**: Vault sync MUST successfully propagate all non-excluded file changes within 60 seconds under normal network conditions (< 100ms round-trip latency between cloud and local).
- **NFR-005**: No task file MUST be processed more than once across both agents combined (zero-duplicate guarantee).
- **NFR-006** (inherited): Banking actions have zero unintended executions; all payments require explicit approval.

### Performance

- **NFR-007**: A new inbound email detected by the cloud agent MUST result in a cloud-prepared plan in `Plans/` within 5 minutes of email arrival.
- **NFR-008** (inherited): CEO briefing generated within 10 minutes of scheduled trigger.
- **NFR-009** (inherited): Dashboard.md updated within 30 seconds of any task state transition.
- **NFR-010**: Cloud agent heartbeat latency to local detection MUST be ≤ 10 minutes (5-minute heartbeat + 5-minute grace).
- **NFR-011**: The provisioning script MUST complete a full cloud VM setup (software install + vault sync initialisation + watcher start) in under 30 minutes.

### Security

- **NFR-012** (inherited): All credentials in `.env` or OS keychain; never in vault markdown files.
- **NFR-013** (inherited): `DRY_RUN=true` is the default.
- **NFR-014**: The cloud VM execution credential set is strictly bounded. Permitted secrets: vault sync authentication token, Gmail API read-only OAuth token (no send permission), and Odoo database credentials for the cloud-hosted Odoo instance. Prohibited on cloud VM: email send credentials, social media API tokens, payment or banking credentials, and WhatsApp sessions. All prohibited credentials are local-only.
- **NFR-015**: Vault sync transport MUST use encrypted channels (TLS/SSH); plaintext sync is prohibited.
- **NFR-016**: The sync exclusion list MUST be version-controlled and reviewed as part of any deployment change.
- **NFR-017** (inherited): Rate limits: max 10 outbound emails/hour, max 3 payment actions/hour.
- **NFR-018**: The cloud VM inbound ports MUST be limited to: SSH (restricted to owner IP range), vault sync port if required by the sync mechanism, and HTTPS port 443 (for the cloud-hosted Odoo instance, accessible to the local machine and the owner's browser). No other public-facing services on the cloud VM. Port 80 is open only for HTTP→HTTPS redirect.

### Modularity

- **NFR-019** (inherited): All agent logic in discrete skills; no ad-hoc reasoning outside skills.
- **NFR-020** (inherited): Each MCP server independently startable/stoppable.
- **NFR-021**: The cloud agent and local agent MUST be independently deployable; upgrading one MUST NOT require simultaneously upgrading the other, as long as the vault schema is backward-compatible.
- **NFR-022**: Adding a new watcher to the cloud VM MUST require no changes to the local agent or any local watcher.

### Observability

- **NFR-023** (inherited): Dashboard.md provides at-a-glance task state counts.
- **NFR-024** (inherited): Logs queryable for 90-day lookback.
- **NFR-025**: Dashboard.md MUST include a Cloud Agent section showing: status (ONLINE/DEGRADED/OFFLINE), last heartbeat timestamp, tasks in `In_Progress/cloud/` count, last 3 updates from `Updates/`.
- **NFR-026**: Sync operations MUST be summarised in Dashboard.md: last successful sync timestamp, direction, files changed in last sync, and any pending conflicts.
- **NFR-027**: The compliance report MUST be linked from Dashboard.md with its overall status and check date.

### Local-First Architecture

- **NFR-028** (inherited): System functions without continuous internet for vault read/write; only MCP action calls and vault sync require network.
- **NFR-029**: When the cloud VM is unreachable, the local agent MUST continue operating fully for all execution tasks; it MUST use the local Gmail watcher as fallback if the cloud Gmail watcher has been the primary.
- **NFR-030**: The local machine MUST be able to process all pending vault tasks without any cloud agent assistance; cloud is an enhancement, not a dependency for basic operation.

### Documentation

- **NFR-031** (inherited): Every folder, module, watcher, skill, and MCP server must have documentation.
- **NFR-032**: The Platinum deployment MUST include an architecture diagram (or equivalent ASCII representation) showing the cloud/local split, vault sync pathway, and data flows for the three primary scenarios: cloud triage, multi-agent coordination, and HITL approval.
- **NFR-033**: The deployment guide MUST document: step-by-step cloud VM provisioning, vault sync configuration, credential setup, and how to verify the system is operating correctly after deployment.

---

## Data Schemas

### Cloud Signal File Schema

```
---
signal_id: SIGNAL_<timestamp>
signal_type: task_recovered | cloud_down | sync_conflict | stale_draft | disk_alert |
             clock_skew | vault_missing_file | single_writer_violation | shutdown_request
originating_agent: cloud | local
created: <ISO-8601Z>
severity: info | warning | critical
requires_human_action: true | false
linked_ref: <path to related task/plan/approval or null>
---

## Signal Message
<plain-language description of the condition>

## Recommended Action
<what the receiving agent or owner should do>
```

### Agent Heartbeat File Schema

```
---
heartbeat_id: HEARTBEAT_<timestamp>
agent_id: cloud_agent
created: <ISO-8601Z>
tasks_in_progress: <integer>
last_processed_task_ref: <path or null>
vault_sync_last_ok: <ISO-8601Z or null>
watcher_status:
  gmail: running | stopped | error
  signals: running | stopped | error
---
```

### Sync Log Entry (append-only plain-text line in `Sync/sync.log`)

```
<ISO-8601Z> | direction=<local→cloud|cloud→local> | files_changed=<N> | bytes=<N> |
conflicts=<N> | duration_ms=<N> | status=<ok|conflict|error>
```

### Compliance Report Schema

```
---
report_id: COMPLIANCE_<YYYY-MM-DD>
check_date: YYYY-MM-DD
generated_by: constitution-check skill
overall_status: PASS | FAIL | PARTIAL
principles_pass: <0-15>
principles_fail: <0-15>
principles_manual_review: <0-15>
---

# Platinum Compliance Report — <date>

## Overall Status: <PASS | FAIL | PARTIAL>

## Principle Results

| # | Principle | Status | Finding |
|---|-----------|--------|---------|
| I | Production First | PASS / FAIL / NEEDS_MANUAL_REVIEW | <finding or "—"> |
| II | Local First | PASS / FAIL / NEEDS_MANUAL_REVIEW | <finding or "—"> |
...

## Remediation Items
<list of FAIL items with specific gap and remediation path>

## Manual Review Items
<list of NEEDS_MANUAL_REVIEW items with human verification instructions>
```

### Briefing Data File Schema (cloud-prepared, local-consumed)

```
---
briefing_data_id: BRIEFING_DATA_<YYYY-MM-DD>
period_start: YYYY-MM-DD
period_end: YYYY-MM-DD
generated_at: <ISO-8601Z>
generated_by: cloud_agent
---

## Signal Summary
<list of notable signals from the period>

## Cloud Agent Uptime
- Uptime percentage: <N>%
- Downtime events: <list or "none">

## Social Activity (from Logs/)
| Platform | Posts | Engagement |
|----------|-------|-----------|
...

## Vault Health Snapshot
<summary from latest vault-health run>
```

### Extended Audit Log Entry (adds cloud-specific fields)

```json
{
  "timestamp": "ISO-8601Z",
  "action_type": "email_send | social_post | payment | odoo_sync | file_move | vault_sync | ...",
  "actor": "cloud_agent | local_agent | watcher_gmail_cloud | watcher_signals | ...",
  "target": "<recipient, URL, or resource identifier>",
  "parameters": {},
  "approval_status": "approved | auto | pending",
  "approved_by": "human | system",
  "result": "success | failure",
  "error_message": "<string or null>",
  "originating_agent": "cloud | local",
  "executing_agent": "local"
}
```

---

## Assumptions

1. The Gold tier is fully operational before Platinum work begins; all Gold-tier skills, watchers, and MCP servers are in production state.
2. The cloud VM has reliable network access to the vault sync endpoint (local machine or shared sync service); average round-trip latency is below 100ms.
3. The owner configures the vault sync mechanism once during initial deployment; the sync process runs automatically thereafter.
4. The Gmail API credentials provisioned for the cloud agent are read-only (fetch/search only); the cloud agent does not have send permissions.
5. The owner's local machine is the single authoritative source of truth; the cloud VM is always treated as a replica that can be destroyed and re-provisioned.
6. The Obsidian vault is accessible from both machines via the sync mechanism; the owner's Obsidian GUI operates only on the local vault copy.
7. The cloud VM's storage is sufficient to hold the full vault replica plus 90 days of log files; storage monitoring is the owner's responsibility.
8. `Company_Handbook.md` and `Business_Goals.md` are maintained on the local machine and synced to the cloud; the cloud agent reads them but never modifies them.
9. The vault sync mechanism handles binary-safe line-ending conversion between operating systems; no manual normalisation is required.
10. The stale-task timeout (default: 10 minutes) is configurable via `sync-config.md` without code changes.
11. The cloud Odoo instance is reachable from the local machine's `odoo-mcp` via HTTPS; firewall rules permit port 443 inbound from the local machine's IP. The Odoo database credentials used by the cloud-side `odoo-mcp` are stored in `/root/.env.cloud` (gitignored) and are never synced to the local machine.

---

## Out of Scope

- Multi-cloud deployment (second cloud VM or multi-region failover).
- Real-time streaming sync (sub-5-second propagation); 60-second SLA is the Platinum target.
- Mobile device integration (push notifications, mobile app).
- Voice interface or natural language command input beyond the vault file protocol.
- Machine learning model fine-tuning or custom model training.
- Third-party SaaS database (all state remains in the vault).
- Automated financial trading or fully autonomous payment execution.
- Multi-owner / multi-user access control; single-owner model only.
- Kubernetes, container orchestration, or microservice deployment patterns.
- GitHub Actions or CI/CD pipeline integration for vault content.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The cloud agent processes at least one complete triage + plan-drafting cycle every hour while the local machine is offline, verified by `Updates/` file timestamps.
- **SC-002**: Zero email send, social media, payment, or banking credentials are present on the cloud VM at any time; only permitted cloud secrets (vault sync token, Gmail read-only OAuth, Odoo DB credentials for cloud-hosted instance) are present; verified by security boundary test.
- **SC-003**: Vault sync propagates all non-excluded changes from cloud to local and local to cloud within 60 seconds, verified by latency test over a 24-hour window with ≥ 95% of operations meeting the SLA.
- **SC-004**: Zero duplicate task processing events occur across cloud and local agents combined, verified by multi-agent coordination test over 100 task samples.
- **SC-005**: The `constitution-check` skill reports all 15 principles as PASS or NEEDS_MANUAL_REVIEW (zero FAIL) on a correctly configured Platinum deployment.
- **SC-006**: The cloud VM is provisioned and operational (processing tasks) within 30 minutes of running the provisioning script on a fresh VM, verified by provisioning smoke test.
- **SC-007**: Dashboard.md includes accurate cloud agent status (ONLINE/DEGRADED/OFFLINE) updated within 10 minutes of any cloud agent state change.
- **SC-008**: When the cloud VM is unreachable, the local agent continues processing all task types without degradation, verified by a 30-minute cloud-offline test.
- **SC-009**: A stale task in `In_Progress/cloud/` (simulated by killing the cloud agent mid-task) is detected and returned to `Needs_Action/` within the configured stale-task timeout (default: 10 minutes), verified by disaster recovery test.
- **SC-010**: A full end-to-end flow (cloud triage → vault sync → local approval presentation → owner approval → local execution → audit log) completes within 15 minutes from email arrival to sent reply, for emails processed while the local machine is online.
- **SC-011** (inherited): 100% of sensitive actions require human-approved approval files; zero autonomous executions of payments, new-contact emails, or social posts.
- **SC-012** (inherited): 100% of system actions produce a corresponding audit log entry; zero silent operations.
- **SC-013**: The cloud VM hosts Odoo Community accessible via HTTPS with a valid TLS certificate; HTTP redirects to HTTPS; verified by `constitution-check` skill (FR-074a).
- **SC-014**: Cloud VM daily backup cron produces at least one backup file per day in `/opt/odoo-backups/` across a 7-day verification window; verified by `constitution-check` skill (FR-074b).
- **SC-015**: All `post_invoice` audit log entries have `executing_agent=local`; zero entries have a cloud agent identity in the `actor` field; verified by `constitution-check` skill (FR-074d).
