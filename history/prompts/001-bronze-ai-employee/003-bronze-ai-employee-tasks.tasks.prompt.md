---
id: 003
title: Bronze AI Employee Task List
stage: tasks
date: 2026-03-06
surface: agent
model: claude-sonnet-4-6
feature: 001-bronze-ai-employee
branch: 001-bronze-ai-employee
user: alihaidernoorani
command: /sp.tasks
labels: ["tasks","bronze","ai-employee","watcher","obsidian","skill","checklist"]
links:
  spec: specs/001-bronze-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-ai-employee/tasks.md
tests:
  - none
---

## Prompt

```text
Generate a detailed task list to implement the Bronze Tier Personal AI Employee.

Tasks should be small and executable.

Each task should include:
task id, description, files to create or modify, dependencies, expected outcome

Tasks should cover:
Project Setup, Vault Structure, Core Files (Dashboard.md, Company_Handbook.md),
Watcher Development (BaseWatcher, FilesystemWatcher, idempotency),
Claude Integration (read tasks, generate Plan.md), Task Processing (move to Done),
Dashboard Updates, Testing (watcher, task creation, plan generation, completion workflow).

The output should be a checklist suitable for SpeckitPlus execution.
```

## Response snapshot

Generated `specs/001-bronze-ai-employee/tasks.md` with 25 tasks across 6 phases.
Tasks organized by user story (US1: watcher, US2: plan creation, US3: completion +
dashboard). Parallel opportunities identified in Setup, Vault, and Watcher phases.
SKILL.md tasks (T013–T020) are sequential (same file). End-to-end acceptance flow
in Phase 6 covers all 6 spec success criteria. Plans/ directory gap identified and
added as T021.

## Outcome

- ✅ Impact: Complete actionable task list covering all 13 FRs and 6 SCs. Each user story has an independent test checkpoint.
- 🧪 Tests: No TDD tasks — manual end-to-end validation per plan.md.
- 📁 Files: specs/001-bronze-ai-employee/tasks.md
- 🔁 Next prompts: /sp.implement to execute tasks; review each checkpoint before proceeding to next US phase.
- 🧠 Reflection: SKILL.md is a single file updated across 8 sequential tasks (T013–T020). If parallelisation is desired in future, breaking SKILL.md into step-specific files could help, but adds complexity — YAGNI for Bronze.

## Evaluation notes (flywheel)

- Failure modes observed: Plans/ directory missing from vault — caught during task generation (T021)
- Graders run and results (PASS/FAIL): Format check — all 25 tasks have checkbox + ID + description + file path; PASS
- Prompt variant (if applicable): structured domain breakdown from user
- Next experiment: validate task independence — can US1 checkpoint be reached without touching SKILL.md at all?
