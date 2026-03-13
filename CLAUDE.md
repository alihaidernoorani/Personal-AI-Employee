# Claude Code Rules

This file is generated during init for the selected agent.

You are an expert AI assistant specializing in Spec-Driven Development (SDD). Your primary goal is to work with the architext to build products.

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps. 

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Basic Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records
- `.specify/` — SpecKit Plus templates and scripts

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.

---

## Project: Personal AI Employee

This project builds a "Digital FTE" (Full-Time Equivalent) — an autonomous agent powered by Claude Code + Obsidian that proactively manages personal affairs (Gmail, WhatsApp, Bank) and business operations (Social Media, Payments, Projects).

### Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Brain | Claude Code (claude-sonnet-4-6+) | Reasoning engine |
| Memory/GUI | Obsidian (`AI_Employee_Vault/`) | Dashboard & long-term memory |
| Senses | Python 3.13+ Watcher scripts (`watchers/`) | Monitors Gmail, WhatsApp, filesystem |
| Hands | MCP servers (Node.js v24+ / Python) | External actions |
| Orchestration | `orchestrator.py` | Launches watchers, manages processes |
| Automation | Playwright | WhatsApp Web, payment portals |

### Vault Structure (`AI_Employee_Vault/`)

Files are the communication bus between all components. Folder = state.

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status (single-writer: Local agent)
├── Company_Handbook.md       # Rules of engagement — edit to change AI behaviour
├── Business_Goals.md         # OKRs, revenue targets, subscription audit rules
├── Bank_Transactions.md      # Finance watcher output — transaction log
├── Inbox/                    # Drop zone for files; watcher picks them up
├── Needs_Action/             # Watcher-created .md task files awaiting Claude
├── In_Progress/<agent>/      # Claimed tasks (claim-by-move, prevents double-work)
├── Plans/                    # Claude-generated Plan.md with [ ] APPROVE checkboxes
├── Pending_Approval/         # Sensitive actions waiting for human sign-off
├── Approved/                 # Human-approved → triggers MCP execution
├── Rejected/                 # Declined actions (never deleted)
├── Done/                     # Completed tasks (never deleted)
├── Briefings/                # Weekly CEO briefings (YYYY-MM-DD_Monday_Briefing.md)
├── Accounting/               # Bank transaction logs (Current_Month.md)
└── Logs/                     # Audit trail — YYYY-MM-DD.json, 90-day retention
```

### Core Architecture Patterns

#### Watcher Pattern (Perception)
All watchers extend `BaseWatcher` (`watchers/base_watcher.py`):
- `check_for_updates() -> list` — polls the source
- `create_action_file(item) -> Path` — writes structured `.md` to `Needs_Action/`

> **WSL2 note:** `/mnt/c` NTFS mounts don't support `inotify`. Use `PollingObserver(timeout=3)` — not the default `InotifyObserver`.

Watchers track processed IDs in `scripts/processed_*.json` for idempotency.

#### Ralph Wiggum Loop (Persistence — Gold tier)
A Claude Code Stop hook that prevents exit until the task is complete:
1. Orchestrator creates state file with prompt
2. Claude works; tries to exit
3. Stop hook checks: is task file in `/Done/`?
4. NO → blocks exit, re-injects prompt (loop continues, max iterations enforced)
5. YES → allows exit

Completion strategies:
- **Promise-based:** Claude outputs `<promise>TASK_COMPLETE</promise>`
- **File movement:** Stop hook detects task moved to `/Done/`

Invocation: `/ralph-loop "<prompt>" --completion-promise "TASK_COMPLETE" --max-iterations 10`

#### Human-in-the-Loop (HITL)
For sensitive actions, Claude writes to `Plans/` (not `Pending_Approval/` directly) with `[ ] APPROVE` checkboxes. Only after a human checks the box does the orchestrator move it to `Approved/` and trigger the MCP action.

**Banking:** never auto-retry. Always require fresh approval.

#### Permission Boundaries

| Action Category | Auto-Approve | Always Require Approval |
|----------------|--------------|------------------------|
| Email replies | To known contacts | New contacts, bulk sends |
| Payments | < $50 recurring, known payees | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read, move within vault | Delete, move outside vault |

#### Claim-by-Move Rule (Platinum multi-agent)
First agent to move an item from `Needs_Action/` to `In_Progress/<agent>/` owns it. Other agents skip claimed items. `Dashboard.md` is single-writer (Local agent only).

### Operation Types

| Type | Example | Trigger |
|------|---------|---------|
| Scheduled | Daily 8 AM briefing | cron / Task Scheduler |
| Continuous | WhatsApp keyword watcher | Python watchdog on `/Inbox/` |
| Project-based | Q1 tax prep | Manual file drop into `/Active_Project/` |

### Business Handover (CEO Briefing — Gold tier)

Runs every Sunday night. Claude reads:
- `Business_Goals.md` — targets, KPIs, subscription audit rules
- `Bank_Transactions.md` — transaction log from Finance watcher

Outputs `Briefings/YYYY-MM-DD_Monday_Briefing.md` containing:
- Revenue vs. target (weekly + MTD)
- Completed tasks from `Done/`
- Bottlenecks (tasks delayed beyond threshold)
- Proactive suggestions (unused subscriptions, budget overruns, upcoming deadlines)

### Error Recovery

| Category | Examples | Strategy |
|----------|---------|----------|
| Transient | Network timeout, API rate limit | Exponential backoff (base 1s, max 60s, 3 attempts) |
| Authentication | Expired token, revoked access | Alert human, pause operations, write ERROR file |
| Logic | Claude misinterprets message | Human review queue in `Needs_Action/ERROR_*.md` |
| Data | Corrupted file, missing field | Quarantine + alert |
| System | Orchestrator crash, disk full | Watchdog process + auto-restart + human notification |

On any failure: write `Needs_Action/ERROR_<timestamp>.md` — never silently fail.

### Security

- **Credentials:** `.env` (gitignored) or OS keychain — never in vault `.md` files
- **Dry-run:** `DRY_RUN=true` is the default. Set to `false` only for live execution
- **Rate limiting:** max 10 emails/hour, max 3 payments/hour
- **Sandboxing:** use test/sandbox accounts for Gmail and banking during development
- **Rotation:** rotate credentials monthly and after any suspected breach
- **Audit log:** every action logged to `Logs/YYYY-MM-DD.json`, retained 90 days

Audit log schema:
```json
{
  "timestamp": "ISO-8601Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "recipient",
  "parameters": {},
  "approval_status": "approved | auto | pending",
  "approved_by": "human | system",
  "result": "success | failure"
}
```

### Development Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # set VAULT_PATH, keep DRY_RUN=true
python orchestrator.py  # starts filesystem watcher
# second terminal: claude → "Run the process-needs-action skill"
```

### MCP Server Configuration (`~/.config/claude-code/mcp.json`)

| Server | Command | Use case |
|--------|---------|----------|
| filesystem | built-in | Vault read/write |
| email-mcp | `node /path/to/email-mcp/index.js` | Gmail send/draft/search |
| browser-mcp | `npx @anthropic/browser-mcp` | Payment portals, WhatsApp Web |
| calendar-mcp | varies | Scheduling |

### Hackathon Tiers

| Tier | Key additions | Estimated time |
|------|--------------|---------------|
| Bronze | Vault + 1 watcher + `process-needs-action` skill | 8–12 hrs |
| Silver | 2+ watchers + LinkedIn MCP + Plan.md generation + cron | 20–30 hrs |
| Gold | Odoo + CEO Briefing + Ralph Wiggum loop + full audit | 40+ hrs |
| Platinum | Cloud VM (24/7) + Cloud/Local split + vault sync | 60+ hrs |

Commit messages must reference tier: `feat(bronze): …`, `feat(silver): …`

### Agent Skills

All AI functionality lives in `.claude/skills/<skill-name>/SKILL.md`. Watchers are perception-only — no logic. Current skills:
- `process-needs-action` — reads `Needs_Action/`, processes by type, updates Dashboard, moves to Done

### Judging Criteria (submission reference)

| Criterion | Weight |
|-----------|--------|
| Functionality | 30% |
| Innovation | 25% |
| Practicality | 20% |
| Security | 15% |
| Documentation | 10% |

## Active Technologies
- Python 3.12+ (WSL2 Ubuntu) + `watchdog>=4.0.0`, `python-dotenv>=1.0.0` (001-bronze-ai-employee)
- Markdown files in `AI_Employee_Vault/` (no database) (001-bronze-ai-employee)

## Recent Changes
- 001-bronze-ai-employee: Added Python 3.12+ (WSL2 Ubuntu) + `watchdog>=4.0.0`, `python-dotenv>=1.0.0`
