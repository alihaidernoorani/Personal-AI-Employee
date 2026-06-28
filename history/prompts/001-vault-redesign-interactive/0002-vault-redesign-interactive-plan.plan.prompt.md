---
id: "0002"
title: vault-redesign-interactive-plan
stage: plan
date: 2026-06-28
surface: agent
model: claude-sonnet-4-6
feature: 001-vault-redesign-interactive
branch: 001-vault-redesign-interactive
user: Ali Haider Noorani
command: /sp.plan
labels: [vault, obsidian, dataview, buttons, kanban, homepage, meta-bind, plan, research]
links:
  spec: specs/001-vault-redesign-interactive/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-vault-redesign-interactive/plan.md
  - specs/001-vault-redesign-interactive/research.md
  - specs/001-vault-redesign-interactive/data-model.md
  - specs/001-vault-redesign-interactive/quickstart.md
  - history/prompts/001-vault-redesign-interactive/0002-vault-redesign-interactive-plan.plan.prompt.md
tests:
  - Manual SC-001: Open Dashboard; identify all pending items within 30s
  - Manual SC-002: Click quick-action buttons; navigate to hubs in 1 click
  - Manual SC-003: Dashboard Dataview renders within 3s with 100+ Done files
  - Manual SC-004: process-needs-action runs without errors after redesign
  - Manual SC-005: Pipeline.md renders 4 Kanban columns
  - Manual SC-006: Obsidian auto-opens Dashboard.md on launch
  - Manual SC-007: Each hub page shows only domain-relevant items
  - Manual SC-008: All Pending_Approval/ files reachable from Dashboard or hub
---

## Prompt

Research and devise a functioning plan to execute the redesign of obsidian vault. Don't execute the plan at this stage

## Response snapshot

Ran setup-plan.sh, read constitution (15 principles, v2.1.0), read spec.md (19 FRs, 5 user stories, 8 SCs), and inspected all 6 installed plugin manifests (Dataview 0.5.68, Buttons 0.9.13, Meta Bind 1.4.15, Kanban 2.0.51, Homepage 4.4.4, Tasks). Analysed actual vault files to confirm watcher naming conventions (WA_, GMAIL_, FINANCE_, APPROVAL_, DONE_ prefixes). Identified that Homepage data.json does not exist yet (plugin installed but not configured).

Produced 4 planning artifacts:
- research.md: 10 research decisions covering plugin syntax, Dataview query patterns, naming conventions, dual-layer Dashboard architecture, and social hub strategy (queries Pending_Approval/ not Needs_Action/ since social posts appear only as approval requests)
- data-model.md: Entity definitions for Hub Page, Quick Action Button, Dataview Query, Watcher File, Approval File, Kanban Card, Homepage Config; file relationship map; state machine diagram
- plan.md: 7 implementation phases with exact Dataview DQL, Buttons syntax, Meta Bind YAML, Kanban format, and Homepage JSON; Constitution Check (all 15 principles PASS); risk register; deliverable summary
- quickstart.md: 6 smoke tests mapping to SC-001 through SC-008

Key architectural decision: Dual-layer Dashboard (live Dataview + preserved AI_EMPLOYEE static markers) — satisfies both Principle XII (Reliability) and SC-001 (30s awareness without Claude having run).

## Outcome

- ✅ Impact: Complete implementation roadmap for the vault redesign — all plugin syntax confirmed, all queries written, all phases sequenced with dependencies clear
- 🧪 Tests: 6 smoke tests defined in quickstart.md covering all 8 success criteria
- 📁 Files: research.md, data-model.md, plan.md, quickstart.md (4 planning artifacts)
- 🔁 Next prompts: /sp.tasks — generate atomic implementation tasks from the 7 phases in plan.md
- 🧠 Reflection: The critical insight was that social media items only appear in Pending_Approval/ (never in Needs_Action/) because they are created by Claude as approval requests, not by a watcher. Without the naming convention analysis, Social_Hub.md would have been querying the wrong folder.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Constitution Check all 15 PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run /sp.tasks to generate implementation task list
