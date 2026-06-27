<!--
SYNC IMPACT REPORT
==================
Version change  : 2.0.0 → 2.1.0
Bump rationale  : MINOR — Principle III (Cloud Worker) extended to include Odoo draft-only
                  accounting actions as a permitted cloud scope. Platinum compliance gate updated
                  to include cloud-hosted Odoo with HTTPS + backups + health monitoring.
                  No existing principles removed or redefined.

Previous version: 1.1.0 → 2.0.0
Bump rationale  : MAJOR — existing 5-principle structure fully replaced with 15 production-grade
                  principles. Scope elevated from Hackathon prototype to 24/7 production system.
                  All original principles renamed, merged, split, or absorbed into the new set.

Principles removed (subsumed or replaced):
  I.   Skills-First & MCP Architecture → absorbed into IX. Modular Design + X. Agent Skills
  II.  Folder-Based State Machine      → split into V. Vault Driven Architecture
                                         + VI. Claim-by-Move + VII. Single Writer Rule
  III. Human-in-the-Loop Safety        → expanded into IV. Human In The Loop
  IV.  Proactive Business Intelligence → subsumed into III. Cloud Worker; briefing cadence
                                         retained in Hackathon Tier Compliance table
  V.   Security & Operations           → split into XIII. Security + XI. Observability
                                         + XII. Reliability

Principles added (new):
  I.    Production First         — no prototype shortcuts; every feature ships-ready
  II.   Local First              — sensitive data stays on-machine; cloud sees only markdown
  III.  Cloud Worker             — cloud scope: triage, draft, plan, schedule; never final actions
  IV.   Human In The Loop        — replaces old III; all sensitive actions require approval
  V.    Vault Driven Architecture — replaces old II; vault = single source of truth
  VI.   Claim-by-Move            — split from old II; file-move = exclusive ownership
  VII.  Single Writer Rule        — new; Dashboard.md local-only; cloud writes Updates/Signals/Plans/
  VIII. Event Driven              — new; watchers + events; no unnecessary polling
  IX.   Modular Design            — new + old I; each integration isolated and independently testable
  X.    Agent Skills              — new + old I; all AI logic in .claude/skills/; no logic in prompts
  XI.   Observability             — new; every action produces structured log + audit record
  XII.  Reliability               — new; retry, timeout, recovery, watchdog, graceful degradation
  XIII. Security                  — replaces old V; secrets never in vault; cloud never runs finance
  XIV.  Documentation             — new; every folder/module/watcher/skill/MCP documented
  XV.   Code Quality              — new; Clean Architecture, SOLID, DI, strong typing, small modules

Templates reviewed:
  ✅ .specify/templates/plan-template.md      — Constitution Check section is generic and compatible.
  ✅ .specify/templates/spec-template.md      — No principle-specific references; no update needed.
  ✅ .specify/templates/tasks-template.md     — Security/Observability tasks in Phase N; compatible.
  ✅ .specify/templates/phr-template.prompt.md — No changes required.

Deferred TODOs carried over from v1.1.0:
  ⚠ CLAUDE.md HITL section may still reference old checkbox pattern — verify manually.
  ⚠ specs/002-silver-ai-employee/spec.md FR-007 may still reference [ ] APPROVE — update via /sp.specify.

New deferred TODOs:
  ⚠ plan-template.md Constitution Check gate list should enumerate all 15 principles explicitly.
  ⚠ Consider ADR for Local/Cloud split boundary (Principles II + III) — architecturally significant.
  ⚠ CLAUDE.md project description should reference the new 15-principle constitution at v2.0.0.
-->

# Digital FTE Constitution: Platinum Production Standards

## Core Principles

### I. Production First

Every feature MUST be production-oriented. Shortcuts, placeholder architectures, and
demo-only code are prohibited. Every module delivered MUST be deployable, observable,
and maintainable as if it will run 24/7 for a real company.

Rationale: the system operates autonomously on behalf of a real business. A feature
that works only in a demo degrades trust and creates silent failures in production.

### II. Local First

Sensitive data MUST never leave the local machine. The following categories MUST be
stored only on-device:

- WhatsApp sessions and browser cookies
- Banking credentials and payment tokens
- API keys, secrets, and `.env` files
- Any credential used for financial operations

Cloud agents MUST receive only synchronized markdown state (vault files). They MUST
NOT receive raw credentials, session data, or tokens under any circumstances.

### III. Cloud Worker

Cloud agents are scoped to analytical and drafting tasks only:

- Email triage and classification
- Draft generation (email, social, planning)
- Odoo draft-only accounting actions (create draft invoices and expenses; posting or payment requires Local approval)
- Scheduling and background monitoring

Cloud agents MUST NEVER execute final, irreversible actions. All execution gates MUST
be enforced locally. A cloud agent that attempts to send an email, post to social
media, or initiate a payment MUST be treated as a configuration error.

### IV. Human In The Loop

All sensitive actions MUST require explicit human approval before execution. The
following MUST never be executed autonomously:

- Sending emails or WhatsApp messages
- Payments, transfers, or Odoo invoice posting
- Social media publishing (posts, replies, DMs)
- Banking operations of any kind

The mandatory approval gate: skills MUST write an `APPROVAL_*.md` file to
`Pending_Approval/` alongside a `Plans/PLAN_*.md` draft. Execution MUST be blocked
until a human explicitly moves the `APPROVAL_*.md` to `Approved/`. No skill MAY
auto-approve its own request. Files moved to `Rejected/` are archived and MUST never
be re-executed.

### V. Vault Driven Architecture

The Obsidian Vault is the single source of truth for all agent state and long-term
memory. Agents MUST communicate exclusively through markdown files in the vault.
No agent MAY bypass the vault to communicate with another agent directly (e.g., via
sockets, shared memory, or direct function calls across agents).

No external databases are used for operational state. The vault folder structure is
the state machine.

### VI. Claim-by-Move

Task ownership MUST be established by moving the task file from `Needs_Action/` to
`In_Progress/<agent>/`. The first agent to complete this move exclusively owns the
task. All other agents MUST skip any item already claimed. This prevents duplicate
processing without requiring a lock service.

### VII. Single Writer Rule

`Dashboard.md` MUST be modified only by the local agent. Cloud agents MUST write
exclusively into the following directories:

- `Updates/` — status updates and progress reports
- `Signals/` — event triggers and alerts
- `Plans/` — planning artifacts and approval drafts

No cloud agent MAY write directly to `Dashboard.md`, `Done/`, `Approved/`, or
`Rejected/`. Violation of this rule corrupts the authoritative local state.

### VIII. Event Driven

Agents MUST NOT poll unnecessarily. All perception MUST be implemented through
watcher scripts that respond to filesystem events. CPU-idle polling intervals MUST
use `PollingObserver` only when `inotify` is unavailable (e.g., NTFS mounts under
WSL2). Background agents MUST sleep between event cycles and MUST NOT busy-wait.

### IX. Modular Design

Every integration MUST be isolated into its own skill or module. Each integration
MUST be independently testable without requiring other integrations to be active.
Examples of required isolation boundaries:

- Gmail Skill, WhatsApp Skill, LinkedIn Skill, Facebook Skill, Instagram Skill
- Odoo Skill, Health Skill, Audit Skill

No module MAY be a God Object. Each module MUST have a single, well-defined
responsibility. Cross-cutting concerns (logging, retry, auth) MUST be handled
by shared utility libraries, not duplicated per-module.

### X. Agent Skills

All AI reasoning and business logic MUST reside in `.claude/skills/<skill-name>/SKILL.md`.
Watcher scripts are pure perception: they deposit structured `.md` files into
`Needs_Action/` and MUST NOT contain reasoning or decision logic. Business logic
MUST never exist inside raw prompts or watcher code.

External services (Gmail, WhatsApp, LinkedIn, Odoo) MUST be accessed exclusively
via MCP servers or typed API client modules. Ad-hoc subprocess calls and hardcoded
HTTP requests inside skill files are prohibited.

### XI. Observability

Every action MUST produce a structured audit record. Each record MUST contain:

- `timestamp` (ISO-8601 UTC)
- `action_type`
- `actor` (agent identity)
- `target`
- `parameters`
- `approval_status` (approved | auto | pending)
- `approved_by` (human | system)
- `result` (success | failure)

Logs MUST be written to `Logs/YYYY-MM-DD.json`. Silent failures are prohibited.
Any action that cannot produce a log record MUST fail loudly and write an
`ERROR_<timestamp>.md` to `Needs_Action/`.

### XII. Reliability

All services MUST assume failures will occur. Every service integration MUST
implement:

- **Retry**: exponential backoff (base 1 s, max 60 s, 3 attempts)
- **Timeout**: every external call MUST have a configurable timeout
- **Recovery**: failed tasks MUST write `ERROR_*.md` to `Needs_Action/`
- **Watchdog**: the orchestrator MUST restart crashed watcher processes
- **Graceful degradation**: partial failures MUST not halt unrelated operations

Banking operations MUST never be auto-retried. A failed payment MUST always
require fresh human approval before a retry is attempted.

### XIII. Security

**Secret Zero**: API keys, tokens, session files, and credentials MUST NEVER appear
in any `.md` vault file, skill file, or committed code. All secrets MUST use `.env`
(gitignored) or OS-level credential stores (Windows Credential Manager / macOS
Keychain).

**Cloud boundary**: cloud agents MUST NEVER receive credentials for financial systems.
Cloud agents MUST NEVER execute payment, banking, or invoice-posting operations.

**Defaults**: `DRY_RUN=true` MUST be the default. Live execution requires explicit
`DRY_RUN=false` in the environment.

**Rate limits**: max 10 emails/hour; max 3 payments/hour. Exceeding these thresholds
MUST trigger a human alert, not a silent queue.

**Rotation**: credentials MUST be rotated monthly and immediately after any suspected
breach.

### XIV. Documentation

Every folder, module, watcher, skill, and MCP server MUST have documentation.
Minimum required documentation per component:

- Purpose and responsibility
- Inputs and outputs (file paths, schemas)
- Configuration and environment variables
- Known limitations or failure modes

A component without documentation MUST be treated as incomplete, regardless of
functional correctness.

### XV. Code Quality

All code MUST follow these principles:

- **Clean Architecture**: dependency direction flows inward; outer layers depend on
  inner abstractions, never the reverse
- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface
  Segregation, Dependency Inversion
- **Dependency Injection**: services MUST receive their dependencies; MUST NOT
  instantiate them internally
- **Strong typing**: all function signatures MUST include type annotations
- **Small modules**: no file exceeds 300 lines; extract when approaching the limit
- **Readable code**: identifiers are self-documenting; comments explain WHY, never WHAT

God Objects are prohibited. Three similar lines in isolation are preferable to a
premature abstraction.

## Hackathon Tier Compliance

Each tier is a superset of the one below. Features MUST be built and validated in
tier order; a tier is complete only when all its requirements pass end-to-end.

| Tier     | Gate Criteria |
|----------|---------------|
| Bronze   | Vault + Dashboard + 1 watcher + `process-needs-action` skill working |
| Silver   | 2+ watchers + LinkedIn MCP + Plan.md generation + HITL workflow + cron |
| Gold     | Odoo integration + CEO Briefing + Ralph Wiggum loop + full audit log |
| Platinum | Cloud VM (24/7) + Cloud/Local split + vault sync + Odoo Community on cloud VM (HTTPS + backups + health monitoring) + all 15 principles enforced |

No tier MAY be declared complete with broken or mocked dependencies.

## Governance

This constitution supersedes all other project-level practices and README guidance.
Any change to a Core Principle requires: (1) a written rationale, (2) a version bump
per the policy below, and (3) propagation to all affected templates before the
amendment commit is merged.

**Versioning policy**:
- MAJOR — removal, redefinition, or structural restructuring of existing principles.
- MINOR — new principle or section added without removing existing ones.
- PATCH — clarifications, wording, or formatting only; no semantic change.

All plans and specs MUST include a "Constitution Check" gate that verifies compliance
with all fifteen Core Principles before implementation begins.

Runtime guidance for Claude Code lives in `CLAUDE.md` at the repository root.
Commit messages MUST reference the hackathon tier (e.g., `feat(platinum): …`).

**Version**: 2.1.0 | **Ratified**: 2026-03-06 | **Last Amended**: 2026-06-27
