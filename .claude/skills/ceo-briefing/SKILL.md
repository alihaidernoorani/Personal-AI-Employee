---
name: ceo-briefing
description: |
  Generates a weekly CEO Briefing from Business_Goals.md, Bank_Transactions.md,
  Done/ folder, Needs_Action/ stalled tasks, and Logs/ social media entries.
  Writes the briefing to AI_Employee_Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md.
  Contains 7 required sections: Executive Summary, Revenue Summary, Completed This Week,
  Bottlenecks, Cost Optimisation Suggestions, Upcoming Deadlines, Social Media Summary.
  Use this skill on Sunday evenings or on-demand for business review.
---

# CEO Briefing

Generate a comprehensive weekly CEO briefing from vault data.

---

## Step 1 — Determine the Briefing Date

Use today's date (UTC) to compute:
- `week_ending`: today's date in YYYY-MM-DD format
- `briefing_filename`: `AI_Employee_Vault/Briefings/<week_ending>_Monday_Briefing.md`

Create the `Briefings/` directory if it does not exist.

---

## Step 2 — Check for Cloud-Prepared Briefing Data (Platinum)

Before reading individual vault files, check for a cloud-prepared data file:

1. List all files matching `AI_Employee_Vault/Updates/BRIEFING_DATA_*.md`
2. Sort by date suffix (newest first)
3. If a file exists **dated within the last 7 days**:
   - Read it and extract the following fields:
     - `cloud_agent_uptime_pct` — percentage uptime from heartbeat gap analysis
     - `signal_summary` — list of signals grouped by type and severity
     - `social_post_count` — platform breakdown of social posts
     - `vault_health_status` — overall vault health
   - Use these as supplemental data in Step 5 (see **Cloud Agent Uptime** section below)
4. If **no file found within 7 days**: set `cloud_data_available = false`; the briefing will note "Cloud agent data unavailable"

---

## Step 3 — Read Input Sources

Read the following files in order:

1. **`AI_Employee_Vault/Business_Goals.md`** — extract:
   - Revenue targets (weekly, MTD, monthly)
   - KPIs
   - Subscription audit rules
   - Upcoming deadlines

2. **Odoo invoices via MCP** — call the `list_invoices` tool (odoo-mcp) with:
   - `date_from`: 7 days ago (YYYY-MM-DD)
   - `date_to`: today (YYYY-MM-DD)
   - `state`: `"posted"` (confirmed invoices only)

   From the result, sum `amount` values for:
   - **Weekly Revenue**: all returned invoices
   - **MTD Revenue**: re-call `list_invoices` with `date_from` = first day of current month

   If the odoo-mcp tool returns an error or is unavailable, fall back to
   **`AI_Employee_Vault/Bank_Transactions.md`** and note "Odoo unavailable — using bank log".

3. **`AI_Employee_Vault/Bank_Transactions.md`** — extract (fallback or supplement):
   - All transaction rows not already captured by Odoo
   - Identify recurring subscriptions (negative amounts with subscription category)

4. **`AI_Employee_Vault/Done/`** — list all files modified in the last 7 days:
   - Read each file's frontmatter for type and description
   - Build a summary list of completed tasks

4. **`AI_Employee_Vault/Needs_Action/`** — identify stalled tasks:
   - List all files that are older than 24 hours (based on file mtime)
   - Exclude ERROR_*.md files (they are handled separately)

5. **`AI_Employee_Vault/Logs/`** — read today's and recent log files:
   - Find entries where `action_type` is `linkedin_post`, `social_post`, or `social_summary`
   - Group by platform and count posts; extract engagement data if available

---

## Step 4 — Calculate Revenue Metrics

Primary source is **Odoo** (via `list_invoices` MCP calls from Step 2).
Fallback to `Bank_Transactions.md` if Odoo is unavailable.

- **Weekly Revenue**: Sum of `amount` from posted Odoo invoices in last 7 days
- **MTD Revenue**: Sum of `amount` from posted Odoo invoices since first of current month
- **Weekly Target**: Read from `Business_Goals.md`
- **MTD Target**: Read from `Business_Goals.md`

If no invoices found for the period, write "No invoices recorded in Odoo" in the table.

---

## Step 5 — Identify Cost Optimisation Issues

Apply the subscription audit rules from `Business_Goals.md`:
- For each subscription transaction in `Bank_Transactions.md`, check:
  - Is this flagged in Business_Goals.md as "under review" or "FLAGGED"?
  - Does the cost exceed the threshold defined in the audit rules?
- List any subscriptions that match the flag criteria

If none, write: "No subscription issues identified this week."

---

## Step 6 — Write the Briefing File

Write `AI_Employee_Vault/Briefings/<week_ending>_Monday_Briefing.md` with the following structure:

```markdown
---
type: ceo_briefing
generated_at: <ISO timestamp>
week_ending: <YYYY-MM-DD>
---

# CEO Briefing — Week Ending <week_ending>

*Generated: <generated_at>*

---

## Executive Summary

<2-3 sentence overview: weekly performance vs targets, key wins, notable issues>

---

## Revenue Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Weekly Revenue | <weekly_target> | <weekly_actual> | 🟢/🟡/🔴 |
| MTD Revenue | <mtd_target> | <mtd_actual> | 🟢/🟡/🔴 |

Status legend: 🟢 On/Above Target | 🟡 Within 20% | 🔴 >20% Below Target

---

## Completed This Week

<bullet list of tasks completed in Done/ in the last 7 days>
<If none: "No tasks completed this week.">

---

## Bottlenecks

<bullet list of tasks in Needs_Action/ older than 24 hours with their age>
<If none: "No bottlenecks identified.">

---

## Cost Optimisation Suggestions

<bullet list of flagged subscriptions or spending issues>
<If none: "No issues identified.">

---

## Upcoming Deadlines

<bullet list of deadlines extracted from Business_Goals.md>
<If none: "No upcoming deadlines.">

---

## Social Media Summary

| Platform | Posts This Week | Engagement |
|----------|----------------|------------|
| LinkedIn | <count> | <likes/shares or "N/A"> |
| Facebook | <count> | <count or "N/A"> |
| Instagram | <count> | <count or "N/A"> |
| Twitter/X | <count> | <count or "N/A"> |

<If no posts: "No social media posts this week." in the table notes>

---

## Cloud Agent Uptime

<If cloud_data_available = true:>

| Metric | Value |
|--------|-------|
| Uptime | <cloud_agent_uptime_pct>% |
| Vault Sync Health | <vault_health_status> |
| Signals This Week | <count by severity> |

<signal_summary — bullet list grouped by signal_type>

<If cloud_data_available = false:>

Cloud agent data unavailable. No BRIEFING_DATA_*.md file found within the last 7 days.
Check that the cloud agent is running and vault sync is operational.
```

**Colour coding for Revenue Status:**
- 🟢 = actual >= target
- 🟡 = actual >= 80% of target
- 🔴 = actual < 80% of target

---

## Step 7 — Log the Briefing Generation

Append a NDJSON entry to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "ceo_briefing",
  "actor": "claude_code",
  "target": "Briefings/<filename>",
  "parameters": {"week_ending": "<YYYY-MM-DD>"},
  "approval_status": "auto",
  "approved_by": "system",
  "result": "success"
}
```

---

## Completion Signal

After writing the briefing file and log entry, output:

```
CEO Briefing written: Briefings/<filename>
<promise>TASK_COMPLETE</promise>
```
