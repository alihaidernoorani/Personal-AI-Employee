---
name: log-cleanup
description: |
  Enforces the 90-day audit log retention policy (FR-033). Scans
  AI_Employee_Vault/Logs/ for NDJSON log files older than 90 days and
  deletes them. Logs the cleanup action itself before deleting anything.
  Safe: never deletes files less than 90 days old; never deletes non-.json files.
  Use this skill on a scheduled basis (every 90 days) or on-demand to reclaim
  disk space and maintain compliance with the audit retention policy.
  Triggered by: "run log-cleanup skill", "clean up logs", "enforce log retention".
---

# Log Cleanup

Enforce the 90-day audit log retention policy by deleting old log files.

---

## Step 1 — Inventory Log Files

List all files in `AI_Employee_Vault/Logs/` matching the pattern `YYYY-MM-DD.json`.

For each file:
- Parse the date from the filename (format: `YYYY-MM-DD`)
- Calculate age in days: today's date minus file date
- Classify as:
  - `retain` — age < 90 days
  - `eligible` — age ≥ 90 days

**Safety rule:** If the date cannot be parsed from a filename, classify as `retain`
(never delete files with unexpected names).

---

## Step 2 — Preview Deletion List

Before deleting anything, compile the deletion list:

```
Files to delete (age ≥ 90 days):
  - Logs/2025-09-01.json (N days old)
  - Logs/2025-08-15.json (N days old)
  ...

Files to retain (age < 90 days):
  - Logs/2026-05-01.json (N days old)
  ...

Total: X files to delete, Y files to retain
```

If no files are eligible for deletion, output:
```
No log files older than 90 days found. Retention policy satisfied.
<promise>TASK_COMPLETE</promise>
```

---

## Step 3 — Log the Cleanup Action (before deleting)

Before deleting any files, append one NDJSON entry to today's log file
`AI_Employee_Vault/Logs/<today>.json` to create an audit trail of the cleanup:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "log_cleanup",
  "actor": "claude_code",
  "target": "AI_Employee_Vault/Logs/",
  "parameters": {
    "retention_days": 90,
    "files_to_delete": ["<filename1>", "<filename2>"],
    "total_files_deleted": 0,
    "oldest_retained": "<oldest retained filename>"
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "in_progress"
}
```

---

## Step 4 — Delete Eligible Files

For each file in the `eligible` list:
1. Confirm file is in `AI_Employee_Vault/Logs/` (never delete files outside this folder)
2. Confirm filename matches `YYYY-MM-DD.json` pattern
3. Confirm age ≥ 90 days (re-check before each delete)
4. Delete the file

If any deletion fails (permission error, file locked):
- Log the failure
- Continue to next file — do not stop the entire cleanup

---

## Step 5 — Update the Audit Log Entry

After all deletions, update the `result` field of the log entry written in Step 3.
Append a second entry (or note in Dashboard) with final counts:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "log_cleanup_complete",
  "actor": "claude_code",
  "target": "AI_Employee_Vault/Logs/",
  "parameters": {
    "retention_days": 90,
    "files_deleted": <actual count>,
    "files_failed": <failure count>,
    "oldest_retained": "<oldest retained filename>",
    "space_freed_approx": "<estimate if available>"
  },
  "approval_status": "auto",
  "approved_by": "system",
  "result": "success"
}
```

---

## Step 6 — Report

Output a human-readable summary:

```
Log Cleanup Complete
-------------------
Files deleted:  X (oldest: YYYY-MM-DD.json)
Files retained: Y (oldest retained: YYYY-MM-DD.json)
Failures:       Z (see ERROR entries above if any)
Retention policy: 90 days — next cleanup due: <today + 90 days>
```

---

## Completion Signal

```
<promise>TASK_COMPLETE</promise>
```
