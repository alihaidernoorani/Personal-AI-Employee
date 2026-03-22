---
id: "002"
title: gold-tier-system-design-plan
stage: plan
date: 2026-03-22
surface: agent
model: claude-sonnet-4-6
feature: 003-gold-ai-employee
branch: 003-gold-ai-employee
user: Ali Haider Noorani
command: /sp.plan
labels: ["plan", "gold-tier", "architecture", "mcp", "watchers", "odoo", "ralph-wiggum", "hitl"]
links:
  spec: specs/003-gold-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-gold-ai-employee/plan.md
  - specs/003-gold-ai-employee/research.md
  - specs/003-gold-ai-employee/data-model.md
  - specs/003-gold-ai-employee/quickstart.md
  - specs/003-gold-ai-employee/contracts/email-mcp.md
  - specs/003-gold-ai-employee/contracts/social-mcp.md
  - specs/003-gold-ai-employee/contracts/odoo-mcp.md
  - specs/003-gold-ai-employee/contracts/ralph-wiggum-hook.md
  - CLAUDE.md
tests:
  - "N/A — plan stage; no tests generated"
---

## Prompt

You are a senior AI systems architect using SpecKitPlus.

Your task is to convert the SPEC into a complete SYSTEM DESIGN.

## Objective
Define HOW the Gold Tier AI Employee system will be built.

## Requirements
You MUST cover:

### 1. High-Level Architecture
- Perception → Reasoning → Action → Logging
- Interaction between Watchers, Claude, MCP, Vault

### 2. Component Design
Design each module:
- Watchers Layer (Python daemons)
- Orchestrator (central controller)
- Claude Code (reasoning engine)
- MCP Servers (action layer)
- Odoo integration layer
- Social automation layer
- Logging & monitoring
- Watchdog system

### 3. Data Flow — How data moves across folders; Lifecycle of a task

### 4. Folder Architecture (STRICT) — /Needs_Action, /Plans, /Pending_Approval, /Approved, /Rejected, /Done, /Logs, /Accounting, /Briefings

### 5. MCP Design — One MCP per domain; Clear responsibility boundaries; Communication patterns

### 6. Ralph Wiggum Loop Design — Stop hook usage; Iteration flow; Failure recovery

### 7. Odoo Integration Plan — JSON-RPC interaction; Invoice + transaction flows

### 8. Error Handling Architecture — Retry strategy; Fallback behavior; Queueing system

### 9. Security Design — Secrets management; Approval enforcement; Rate limiting

## Constraints
- Must align 100% with SPEC
- Must be modular and scalable
- Must support always-on automation

## Output Format
Generate Plan.md with architecture diagram (text), module descriptions, data flow explanation, integration strategy. Do NOT write code.

## Response snapshot

Generated complete Gold Tier system design across 9 required areas:

**plan.md**: Full implementation plan with ASCII architecture diagram, Technical Context, Constitution Check (all 5 principles PASSED), complete project source tree, 9-section system design covering all required areas, integration strategy with 10-step phase order, dependency map, and 3 ADR candidates surfaced.

**research.md**: 10 research decisions resolved — MCP transport (stdio), Odoo MCP language (Python), polling vs push (PollingObserver), email queue (JSON file), WhatsApp single-session (PID guard), Odoo auth (session-based), Ralph Wiggum hook registration (Stop hook in settings.json), social media API strategy (official APIs + Browser MCP fallback), temp folder strategy, CEO briefing trigger (schedule library + Task Scheduler).

**data-model.md**: 8 entities defined (Task File, Plan, Approval File, Audit Log Entry, CEO Briefing, Bank Transaction, Watcher State, Loop State File) with fields, types, invariants, and complete state machine diagram.

**quickstart.md**: Full developer setup guide — prerequisites, install, .env config, vault initialisation, MCP registration, hook config, start commands, HITL test procedure, Windows Task Scheduler production setup, end-to-end verification checklist.

**contracts/**: 4 MCP interface contracts (email-mcp, social-mcp, odoo-mcp, ralph-wiggum-hook) with all tool inputs/outputs, error codes, rate limits, approval enforcement rules.

CLAUDE.md updated with Gold tier tech stack via update-agent-context.sh.

## Outcome

- ✅ Impact: Complete system design ready for /sp.tasks; all 9 required areas covered; all 5 constitution principles satisfied; 3 ADR candidates identified; CLAUDE.md updated.
- 🧪 Tests: N/A — plan stage
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/email-mcp.md, contracts/social-mcp.md, contracts/odoo-mcp.md, contracts/ralph-wiggum-hook.md, CLAUDE.md
- 🔁 Next prompts: /sp.adr (3 candidates), /sp.tasks
- 🧠 Reflection: Constitution Check passed cleanly with no violations. The graceful degradation requirements (FR-041–043) from the spec update drove three non-trivial design decisions (email queue, watcher-continues, temp folder) that are all now captured in research.md with rationale. Odoo MCP as Python (not Node.js) is the key tech decision — documented in research.md item 2.

## Evaluation notes (flywheel)

- Failure modes observed: None — all sections populated; constitution gate passed; no NEEDS CLARIFICATION markers remain.
- Graders run and results (PASS/FAIL): Constitution Check — PASS (all 5 principles); Technical Context — PASS (all unknowns resolved in research.md)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add browser-mcp.md contract file to contracts/ for completeness (browser-mcp is provided by Anthropic so interface is external, but a stub contract would aid task generation).
