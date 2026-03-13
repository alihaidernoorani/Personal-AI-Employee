---
id: 001
title: Digital FTE Constitution 2026 Hackathon Standards
stage: constitution
date: 2026-03-06
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: alihaidernoorani
command: /sp.constitution
labels: ["constitution","governance","digital-fte","hackathon","skills-first","hitl","security"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - history/prompts/constitution/001-digital-fte-constitution-2026.constitution.prompt.md
tests:
  - none
---

## Prompt

```text
# Digital FTE Constitution: 2026 Hackathon Standards

## I. Skills-First & MCP Architecture
- **Skills-Only Logic**: All AI functionality MUST reside in `.claude/skills/`. Watchers only invoke these skills.
- **MCP Integration**: Access external services (WhatsApp, Odoo, Gmail) exclusively via MCP servers or direct API clients.
- **Idempotency**: Track processed IDs in `scripts/processed_*.json` to prevent duplicate actions.

## II. Folder-Based State Machine
- **Strict Flow**: Inbox → Needs_Action → Plans → Done. No skipping states.
- **Obsidian GUI**: Use Markdown files as the primary interface for state management and long-term memory.

## III. Human-in-the-Loop (HITL) Safety
- **Restricted Actions**: Explicit human approval required for:
  - External communication (Emails, WhatsApp, LinkedIn).
  - Financial transactions or Odoo record modifications.
- **Approval Gate**: Draft intents in `Plans/` with `[ ] APPROVE` checkboxes. Only execute after a human checks the box.

## IV. Proactive Business Intelligence
- **CEO Briefing**: Autonomously audit `Business_Goals.md` and `Bank_Transactions.md` every Sunday night.
- **Output**: Generate a "Monday Morning CEO Briefing" in the Dashboard highlighting revenue, bottlenecks, and optimizations.

## V. Security & Operations
- **Secret Zero**: Never hardcode or commit API keys/tokens. Use `.env` or OS-level stores.
- **Atomic Commits**: Reference hackathon tiers (Bronze–Platinum) in commit messages.
- **Environment**: Target Windows 11 Pro with forward-slash path compatibility.
```

## Response snapshot

Ratified constitution v1.0.0 at `.specify/memory/constitution.md` with five Core
Principles (Skills-First, Folder State Machine, HITL Safety, Proactive BI, Security &
Ops), a Hackathon Tier Compliance table, and a Governance section with semantic
versioning policy. Sync Impact Report prepended as HTML comment. Templates reviewed
and confirmed compatible; no updates required.

## Outcome

- ✅ Impact: Project governance established; all future plans, specs, and tasks must pass the five-principle Constitution Check gate.
- 🧪 Tests: N/A — governance document, no executable tests.
- 📁 Files: .specify/memory/constitution.md (created v1.0.0)
- 🔁 Next prompts: /sp.specify for first feature spec; /sp.plan for architecture; /sp.adr for significant decisions.
- 🧠 Reflection: Constitution cleanly maps to the hackathon's Bronze–Platinum tier model. HITL and Skills-First principles are the most critical constraints to enforce in plan-template Constitution Check gates.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): initial ratification
- Next experiment: validate Constitution Check enforcement in first /sp.plan run
