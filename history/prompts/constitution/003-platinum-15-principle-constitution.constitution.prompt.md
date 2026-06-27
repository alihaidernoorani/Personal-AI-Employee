---
id: "003"
title: Platinum 15-Principle Constitution
stage: constitution
date: 2026-06-27
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 003-gold-ai-employee
user: Ali Haider Noorani
command: /sp.constitution
labels: ["constitution","platinum","production","v2.0.0","15-principles","local-first","cloud-worker","observability","reliability","security","code-quality"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

# Platinum AI Employee Constitution

You are a Senior Principal AI Software Architect.

Your responsibility is to help build a production-grade Personal AI Employee that satisfies every Platinum Tier requirement of the GIAIC Personal AI Employee Hackathon.

This is NOT a prototype.

This is NOT a demo.

Treat this repository like software that will run 24/7 for a real company.

---

## Core Mission

Design a Personal AI Employee capable of continuously operating across both Local and Cloud environments while maintaining security, reliability, auditability, and human oversight.

---

## Engineering Principles

### 1. Production First
Every feature must be production-oriented. Avoid shortcuts. No placeholder architecture.

### 2. Local First
Sensitive data never leaves the local machine. (WhatsApp Sessions, Banking Credentials,
API Secrets, Tokens, .env, Payment Credentials). Cloud only receives synchronized markdown state.

### 3. Cloud Worker
Cloud is responsible only for: Email triage, Draft generation, Social draft generation,
Planning, Scheduling, Background monitoring. Cloud NEVER performs final actions.

### 4. Human In The Loop
All sensitive actions require approval. (Sending email, Payments, Posting, Banking,
WhatsApp replies). Approval is performed locally.

### 5. Vault Driven Architecture
The Obsidian Vault is the single source of truth. Agents communicate only through
markdown files. Never bypass the vault.

### 6. Claim-by-Move
No task duplication. Agent ownership is determined by moving files from Needs_Action
to In_Progress/<agent>.

### 7. Single Writer Rule
Dashboard.md can only be modified locally. Cloud writes only into Updates/, Signals/, Plans/.

### 8. Event Driven
Never poll unnecessarily. Use watchers. Use events. Minimize idle work.

### 9. Modular Design
Every integration must be isolated. (Gmail, WhatsApp, LinkedIn, Facebook, Instagram,
Odoo, Health, Audit Skills). Each skill must be independently testable.

### 10. Agent Skills
All AI functionality must be implemented as Claude Agent Skills. Business logic must
never exist inside prompts.

### 11. Observability
Everything must be logged. Every action produces: structured log, audit record,
execution status, timestamp.

### 12. Reliability
Assume failures happen. Every service must support: retry, timeout, recovery,
watchdog, graceful degradation.

### 13. Security
Never expose secrets. Never sync secrets. Never hardcode credentials. Never allow
cloud execution of financial operations.

### 14. Documentation
Every folder, module, watcher, skill, MCP must have documentation.

### 15. Code Quality
Prefer Clean Architecture, SOLID, Dependency Injection, Strong typing, Small modules,
Readable code. Avoid God Objects.

## Response snapshot

Constitution updated from v1.1.0 to v2.0.0 (MAJOR bump).

Old structure: 5 principles (Skills-First, Folder State Machine, HITL Safety,
Proactive BI, Security & Ops)

New structure: 15 production-grade principles, each declarative and using MUST/MUST NOT
language:
  I. Production First — no prototype shortcuts
  II. Local First — sensitive data stays on-machine; cloud sees only markdown
  III. Cloud Worker — cloud scope: triage/draft/plan/schedule; never final actions
  IV. Human In The Loop — HITL safety with folder-movement approval gate (from v1.1.0)
  V. Vault Driven Architecture — vault = single source of truth; no bypass
  VI. Claim-by-Move — file-move = exclusive ownership; prevents duplicates
  VII. Single Writer Rule — Dashboard.md local-only; cloud writes Updates/Signals/Plans/
  VIII. Event Driven — watchers + events; no busy-wait
  IX. Modular Design — each integration isolated and independently testable
  X. Agent Skills — all logic in .claude/skills/; never inside prompts
  XI. Observability — structured audit log with 8 required fields; silent failures prohibited
  XII. Reliability — retry/timeout/recovery/watchdog/graceful degradation; banking never auto-retried
  XIII. Security — Secret Zero, cloud can't touch finance, DRY_RUN=true default, monthly rotation
  XIV. Documentation — every component must document purpose/IO/config/limitations
  XV. Code Quality — Clean Architecture, SOLID, DI, strong typing, <300 lines/file

Platinum Tier gate updated to require all 15 principles enforced.
Sync Impact Report prepended as HTML comment with full change log.

## Outcome

- ✅ Impact: Constitution elevated from Hackathon prototype (v1.1.0, 5 principles) to
             Platinum production-grade standard (v2.0.0, 15 principles)
- 🧪 Tests: Run /sp.analyze after next spec/plan cycle to verify 15-principle compliance
- 📁 Files: .specify/memory/constitution.md updated (v1.1.0 → v2.0.0)
- 🔁 Next prompts: Consider /sp.adr for Local/Cloud split boundary (Principles II+III);
             update plan-template.md Constitution Check to enumerate all 15 principles;
             verify CLAUDE.md HITL section no longer references checkbox pattern
- 🧠 Reflection: MAJOR bump is correct — existing 5-principle structure is fully replaced;
             the new 15-principle set redefines scope, ownership, reliability, and quality
             in ways that are not backward-compatible with the old governance model

## Evaluation notes (flywheel)

- Failure modes observed: None — template fill was clean; no placeholder tokens remain
- Graders run and results (PASS/FAIL): Version bump type — MAJOR PASS (full structural
  replacement of principle set); no bracket tokens remaining — PASS; ISO dates — PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Update plan-template.md Constitution Check
  gates to explicitly list all 15 principles as checkboxes
