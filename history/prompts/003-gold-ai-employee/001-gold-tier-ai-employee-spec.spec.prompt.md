---
id: "001"
title: gold-tier-ai-employee-spec
stage: spec
date: 2026-03-22
surface: agent
model: claude-sonnet-4-6
feature: 003-gold-ai-employee
branch: 003-gold-ai-employee
user: Ali Haider Noorani
command: /sp.specify
labels: ["spec", "gold-tier", "ai-employee", "watcher", "hitl", "mcp", "odoo", "ceo-briefing"]
links:
  spec: specs/003-gold-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-gold-ai-employee/spec.md
  - specs/003-gold-ai-employee/checklists/requirements.md
  - history/prompts/003-gold-ai-employee/001-gold-tier-ai-employee-spec.spec.prompt.md
tests:
  - "N/A — spec stage; no tests generated"
---

## Prompt

You are an expert product architect using SpecKitPlus methodology.

Your task is to DEFINE a complete, unambiguous specification for a "Gold Tier Personal AI Employee" system based on the provided hackathon document.

## Objective
Create a SPEC that clearly defines WHAT needs to be built — not how.

## Scope (MANDATORY Gold Tier Features)
The system MUST include:

1. Cross-domain automation
   - Personal (Gmail, WhatsApp)
   - Business (Social media, Accounting, Tasks)

2. Watcher-based perception system
   - Gmail watcher
   - WhatsApp watcher (persistent session, single browser instance)
   - File system watcher
   - Finance watcher

3. Reasoning system
   - Claude Code as core engine
   - Plan generation (Plan.md)
   - Agent Skills for ALL functionality

4. Action system (MCP servers)
   - Email MCP
   - Browser MCP
   - Social MCP (Facebook, Instagram, Twitter/X, LinkedIn)
   - Odoo MCP (JSON-RPC integration)

5. Accounting system
   - Odoo Community (self-hosted)
   - Invoice generation
   - Transaction tracking

6. Weekly CEO Briefing
   - Revenue analysis
   - Bottleneck detection
   - Cost optimization suggestions

7. Human-in-the-loop (HITL)
   - Approval workflow using file movement
   - Required for payments, emails, social posts

8. Ralph Wiggum Loop
   - Autonomous iteration until completion
   - File-based completion detection (/Done)

9. Audit Logging
   - All actions logged
   - Structured JSON logs
   - Stored in /Logs

10. Error Handling
   - Retry logic
   - Graceful degradation
   - Watchdog process recovery

## Functional Requirements
Define:
- Inputs (watchers)
- Outputs (actions, logs, reports)
- State transitions (Needs_Action → Plan → Approval → Done)

## Non-Functional Requirements
- Local-first architecture
- High reliability (auto-restart, retries)
- Security (no secrets in vault)
- Modularity (MCP-based)
- Observability (logs + dashboard)

## Data Contracts (VERY IMPORTANT)
Define schemas for:
- Needs_Action files
- Plan.md
- Approval files
- Logs
- CEO Briefing

## Constraints
- Obsidian is the single source of truth
- File-based workflow only
- No direct autonomous payments without approval
- WhatsApp must NOT open multiple sessions

## Output Format
Produce a structured SPEC.md with:
- System Overview
- Features
- Functional Requirements
- Non-Functional Requirements
- Data Schemas
- Acceptance Criteria (for each Gold feature)

Do NOT include implementation details or code.

## Response snapshot

Created `specs/003-gold-ai-employee/spec.md` — a complete Gold Tier specification covering:

- **System Overview**: actors (Owner, AI Agent, Watchers, MCP Servers), communication model via vault files.
- **7 User Stories** (P1–P3): inbound email triage, HITL approval workflow, WhatsApp keyword monitoring, Finance watcher + Odoo sync, Weekly CEO Briefing, social media post approval, Ralph Wiggum loop.
- **Edge Cases**: malformed task files, duplicate watcher events, vault unmount, mid-session WhatsApp expiry, Odoo unavailability.
- **40 Functional Requirements** (FR-001–FR-040) covering all 10 mandatory Gold features.
- **20 Non-Functional Requirements** (NFR-001–NFR-020) across reliability, performance, security, modularity, observability, local-first architecture.
- **8 Key Entities** with attributes.
- **5 Data Schemas**: Needs_Action file, Plan.md, Approval file, Audit Log (NDJSON), CEO Briefing.
- **8 Assumptions** documented.
- **10 Success Criteria** (SC-001–SC-010), all measurable and technology-agnostic.
- Quality checklist created at `specs/003-gold-ai-employee/checklists/requirements.md` — all items passing.
- Branch created and renamed: `003-gold-ai-employee`.

## Outcome

- ✅ Impact: Full Gold Tier spec produced; all 10 mandatory features specified with acceptance criteria; no NEEDS CLARIFICATION markers; ready for /sp.plan.
- 🧪 Tests: N/A — spec stage
- 📁 Files: specs/003-gold-ai-employee/spec.md, specs/003-gold-ai-employee/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify (optional) or /sp.plan
- 🧠 Reflection: Spec covers all Gold-tier scope without leaking implementation details. Finance watcher bank-source is intentionally deployment-agnostic; owner should clarify before planning if a specific bank API is targeted.

## Evaluation notes (flywheel)

- Failure modes observed: None — all sections populated; no placeholder leakage.
- Graders run and results (PASS/FAIL): Requirements checklist — PASS (all 14 items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add a clarification question about the specific bank integration mechanism before /sp.plan to reduce assumption risk.
