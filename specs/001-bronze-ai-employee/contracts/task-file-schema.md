# Contract: Task File Schema

**Version**: 1.0 | **Date**: 2026-03-06

A Task File is the unit of work that flows through the vault's state machine.
The `FilesystemWatcher` creates it; the `process-needs-action` skill consumes it.

---

## Filename Pattern

```
FILE_<YYYYMMDDTHHMMSSz>_<sanitised-stem><original-ext>.md
```

Examples:
- `FILE_20260306T120000Z_invoice.txt.md`
- `FILE_20260306T120500Z_contract_v2.pdf.md`

Rules:
- Spaces in original filename replaced with `_`
- Timestamp is UTC in compact ISO 8601 format
- The companion copy (actual file) uses the same stem without `.md`

---

## Frontmatter Contract

```yaml
---
type: file_drop          # REQUIRED — one of: file_drop | email | error | unknown
original_name: <str>     # REQUIRED — original filename as dropped in Inbox
copied_to: <str>         # REQUIRED — name of copied file in Needs_Action/
size_bytes: <int>        # REQUIRED — file size ≥ 0
received: <ISO 8601Z>    # REQUIRED — UTC detection timestamp
priority: normal         # REQUIRED — one of: urgent | high | normal | low
status: pending          # REQUIRED — one of: pending | in_progress | done | error
---
```

All fields are required. The skill MUST reject (flag for human review) any task
file missing a required field rather than silently assuming defaults.

---

## Body Contract

```markdown
## File Dropped for Processing

| Field         | Value           |
|---------------|-----------------|
| Original name | `<filename>`    |
| File size     | <N> bytes       |
| Received      | <YYYY-MM-DD HH:MM UTC> |
| Copied to     | `<dest_filename>` |

## Suggested Actions

- [ ] Review file contents
- [ ] Determine if action is required
- [ ] Move this file to `/Done/` when complete, or `/Rejected/` to discard
```

---

## Done State

When processing completes, the task file is moved to `Done/` with a `DONE_` prefix:

```
Done/DONE_FILE_20260306T120000Z_invoice.txt.md
```

The file's content is updated with a `## Summary` section added by the skill
describing what was done and any follow-up reminders.
