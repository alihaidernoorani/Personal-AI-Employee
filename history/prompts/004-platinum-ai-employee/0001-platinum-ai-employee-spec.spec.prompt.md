---
id: "0001"
title: Platinum AI Employee Spec
stage: spec
date: 2026-06-27
surface: agent
model: claude-sonnet-4-6
feature: 004-platinum-ai-employee
branch: 004-platinum-ai-employee
user: Ali Haider Noorani
command: /sp.specify
labels: ["platinum","spec","cloud-local-split","vault-sync","multi-agent","constitution"]
links:
  spec: specs/004-platinum-ai-employee/spec.md
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - specs/004-platinum-ai-employee/spec.md
  - specs/004-platinum-ai-employee/checklists/requirements.md
  - history/prompts/004-platinum-ai-employee/0001-platinum-ai-employee-spec.spec.prompt.md
tests:
  - "null"
---

## Prompt

Generate a complete technical specification for a Platinum Tier Personal AI Employee.

Include:
- Functional requirements
- Non-functional requirements
- System architecture
- Folder structure
- Claude Skills
- MCP servers
- Watchers
- Vault design
- Security model
- Approval workflow
- Cloud/Local responsibilities
- Deployment architecture
- Testing strategy

The specification should be implementation-ready.

## Response snapshot

Generated a complete Platinum Tier specification at `specs/004-platinum-ai-employee/spec.md`. The spec:

- Defines the Cloud/Local agent split with explicit responsibility boundaries (FR-001–FR-020)
- Specifies bidirectional vault sync with 60-second SLA, conflict resolution rules, and audit trail (FR-021–FR-030)
- Defines multi-agent task coordination via claim-by-move across `In_Progress/cloud/` and `In_Progress/local/` (FR-031–FR-035)
- Specifies the `constitution-check` skill for 15-principle compliance verification (FR-036–FR-040)
- Covers cloud VM deployment automation with provisioning script and smoke test (FR-041–FR-047)
- Adds 5 new vault folders: `Updates/`, `Signals/`, `In_Progress/cloud/`, `In_Progress/local/`, `Sync/`
- Introduces 4 new Platinum skills: `cloud-triage`, `vault-health`, `constitution-check`, `cloud-briefing-prep`
- Defines a testing strategy with 9 test categories (FR-059–FR-067)
- Covers 7 user stories (P1–P3) spanning 24/7 triage, multi-agent coordination, vault sync, security boundary, social drafting, compliance, and provisioning
- Defines 12 success criteria (SC-001–SC-012)
- All 15 constitution principles explicitly addressed; no NEEDS CLARIFICATION markers

## Outcome

- ✅ Impact: Complete implementation-ready spec for Platinum Tier; establishes the 24/7 cloud/local architecture on top of Gold Tier
- 🧪 Tests: Testing strategy defined in FR-059–FR-067; no code tests run at spec stage
- 📁 Files: specs/004-platinum-ai-employee/spec.md, checklists/requirements.md
- 🔁 Next prompts: /sp.plan to generate the implementation plan; /sp.adr for cloud/local split boundary decision
- 🧠 Reflection: Spec builds on Gold spec patterns for consistency; security boundary (NFR-014) and single-writer rule (FR-004) are the most critical constraints to verify during planning

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): checklist validation PASS (15/15 items)
- Prompt variant (if applicable): "null"
- Next experiment: /sp.plan 004-platinum-ai-employee
