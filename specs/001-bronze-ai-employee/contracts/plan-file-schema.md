# Contract: Plan File Schema

**Version**: 1.0 | **Date**: 2026-03-06

A Plan File is created by Claude for each processed task. It describes what should
happen next and is the HITL gate for any sensitive action.

---

## Filename Pattern

```
Plans/PLAN_<YYYYMMDDTHHMMSSz>_<source-task-stem>.md
```

---

## Frontmatter Contract

```yaml
---
type: plan                    # REQUIRED — always "plan"
source_task: <filename>       # REQUIRED — the task .md file this plan was created for
created_at: <ISO 8601Z>       # REQUIRED — UTC creation timestamp
requires_approval: false      # REQUIRED — true if any action has an APPROVE checkbox
status: draft                 # REQUIRED — one of: draft | approved | rejected | executed
---
```

---

## Body Contract

```markdown
## Summary
<1-3 sentences: what the task is and what the plan does>

## Analysis
<Claude's interpretation: task type, key data extracted, relevant handbook rules applied>

## Actions
- [ ] <safe action — Claude executes this directly, no human needed>
- [ ] APPROVE: <sensitive action — BLOCKED until human checks this checkbox>

## Notes
<optional: follow-up reminders, due dates, flags>
```

---

## HITL Gate Rule

If ANY action line contains `APPROVE:`, the plan frontmatter MUST set
`requires_approval: true` and the skill MUST NOT execute that action until
the checkbox is checked by a human.

Plans with `requires_approval: false` are executed fully by the skill
on the same run they are created.
