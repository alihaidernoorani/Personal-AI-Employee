<!--
SYNC IMPACT REPORT
==================
Version change  : N/A (initial creation) → 1.0.0
Bump rationale  : MINOR — First ratification; all five principles and governance sections are new.

Principles added:
  I.   Skills-First & MCP Architecture (new)
  II.  Folder-Based State Machine (new)
  III. Human-in-the-Loop (HITL) Safety (new)
  IV.  Proactive Business Intelligence (new)
  V.   Security & Operations (new)

Principles removed : none
Sections added     : Hackathon Tier Compliance, Governance
Sections removed   : none

Templates reviewed:
  ✅ .specify/templates/plan-template.md   — Constitution Check section is generic; compatible.
  ✅ .specify/templates/spec-template.md   — No constitution-specific references; compatible.
  ✅ .specify/templates/tasks-template.md  — Skill-based task structure aligns with Principle I.
  ✅ .specify/templates/phr-template.prompt.md — No changes required.

Deferred TODOs:
  - RATIFICATION_DATE is set to today (2026-03-06); update if project has an earlier founding date.
-->

# Digital FTE Constitution: 2026 Hackathon Standards

## Core Principles

### I. Skills-First & MCP Architecture

All AI logic MUST reside in `.claude/skills/`. Watcher scripts are pure perception;
they MUST NOT contain reasoning or decision logic — they only deposit structured `.md`
files into `Needs_Action/` and invoke skills.

External services (Gmail, WhatsApp, LinkedIn, Odoo) MUST be accessed exclusively via
MCP servers or typed API client modules — never via ad-hoc subprocess calls or
hardcoded HTTP in skill files.

Idempotency is non-negotiable: every watcher MUST track processed item IDs in
`scripts/processed_*.json` and skip already-processed items on restart.

### II. Folder-Based State Machine

The vault enforces a strict, one-way state flow:

```
Inbox → Needs_Action → Plans → (Pending_Approval →) Done
```

No item MAY skip a state. Files MUST move forward only; backward moves are forbidden
except by explicit human override. The Obsidian vault is the single source of truth
for all agent state and long-term memory — no external databases are used for state.

### III. Human-in-the-Loop (HITL) Safety

The following actions MUST NOT be executed autonomously under any circumstances:

- External communication (sending emails, WhatsApp messages, LinkedIn posts)
- Financial transactions or Odoo record modifications (posting invoices, payments)
- Any action that is irreversible or affects a third party

The mandatory approval gate: skills MUST draft intents in `Plans/` as `.md` files
containing `[ ] APPROVE` checkboxes. Execution MUST be blocked until a human
checks the box. No skill MAY poll or auto-approve its own approval request.

### IV. Proactive Business Intelligence

The AI Employee MUST operate proactively, not just reactively. A scheduled weekly
audit MUST run every Sunday night, reading `Business_Goals.md` and
`Bank_Transactions.md`, and generating a "Monday Morning CEO Briefing" in
`Briefings/` that includes: revenue vs. target, bottlenecks (tasks delayed > threshold),
cost optimisation opportunities (unused subscriptions, budget overruns), and
upcoming deadlines.

Briefings MUST be generated even when no anomalies are found; a clean briefing
is a valid and expected output.

### V. Security & Operations

**Secret Zero**: API keys, tokens, session files, and credentials MUST NEVER appear
in any `.md` file, skill file, or committed code. All secrets use `.env` or OS-level
credential stores (Windows Credential Manager / macOS Keychain).

**Environment**: The system targets Windows 11 Pro with WSL2. All file paths in code
MUST use forward-slash separators. Watcher scripts MUST use `PollingObserver`
(not `InotifyObserver`) when operating on `/mnt/c` NTFS mounts.

**Commit discipline**: Commit messages MUST reference the hackathon tier being
implemented (e.g., `feat(bronze): …`, `feat(silver): …`). Each tier's deliverables
MUST be completable and demonstrable independently.

## Hackathon Tier Compliance

Each tier is a superset of the one below. Features MUST be built and validated
in tier order; a tier is complete only when all its requirements pass end-to-end.

| Tier     | Gate Criteria |
|----------|---------------|
| Bronze   | Vault + Dashboard + 1 watcher + `process-needs-action` skill working |
| Silver   | 2+ watchers + LinkedIn MCP + Plan.md generation + HITL workflow + cron |
| Gold     | Odoo integration + CEO Briefing + Ralph Wiggum loop + full audit log |
| Platinum | Cloud VM (24/7) + Cloud/Local split + vault sync + Odoo on cloud |

No tier MAY be declared complete with broken or mocked dependencies.

## Governance

This constitution supersedes all other project-level practices and README guidance.
Any change to a Core Principle requires: (1) a written rationale, (2) a version
bump per semantic versioning rules below, and (3) propagation to all affected
templates before the amendment commit is merged.

**Versioning policy**:
- MAJOR — removal or redefinition of an existing principle.
- MINOR — new principle or section added.
- PATCH — clarifications, wording, or formatting only.

All plans and specs MUST include a "Constitution Check" gate that verifies
compliance with the five Core Principles before implementation begins.

Runtime guidance for Claude Code lives in `CLAUDE.md` at the repository root.

**Version**: 1.0.0 | **Ratified**: 2026-03-06 | **Last Amended**: 2026-03-06
