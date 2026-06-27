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

## Step 2 — Read Input Sources

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

## Step 3 — Calculate Revenue Metrics

Primary source is **Odoo** (via `list_invoices` MCP calls from Step 2).
Fallback to `Bank_Transactions.md` if Odoo is unavailable.

- **Weekly Revenue**: Sum of `amount` from posted Odoo invoices in last 7 days
- **MTD Revenue**: Sum of `amount` from posted Odoo invoices since first of current month
- **Weekly Target**: Read from `Business_Goals.md`
- **MTD Target**: Read from `Business_Goals.md`

If no invoices found for the period, write "No invoices recorded in Odoo" in the table.

---

## Step 4 — Identify Cost Optimisation Issues

Apply the subscription audit rules from `Business_Goals.md`:
- For each subscription transaction in `Bank_Transactions.md`, check:
  - Is this flagged in Business_Goals.md as "under review" or "FLAGGED"?
  - Does the cost exceed the threshold defined in the audit rules?
- List any subscriptions that match the flag criteria

If none, write: "No subscription issues identified this week."

---

## Step 5 — Write the Briefing File

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
```

**Colour coding for Revenue Status:**
- 🟢 = actual >= target
- 🟡 = actual >= 80% of target
- 🔴 = actual < 80% of target

---

## Step 6 — Log the Briefing Generation

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
