---
id: "004"
title: Constitution Check Skill Design
stage: general
date: 2026-06-27
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 003-gold-ai-employee
user: Ali Haider Noorani
command: "Design constitution-check skill — classify 15 principles as auto/partial/manual"
labels: ["constitution-check","skill-design","validation","static-analysis"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - watchers/base_watcher.py
  - watchers/gmail_api_watcher.py
  - mcp-servers/odoo-mcp/server.py
  - mcp-servers/social-mcp/server.py
  - .specify/memory/constitution.md
tests:
  - none
---

## Prompt

I need to design a `constitution-check` skill for a Claude Code-based AI Employee system. The skill must validate a deployed system against 15 constitution principles. Help me determine which principles can be checked automatically vs. requiring manual review.

**The 15 principles** (from the constitution):
I. Production First — no prototype shortcuts; every feature ships-ready
II. Local First — sensitive data never leaves local machine (credentials, sessions, .env)
III. Cloud Worker — cloud agent NEVER calls execution MCP tools (no email send, social post, payment)
IV. Human In The Loop — all sensitive actions require APPROVAL_*.md in Pending_Approval/ before execution
V. Vault Driven Architecture — agents communicate only through vault markdown files
VI. Claim-by-Move — tasks owned by moving to In_Progress/<agent>/; others skip claimed tasks
VII. Single Writer Rule — Dashboard.md written only by local agent; cloud writes only Updates/, Signals/, Plans/
VIII. Event Driven — agents use PollingObserver not busy-wait; sleep between cycles
IX. Modular Design — each integration isolated; no God Objects
X. Agent Skills — all AI logic in .claude/skills/; no logic in watchers
XI. Observability — every action produces structured audit record in Logs/YYYY-MM-DD.json
XII. Reliability — retry with exponential backoff, timeout, watchdog
XIII. Security — no secrets in .md files; .env gitignored; DRY_RUN=true default
XIV. Documentation — every folder/module/watcher/skill has docs
XV. Code Quality — SOLID, DI, strong typing, no file > 300 lines

**System structure to inspect**:
- Vault at `AI_Employee_Vault/`
- Skills at `.claude/skills/`
- Watchers at `watchers/`
- MCP servers at `mcp-servers/`
- Config in `.mcp.json`, `.env`, `CLAUDE.md`
- Cloud VM has separate vault replica

**For each principle**, determine:
1. Can it be checked programmatically? (YES/PARTIAL/NO)
2. What check would you run? (file system scan, grep, file existence, etc.)
3. What would a FAIL look like?

Give a table with all 15 principles. Report in under 500 words.

## Response snapshot

Produced a grounded 15-row classification table based on actual codebase scan. Key findings:

- 7 principles are fully automatable (II, IV, VII, VIII, X, XI, XIII) via grep/file-existence checks
- 7 are partially automatable (I, III, V, VI, IX, XII, XIV) — structural checks automated, intent requires human
- 1 is manual only (XV — SOLID/DI design judgment beyond line count)

Pre-existing violations identified:
- Principles IX/XV: odoo-mcp/server.py (636 lines), social-mcp/server.py (515 lines), gmail_api_watcher.py (322 lines) exceed 300-line limit
- Principle VIII: PollingObserver import unconfirmed in any watcher file

## Outcome

- Impact: Clear classification map for implementing constitution-check skill; pre-existing failures surfaced before skill is built
- Tests: none
- Files: none modified; analysis only
- Next prompts: Implement constitution-check SKILL.md using this table; split checks into automated runner + manual checklist sections
- Reflection: Grounding the classification in the actual codebase (line counts, grep patterns, folder structure) revealed real violations the skill must detect, making the design immediately actionable

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment: Implement the skill with a two-section output — automated PASS/FAIL table followed by manual checklist items
