---
id: "003"
title: gold-tier-tasks-generation
stage: tasks
date: 2026-03-22
surface: agent
model: claude-sonnet-4-6
feature: 003-gold-ai-employee
branch: 003-gold-ai-employee
user: DELL
command: /sp.tasks
labels: ["tasks","gold-tier","credential-checkpoints","dry-run","orchestrator","mcp","odoo","social","briefing","ralph-wiggum"]
links:
  spec: specs/003-gold-ai-employee/spec.md
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - specs/003-gold-ai-employee/tasks.md
tests:
  - T005 Claude Code read/write vault test
  - T012 Finance watcher dry-run with mock CSV
  - T017 Orchestrator dry-run vault health check
  - T027 Email MCP queue round-trip test
  - T034 Odoo MCP dry-run invoice creation
  - T041 CEO Briefing mock data generation
  - T059 Ralph loop multi-step completion test
  - T065 Audit log entry verification
  - T072 Simulated failure + recovery test
  - T076 Full end-to-end DRY_RUN=true validation
---

## Prompt

You are a senior technical project manager using SpecKitPlus.

Convert the PLAN into a clear, executable Tasks.md for a Gold Tier AI Employee system.

## Core Requirements
- Include credential checkpoints (pause for user input)
- Include testing for every phase
- Include DRY_RUN before real execution
- Do NOT proceed if tests fail

---

## Task Format (MANDATORY)
Each task must include:
- Name
- Description
- Inputs / Outputs
- Dependencies
- Done Criteria
- Test Step
- Dry Run (if applicable)

---

## PHASES

### Phase 1: Setup
- Environment (Python, Node)
- Obsidian vault
- Claude Code

✅ Test: Claude can read/write files

---

### 🔐 Checkpoint 1: Base Credentials
Pause for `.env` setup:
(Gmail, WhatsApp session path, Odoo placeholder, social placeholders)

---

### Phase 2: Watchers
- Gmail
- WhatsApp (single session, no multiple browsers)
- File system
- Finance

🧪 Test: Events → files in `/Needs_Action`
🧯 Dry Run: Use mock data

---

### 🔐 Checkpoint 2: Gmail Credentials
Require OAuth setup + test Gmail watcher

---

### Phase 3: Orchestrator
- Folder monitoring
- Claude trigger
- File state transitions
- Approval handling

🧪 Test: File → Plan → Approval flow
🧯 Dry Run: No real actions

---

### Phase 4: MCP Servers
- Email, Browser, Social, Odoo

🧯 Dry Run: Log actions only
🧪 Test: Each MCP independently

---

### 🔐 Checkpoint 3: External APIs
Collect & verify:
Email, Social, Browser configs

---

### Phase 5: Agent Skills
- Plan generation
- Execution
- Approval
- Logging

🧪 Test: Valid Plan.md + execution flow

---

### Phase 6: Odoo Integration
- Setup Odoo
- JSON-RPC MCP
- Invoice + transactions

---

### 🔐 Checkpoint 4: Odoo Credentials
Require: URL, DB, user, key

🧪 Test: Create invoice (DRY_RUN first)

---

### Phase 7: Social Automation
- Post generation
- Approval-based posting
- Summaries

🧯 Dry Run: No real posting
🧪 Test: Content + flow

---

### Phase 8: CEO Briefing
- Analyze goals + accounting
- Generate weekly report

🧪 Test: Use mock data

---

### Phase 9: Ralph Loop
- Stop hook
- Iteration until `/Done`

🧪 Test: Multi-step task completion

---

### Phase 10: Logging & Security
- JSON logs
- Permission rules
- .env usage

🧪 Test: Logs generated correctly

---

### Phase 11: Error Handling
- Retry system
- Graceful fallback
- Watchdog

🧪 Test: Simulate failures

---

## ✅ Final Validation
- End-to-end flow: Message → Plan → Approval → Action → Done
- Full system with DRY_RUN=true
- Limited real execution test

---

## Output
Generate a clean, phase-wise Tasks.md with strict execution order.

## Response snapshot

Generated `specs/003-gold-ai-employee/tasks.md` containing 76 tasks (T001–T076) organized across 11 phases, 4 credential checkpoints, and a Final Validation section.

**Structure:**
- Phase 1 (T001–T005): Environment setup verification — Python 3.13+, Node.js v24+, Obsidian vault, `.env`, Claude read/write test
- Checkpoint 1 (T006): Base .env credentials pause (Gmail, WhatsApp, Odoo placeholders, social placeholders)
- Phase 2 (T007–T012): Watcher verification [VERIFY] + Finance Watcher build [BUILD] with mock CSV dry-run
- Checkpoint 2 (T013): Gmail OAuth setup + watcher live test
- Phase 3 (T014–T017): Orchestrator watchdog + cron scheduler + vault health check dry-run
- Phase 4 (T018–T034): Email MCP queue extensions [BUILD] + Social MCP server [BUILD] + Odoo MCP server [BUILD]
- Checkpoint 3 (T028): Social API token verification
- Checkpoint 4 (T042): Odoo credentials + connectivity check
- Phase 5 (T035–T041): Skill verification [VERIFY] + CEO Briefing skill [BUILD]
- Phase 6 (T043–T046): Odoo live invoice + transaction integration tests
- Phase 7 (T047–T053): Social automation + approval gate + engagement summary
- Phase 8 (T054–T056): CEO Briefing full data test + Sunday 23:00 cron
- Phase 9 (T057–T059): Ralph loop stop hook verification [VERIFY] + multi-step task test
- Phase 10 (T060–T065): Audit logging + permission rules + .env security check
- Phase 11 (T066–T072): Retry/backoff + graceful degradation + watchdog simulation
- Final Validation (T073–T076): End-to-end DRY_RUN + limited live run + architecture docs

Each task includes: checklist line with [P]/[US#] markers, Inputs/Outputs, Dependencies, Done Criteria, Test Step, and Dry Run section where applicable. Build-vs-verify distinction clearly marked throughout.

## Outcome

- ✅ Impact: 76 immediately-executable tasks covering the full Gold tier implementation with clear build-vs-verify distinction for Silver carryover components
- 🧪 Tests: Every phase has at least one test step; DRY_RUN mode tested before any live execution; 4 credential checkpoints block autonomous progress at human-required setup steps
- 📁 Files: specs/003-gold-ai-employee/tasks.md (created)
- 🔁 Next prompts: `/sp.implement` to begin task execution; `/sp.adr stdio-vs-http-mcp-transport` to document transport decision; `git commit` to save all Gold tier spec artifacts
- 🧠 Reflection: The build-vs-verify pattern ([BUILD] vs [VERIFY] markers) is critical here — the Silver tier already has 6 skills, 5 watchers, Ralph Wiggum loop, and Email MCP. Without this distinction, tasks would redundantly rebuild existing components. The credential checkpoints prevent the common failure mode where automation runs ahead of available secrets.

## Evaluation notes (flywheel)

- Failure modes observed: Tasks without explicit file paths are too vague for LLM execution; checkpoint tasks must be unmistakably blocking (not skippable); DRY_RUN tasks must come before any live equivalents
- Graders run and results (PASS/FAIL): Manual review — all 76 tasks have file paths, done criteria, and test steps (PASS); all 4 checkpoints are non-parallelizable blocking steps (PASS)
- Prompt variant (if applicable): sp.tasks v1.0 with SpecKitPlus checklist format
- Next experiment: Add explicit rollback steps to each phase so failed phases can be cleanly reset without orphaned vault files
