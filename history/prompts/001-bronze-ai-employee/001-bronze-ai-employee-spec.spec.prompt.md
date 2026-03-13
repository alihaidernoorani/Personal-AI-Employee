---
id: 001
title: Bronze AI Employee Foundation Spec
stage: spec
date: 2026-03-06
surface: agent
model: claude-sonnet-4-6
feature: 001-bronze-ai-employee
branch: 001-bronze-ai-employee
user: alihaidernoorani
command: /sp.specify
labels: ["spec","bronze","ai-employee","watcher","obsidian","hackathon"]
links:
  spec: specs/001-bronze-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-ai-employee/spec.md
  - specs/001-bronze-ai-employee/checklists/requirements.md
tests:
  - none
---

## Prompt

```text
Create a product specification for a Bronze Tier implementation of a Personal AI Employee for the "Personal AI Employee Hackathon".

The system should implement a minimal local-first AI employee architecture using Claude Code and an Obsidian vault.

Goal:
Create a foundation where incoming events are captured as markdown files, processed by Claude Code, and tracked through a task workflow.

Core Architecture:
Perception → Reasoning → Task Management

Perception Layer:
A Python watcher detects new events and creates markdown task files.

Reasoning Layer:
Claude Code reads tasks from the vault, analyzes them, and generates a plan.

Task Workflow:
Tasks move through a folder-based workflow inside the Obsidian vault.

Vault Folder Structure:
Inbox/
Needs_Action/
Plans/
Done/
Logs/

Core Files:
Dashboard.md – overview of current activity
Company_Handbook.md – rules for AI behavior

Functional Requirements:

1. Obsidian Vault
The system uses a local Obsidian vault as the main storage and interface.

2. File System Watcher
A Python watcher monitors a folder called /Inbox for new files.
When a new file appears, it creates a task file in /Needs_Action.

3. Claude Processing
Claude Code reads markdown files from /Needs_Action.
Claude analyzes the task and creates a Plan.md file inside /Plans.

4. Task Completion
After the task is processed, the task file is moved to /Done.

5. Dashboard Updates
Claude updates Dashboard.md with a summary of recent activity.

Example Workflow:
File added to Inbox → Watcher creates task file → Claude reads task → Claude creates plan → Task processed → Task moved to Done → Dashboard updated

Non Functional Requirements:
Local-first architecture, all data stored as markdown files, no external services required, clear folder-based workflow.

Deliverable:
A minimal working AI Employee foundation capable of detecting events, planning tasks, and tracking task completion.
```

## Response snapshot

Created branch `001-bronze-ai-employee`, scaffolded `specs/001-bronze-ai-employee/spec.md`
with 3 prioritised user stories (P1: event detection, P2: Claude task analysis + plan
creation, P3: completion tracking + dashboard update), 13 functional requirements,
5 key entities, 6 measurable success criteria, and an assumptions section. Quality
checklist created and all items pass. No NEEDS CLARIFICATION markers — spec is ready
for `/sp.plan`.

## Outcome

- ✅ Impact: Bronze tier fully specified; clear acceptance criteria and success metrics defined for all three user stories.
- 🧪 Tests: N/A — specification document, no executable tests.
- 📁 Files: specs/001-bronze-ai-employee/spec.md, specs/001-bronze-ai-employee/checklists/requirements.md
- 🔁 Next prompts: /sp.plan to generate implementation architecture; /sp.clarify if any requirements need elaboration.
- 🧠 Reflection: All requirements were unambiguous from the user input. Idempotency (FR-004), DRY_RUN default (FR-012), and WSL2 polling assumption are the three constraints most likely to cause confusion during planning.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): quality checklist — all items PASS
- Prompt variant (if applicable): initial spec from structured user description
- Next experiment: validate spec accuracy against /sp.plan output
