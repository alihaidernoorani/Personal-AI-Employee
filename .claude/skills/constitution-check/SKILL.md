---
name: constitution-check
description: |
  Verifies compliance with all 15 constitution principles defined in
  .specify/memory/constitution.md. Runs 15 checks per the Automation Matrix
  in specs/004-platinum-ai-employee/research.md (7 automated YES, 7 PARTIAL,
  1 NEEDS_MANUAL_REVIEW). For each FAIL, writes finding + remediation.
  Writes Briefings/COMPLIANCE_REPORT_<date>.md per the Compliance Report Schema.
  On any FAIL, creates Needs_Action/COMPLIANCE_FAIL_<date>.md.
  Updates Dashboard.md compliance section with overall status, check date, report link.
  Triggered by: "run constitution-check skill", "check compliance", "run compliance check",
  final Platinum sign-off gate (T047).
---

# Constitution Check

Verify all 15 principles. Produce a compliance report. Gate Platinum sign-off.

---

## Step 1 — Load Constitution

Read `.specify/memory/constitution.md` to confirm the 15 principles are present.
If missing: FAIL all checks with note "Constitution file not found".

---

## Step 2 — Run 15 Principle Checks

Run each check in order. Record status as `PASS`, `FAIL`, or `NEEDS_MANUAL_REVIEW`.

### Principle I — Production First (NEEDS_MANUAL_REVIEW)

**Human checklist** (cannot be automated):
- [ ] No placeholder `TODO`, `FIXME`, `pass`, or `raise NotImplementedError` stubs in any watcher or MCP server
- [ ] All skill SKILL.md files describe real, executable workflows (not "TBD")
- [ ] `DRY_RUN` is configurable and documented in `.env.example`

Mark as `NEEDS_MANUAL_REVIEW` with the checklist above for human sign-off.

### Principle II — Local First (YES — automated)

Run `scripts/sync/security-boundary-test.sh` via subprocess.
- **PASS**: All checks return PASS (zero FAIL lines in output)
- **FAIL**: Any FAIL line found — include the specific check that failed

If script not executable or SSH unavailable: perform inline checks:
- Verify `.env` is not tracked by git: `git check-ignore .env` returns `.env`
- Verify `.env` is in `.gitignore`
- Report "PARTIAL — SSH check skipped" with manual verification checklist

### Principle III — Cloud Worker (PARTIAL)

Automated checks:
1. Verify no `.mcp.json` at project root with email/social tools registered
2. Grep all files in `.claude/skills/cloud-triage/`, `watchers/heartbeat_writer.py`, `watchers/signals_watcher.py`, `watchers/stale_task_monitor.py` for calls to `send_email`, `post_twitter`, `post_linkedin`, `post_facebook`, `post_instagram`, `post_invoice`
3. Verify cloud skills import `safe_vault_write` (grep for the import)

Manual check:
- [ ] Confirm cloud VM has no `.mcp.json` with execution tools (requires SSH)

Report: PASS if no violations found; PARTIAL if manual SSH check pending.

### Principle IV — Human In The Loop (YES — automated)

1. Read `execute-plan` skill SKILL.md — verify it reads from `Approved/` only
2. Grep all skill files for patterns that auto-move files from `Pending_Approval/` to `Approved/`
3. Verify `process-needs-action` writes APPROVAL_*.md before any MCP call
4. Check that `APPROVAL_REQUIRED` error is returned when `approval_id` missing in social-mcp and odoo-mcp

**FAIL**: If any skill bypasses the APPROVAL_*.md gate for sensitive actions.

### Principle V — Vault Driven Architecture (PARTIAL)

Automated:
1. Grep all Python files for `http.client`, `socket.connect`, `requests.get/post` used for inter-agent communication (allow HTTP calls to external APIs — flag only agent-to-agent HTTP)
2. Verify no shared-memory patterns (`multiprocessing.shared_memory`, `mmap`)

Manual check:
- [ ] Confirm agents communicate only via vault filesystem, not network sockets

### Principle VI — Claim-by-Move (YES — automated)

1. Verify directories exist: `AI_Employee_Vault/In_Progress/cloud/`, `AI_Employee_Vault/In_Progress/local/`
2. Grep `process-needs-action` and `cloud-triage` skills for `os.rename()` or `Path.rename()` before task processing
3. Verify stale-task monitor moves files BACK to `Needs_Action/`

**FAIL**: Missing `In_Progress/` subdirectory or missing rename-before-process in skill code.

### Principle VII — Single Writer Rule (YES — automated)

Grep all cloud-side files (`cloud_orchestrator.py`, `watchers/heartbeat_writer.py`, `watchers/stale_task_monitor.py`, `watchers/signals_watcher.py`, `.claude/skills/cloud-triage/SKILL.md`, `.claude/skills/cloud-briefing-prep/SKILL.md`) for:
- Direct writes to `Dashboard.md`
- Direct writes to `Done/`
- Direct writes to `Approved/`
- Direct writes to `Rejected/`

**FAIL**: Any direct write to prohibited paths found (bypassing `safe_vault_write` check).

Also verify `safe_vault_write()` is imported and used in all cloud-side vault writes.

### Principle VIII — Event Driven (PARTIAL)

Automated:
1. Grep `watchers/` for `InotifyObserver` — flag if found without NTFS-path check
2. Verify watchers use `PollingObserver` or `time.sleep()` polling (not busy-wait `while True: pass`)
3. Check `orchestrator.py` uses polling interval ≥ 30s

Manual:
- [ ] Confirm no busy-wait loops introduced in new watchers

### Principle IX — Modular Design (PARTIAL)

Automated:
1. Count lines in every `.py` file under `watchers/`, `mcp-servers/`, `scripts/`
2. **FAIL** if any file exceeds 300 lines
3. List all oversized files with line counts

Manual:
- [ ] Review that each module has a single clear responsibility (cannot be automated)

### Principle X — Agent Skills (YES — automated)

Grep `watchers/*.py` for:
- Decision-making patterns: `if "urgent" in`, `Company_Handbook`, `Business_Goals`, `draft`, `classify`
- Reasoning keywords that belong in skills

**FAIL**: Decision logic found in watcher code (watchers should only detect and create task files).

### Principle XI — Observability (YES — automated)

1. Grep all MCP server `call_tool` functions for `_log_action` or `log_action` call after each tool dispatch
2. Verify `AI_Employee_Vault/Logs/` exists and has at least one `.json` file
3. Verify at least one log entry has all required fields: `timestamp`, `action_type`, `actor`, `target`, `parameters`, `approval_status`, `result`

**FAIL**: Any MCP tool dispatch without audit log entry; missing required field.

### Principle XII — Reliability (PARTIAL)

Automated:
1. Grep `mcp-servers/` for retry patterns (`time.sleep`, `backoff`, `retryable`)
2. Verify `orchestrator.py` has watchdog loop (grep for `thread.is_alive()` or `watchdog`)
3. Verify `cloud_orchestrator.py` has watchdog loop

Manual:
- [ ] Confirm exponential backoff parameters are appropriate (base 1s, max 60s, 3 attempts)

### Principle XIII — Security (YES — automated)

1. Verify `.env` is in `.gitignore`: `git check-ignore .env`
2. Grep all `AI_Employee_Vault/**/*.md` files for patterns: `sk-`, `Bearer `, `password=`, `token=`, `api_key=`
3. Verify `DRY_RUN=true` is the default in `.env.example`
4. Verify no hardcoded tokens in any `.py` file (grep for quoted strings matching `[A-Za-z0-9]{32,}` that look like API keys)

**FAIL**: Any secret pattern found in vault .md files; DRY_RUN defaulting to false.

### Principle XIV — Documentation (PARTIAL)

Automated:
1. Verify every file in `.claude/skills/` has a `SKILL.md` with valid YAML frontmatter (name, description fields present)
2. Verify every file in `watchers/` has a module docstring (first non-blank line after `"""`)
3. Verify `specs/004-platinum-ai-employee/contracts/` folder exists and has at least 1 file

Manual:
- [ ] Verify README.md has Platinum Architecture section (T046)
- [ ] Verify quickstart.md has Troubleshooting section (T040)

### Principle XV — Code Quality (PARTIAL)

Automated (same as Principle IX file-size check — deduplicate results):
1. List all files > 300 lines — report each as FAIL
2. After T031/T032/T033 splits: all odoo-mcp, social-mcp, gmail_api_watcher files should be ≤ 300 lines

Manual:
- [ ] Review for God Object patterns, tight coupling, missing dependency injection

---

## Step 3 — Write Compliance Report

Write `AI_Employee_Vault/Briefings/COMPLIANCE_REPORT_<YYYY-MM-DD>.md`:

```markdown
---
type: compliance_report
generated_at: <ISO-8601Z>
date: <YYYY-MM-DD>
overall_status: <PASS|FAIL|PARTIAL>
principles_pass: <count>
principles_fail: <count>
principles_manual: <count>
---

# Compliance Report — <YYYY-MM-DD>

*Generated by constitution-check skill. All 15 principles checked.*

## Summary

| Result | Count |
|--------|-------|
| PASS | <n> |
| FAIL | <n> |
| NEEDS_MANUAL_REVIEW | <n> |

**Overall**: <PASS if 0 FAIL / PARTIAL if any NEEDS_MANUAL_REVIEW / FAIL if any FAIL>

---

## Principle-by-Principle Results

| # | Principle | Status | Finding |
|---|-----------|--------|---------|
| I | Production First | NEEDS_MANUAL_REVIEW | Human checklist required |
| II | Local First | PASS/FAIL | <specific finding> |
| III | Cloud Worker | PASS/PARTIAL | <finding> |
| ... | ... | ... | ... |

---

## FAIL Details

For each FAIL:

### Principle <N> — <Name>

**Violation**: <specific file path and line number>
**Remediation**: <exact steps to fix>

---

## Manual Review Checklist

Items requiring human verification:

- [ ] Principle I: Production First — complete the Production checklist above
- [ ] Principle III: Cloud VM has no .mcp.json with execution tools (SSH verification)
- [ ] Principle V: No agent-to-agent HTTP calls (architectural review)
- [ ] Principle VIII: No busy-wait loops in new watchers
- [ ] Principle IX: All modules have single responsibility
- [ ] Principle XII: Exponential backoff parameters correct
- [ ] Principle XIV: README and quickstart complete
- [ ] Principle XV: No God Object patterns

Sign-off: _____________________________ Date: ___________
```

---

## Step 4 — Write Error File on FAIL

If any principle has status FAIL:

Write `AI_Employee_Vault/Needs_Action/COMPLIANCE_FAIL_<YYYY-MM-DD>.md`:

```markdown
---
type: compliance_fail
priority: high
received: <ISO-8601Z>
status: pending
---

# Constitution Compliance FAIL — <YYYY-MM-DD>

One or more constitution principles failed automated checks.
See `Briefings/COMPLIANCE_REPORT_<YYYY-MM-DD>.md` for details.

## Failed Principles

<List of failed principles with remediation steps>

## Required Action

Fix violations and re-run `/constitution-check`.
```

---

## Step 5 — Update Dashboard.md

Update the Compliance Status section in `AI_Employee_Vault/Dashboard.md`:

```
<!-- AI_EMPLOYEE:COMPLIANCE_RESULT --><PASS|FAIL|PARTIAL><!-- /AI_EMPLOYEE:COMPLIANCE_RESULT -->
<!-- AI_EMPLOYEE:COMPLIANCE_DATE --><YYYY-MM-DD><!-- /AI_EMPLOYEE:COMPLIANCE_DATE -->
<!-- AI_EMPLOYEE:COMPLIANCE_REPORT -->Briefings/COMPLIANCE_REPORT_<date>.md<!-- /AI_EMPLOYEE:COMPLIANCE_REPORT -->
<!-- AI_EMPLOYEE:COMPLIANCE_COUNTS -->Pass: <n>, Fail: <n>, Manual: <n><!-- /AI_EMPLOYEE:COMPLIANCE_COUNTS -->
```

---

## Step 6 — Append Audit Log

Append to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "constitution_check",
  "actor": "claude_code",
  "target": "AI_Employee_Vault/",
  "parameters": {
    "principles_pass": <n>,
    "principles_fail": <n>,
    "principles_manual": <n>,
    "report_file": "Briefings/COMPLIANCE_REPORT_<date>.md"
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "<pass|fail|partial>"
}
```

---

## Completion Signal

```
<promise>TASK_COMPLETE</promise>
```
